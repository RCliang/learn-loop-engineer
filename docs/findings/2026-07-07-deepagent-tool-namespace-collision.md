# Deepagent 工具命名空间冲突 —— 为什么 `bash_exec` 一直"失败"

**日期：** 2026-07-07
**任务：** `task_01_simple_script`（创建 `sandbox/hello.py`，运行，验证输出 "hello world"）
**触发场景：** 第一次真实并行运行 `python -m cli run --agent both --task task_01_simple_script`

## TL;DR

`create_deep_agent` 在我们传入的 3 个工具之外，**强制注入了 9 个内置工具**，形成 **3 对命名冲突**（`write_file`/`file_write`、`read_file`/`file_read`、`execute`/`bash_exec`）。模型按字母序优先选了 `write_file`（内置），它用的是不同的 schema（`file_path` vs `path`）和不同的 CWD 约定，与我们沙箱化的 `bash_exec` 产生冲突。CWD 错位导致模型尝试 5 次 bash 才偶然找到正确的相对路径。handroll 路只暴露这 3 个共享工具，完全没有这个问题。

## 观察现象

运行 `python -m cli run --agent both --task task_01_simple_script`。两条路径都成功，但 RunLog 长相天差地别：

| agent     | success | turns | in_tokens | out_tokens | duration_s |
|-----------|---------|-------|-----------|------------|------------|
| handroll  | True    | 3     | 2413      | 282        | 9.48       |
| deepagent | True    | 21    | 47202     | 563        | 12.64      |

`loop_turns` 差了约 7 倍，`in_tokens` 差了约 20 倍。任务内容是"创建 hello.py 并运行"——根本不需要 21 轮。deepagent 的 `tool_calls` 轨迹讲清了故事：

```json
"tool_calls": [
  {"name": "write_file",  "input": {"file_path": "sandbox/hello.py", "content": "print('hello world')\n"}},
  {"name": "bash_exec",   "input": {"command": "cd /sandbox && python hello.py"}},
  {"name": "bash_exec",   "input": {"command": "python /sandbox/hello.py"}},
  {"name": "bash_exec",   "input": {"command": "pwd && ls"}},
  {"name": "bash_exec",   "input": {"command": "python /e/2026projects/loop-engineer/sandbox/hello.py"}},
  {"name": "bash_exec",   "input": {"command": "python hello.py"}}
]
```

一个一行的文件，5 次 `bash_exec` 尝试。handroll 轨迹干净利落——一次 `file_write`、一次 `bash_exec`、完成。

## 证据：模型实际看到什么

检查编译图的 ToolNode（`agent.get_graph().nodes["tools"]`），可以看到**总共 12 个工具**：9 个 deepagents 内置 + 3 个我们的。

### 完整工具清单

| # | 工具 | 来源 | 冲突情况 | 用途（描述首行） | 关键参数 |
|---|------|------|----------|------------------|----------|
| 1 | `write_todos` | deepagents | — | 管理当前会话的结构化任务列表 | `todos: array` |
| 2 | `ls` | deepagents | 与 `file_read` 软重叠 | 列出目录中的所有文件 | `path: string`（**绝对路径**） |
| 3 | `read_file` | deepagents | **命名冲突** 我们的 `file_read` | 读取文件系统中的文件（支持分页、多模态） | `file_path`、`offset`、`limit`（**绝对路径**） |
| 4 | `write_file` | deepagents | **命名冲突** 我们的 `file_write` | 写入新文件到文件系统 | `file_path`、`content`（**绝对路径**） |
| 5 | `edit_file` | deepagents | — | 在文件中执行精确字符串替换 | `file_path`、`old_string`、`new_string`、`replace_all` |
| 6 | `glob` | deepagents | — | 按 glob 模式查找文件 | `pattern`、`path` |
| 7 | `grep` | deepagents | — | 跨文件搜索文本（字面量，非正则） | `pattern`、`path`、`glob`、`output_mode` |
| 8 | `execute` | deepagents | **功能重叠** 我们的 `bash_exec` | 在隔离沙箱环境中执行 shell 命令 | `command`、`timeout` |
| 9 | `task` | deepagents | — | 启动临时 subagent 处理复杂多步任务 | `description`、`subagent_type` |
| 10 | `bash_exec` | **我们的** | — | 在沙箱 shell（限制在 sandbox/ 工作目录）中执行命令 | `command`、`timeout` |
| 11 | `file_read` | **我们的** | — | 读取 sandbox/ 工作目录下的文件内容 | `path`、`encoding`（**相对 sandbox**） |
| 12 | `file_write` | **我们的** | — | 将内容写入 sandbox/ 工作目录下的文件 | `path`、`content`、`encoding`（**相对 sandbox**） |

### 三对冲突

真正让模型困惑的碰撞：

| 内置（deepagents） | 我们的 | Schema 差异 | 行为差异 |
|--------------------|--------|-------------|----------|
| `write_file(file_path=...)` | `file_write(path=...)` | 参数名 `file_path` vs `path` | 内置用项目根的**绝对**路径；我们的用**相对 sandbox** 的路径 |
| `read_file(file_path=...)` | `file_read(path=...)` | 参数名 `file_path` vs `path` | 同上；内置还多了我们没实现的 `offset`/`limit` 分页 |
| `execute(command=...)` | `bash_exec(command=...)` | 参数名同为 `command` | 内置"在隔离沙箱环境运行"（deepagents 自管）；我们的显式设 `cwd=SANDBOX_DIR` |

### 内置工具描述（完整参考）

下列描述逐字摘自 deepagents ToolNode（通过 `agent.get_graph().nodes["tools"].data.tools_by_name[name].description` 抓取）。它们有助于理解模型在选择工具时实际看到的内容。

**`write_todos`** —— 任务清单管理器。当模型判断任务需要 3 步以上时触发，注入一个计划阶段（增加轮次/token 开销）。（对 `task_01_simple_script` 来说是纯负担。）

**`ls`** —— 目录列表。参数：`path`（**"必须是绝对路径，不接受相对路径"**）。deepagents 的文件系统以项目根为根，**不是**我们的 sandbox/。

**`read_file`** —— 文件读取，支持分页 + 多模态（图片/PDF）。参数：`file_path`（**"必须是绝对路径"**）、`offset`（0 起始行号）、`limit`。返回 `cat -n` 格式内容。

**`write_file`** —— 文件创建器。参数：`file_path`（**"必须是绝对路径"**）、`content`。文档明确说"优先用 edit_file 编辑已有文件，而不是新建"。

**`edit_file`** —— 字符串替换编辑器。要求先读过文件。参数：`file_path`、`old_string`、`new_string`、`replace_all`。

**`glob`** —— 模式匹配。参数：`pattern`（如 `**/*.py`）、`path`（起始目录）。

**`grep`** —— 字面量文本搜索（**非正则**）。参数：`pattern`、`path`、`glob`、`output_mode`（`files_with_matches` | `content` | `count`）。

**`execute`** —— shell 执行器。参数：`command`、`timeout`。文档特别强调"避免用 find、grep 这类搜索命令，改用 grep、glob 工具"以及"避免用 cat、head、tail 这类读取命令，改用 read_file"。这是 Claude Code 风格的"固化"工作流。

**`task`** —— subagent 生成器。参数：`description`、`subagent_type`（默认 `general-purpose`）。每次生成都是无状态的。

### 内置工具行为模型小结

所有 deepagents 内置文件系统工具（`ls`、`read_file`、`write_file`、`edit_file`、`glob`、`grep`）**都要求以项目根为基准的绝对路径**。这与我们共享工具的约定**完全相反**——我们的工具**要求相对 `sandbox/` 的路径**。模型一旦混用（由于两者看起来很像，几乎必然混用），CWD 假设就会冲突，产生 RunLog 中那种多轮重试的现象。

deepagents 库在 `create_deep_agent` 的 docstring 中这样描述：

> By default, this agent has access to the following tools:
> - `write_todos`: manage a todo list
> - `ls`, `read_file`, `write_file`, `edit_file`, `glob`, `grep`: file operations
> - `execute`: run shell commands
> - `task`: call subagents

`create_deep_agent` 的签名里**没有 `disable_default_tools` 开关**，内置工具总是会被加上。

## 根因 #1 —— 工具命名空间污染

模型看到的是按字母序排列的工具列表。对于"写文件"这一步：

```
...
write_file   (deepagents)   ← 字母序在前，先出现
file_write   (我们的)
...
```

两者的描述看起来都合理（"Writes to a new file in the filesystem" vs "将内容写入 sandbox/ 工作目录下的文件"）。模型选了 `write_file`——内置的那个，不是我们的。

**后果：** 文件写入走了 deepagents 的代码路径，不是我们的 `shared/tools/file_write.py`。这意味着：
- 我们的 `resolve_in_sandbox` 路径守卫被**绕过**
- 我们的 errors-as-payload dict 形状没产生
- 模型学到了错误的 schema（`file_path=...` 而非 `path=...`）

文件确实写到了正确的位置，但纯属巧合：deepagents 的 `write_file` 从真实项目根目录运行，所以相对路径 `sandbox/hello.py` 解析后恰好就是我们沙箱守卫强制限制的那个位置。

## 根因 #2 —— CWD 上下文错位

我们的 `bash_exec` 以 `cwd=SANDBOX_DIR` 运行。模型不知道这一点。它的"我在哪里"心智模型来自它之前调用的 `write_file`——而 `write_file` 是从项目根运行的。

于是模型推理：*"我从项目根写了 `sandbox/hello.py`。要运行它，我得 `cd sandbox` 或者用路径 `sandbox/hello.py`。"*

现实是：bash 已经在 `sandbox/` 里面了。模型尝试的每个绝对路径或 `sandbox/` 前缀路径要么不存在、要么解析错误：

| 尝试 | 命令 | 失败原因 |
|------|------|----------|
| 1 | `cd /sandbox && python hello.py` | `/sandbox` 不是真实的绝对目录——`sandbox/` 是相对项目根的 |
| 2 | `python /sandbox/hello.py` | 同上——文件不存在 |
| 3 | `pwd && ls` | **调试探测**——模型发现 CWD 已经是 `sandbox/`，文件就在手边 |
| 4 | `python /e/2026projects/loop-engineer/sandbox/hello.py` | 从 sandbox CWD 解析的绝对路径；Python 能找到但路径很难看 |
| 5 | `python hello.py` | 终于对了——从 sandbox CWD 出发的相对路径 |

5 次调用中有 3 次产生错误，模型需要读取并恢复。正是这个恢复过程把 `in_tokens` 推到 47k——模型每轮都在读冗长的 bash 错误信息并重新推理路径。

## 为什么 handroll 没有这个问题

handroll 路径只暴露 3 个工具，全是我们的：

```
bash_exec, file_read, file_write
```

没有命名歧义。模型调用 `file_write(path="hello.py", ...)`——相对路径，正是我们沙箱所期望的。然后 `bash_exec(command="python hello.py")`——也是相对路径，第一次就成功，因为 CWD 已经是沙箱了。

两条路径的 system prompt 完全一致。差异**纯粹**在工具表面。

## 含义：记录中所有调用的 `exit_code` 都是 null

我们的 RunLog 为每次 deepagent 工具调用都记录 `exit_code: null`，即便是那些明显报错的（`cd /sandbox && python hello.py`）。这是因为 `deepagent/agent.py:_ingest_event` 只消费 `AIMessage.tool_calls`——即**请求**。真正的 `ToolMessage` 结果（包含 stdout/stderr/exit_code）走的是另一条 LangGraph 事件，我们目前忽略了它：

```python
elif msg_type == "tool":
    # ToolMessage: 工具结果。若 log_tool_call 时 ok=True 是估计值，这里可校正
    pass
```

所以对比用的 RunLog 能告诉你**模型尝试了什么**，但告诉不了你**实际发生了什么**。要看到驱动 47k token 峰值的那些 bash 错误，你需要捕获 `ToolMessage.content` 并事后校正 `ok` / `exit_code` 字段。

## Week 2 可选方案

从最便宜到最彻底：

### 方案 A —— 增强 system prompt

告诉模型它的 bash CWD 就是 `sandbox/`，并要求优先用共享工具而非内置工具：

```
注意：bash_exec 的当前工作目录就是 sandbox/，文件就在当前目录下，直接用相对路径。
优先使用 file_write / file_read / bash_exec，不要使用 write_file / read_file。
```

成本：`DEEP_AGENT_SYSTEM_PROMPT` 里加 2 行。预期可把 bash 尝试次数减半。

### 方案 B —— 记录 ToolMessage 结果

在 `deepagent/agent.py:_ingest_event` 里处理 `elif msg_type == "tool"` 分支：从 `msg.content` 解析退出码/错误信号，更新对应的 `run_log.tool_calls` 条目。这不会改变行为，但能让 RunLog 成为一忠实的对比记录。

### 方案 C —— 过滤内置工具

`create_deep_agent` 不接受 `disable_default_tools` 标志，但编译图的 ToolNode 可以在构造后替换：

```python
agent = create_deep_agent(model=model, tools=ALL_TOOLS_AS_CALLABLES, system_prompt=...)
# 替换 ToolNode 丢弃重叠的内置工具
keep = {"bash_exec", "file_read", "file_write", "write_todos", "task"}
agent.tools = {n: t for n, t in agent.tools.items() if n in keep}
```

这种方式很脆弱——它伸进了 deepagents 的内部结构，版本升级时可能失效。但这是唯一能得到真正干净工具表面、实现公平对比的办法。

## 教学要点

这是把"框架抽象的成本"具象化呈现出来：

- **handroll** = 3 个工具、30 行编排代码、模型一次就成功。
- **deepagent** = 11 个工具（3 个我们的 + 8 个框架注入的）、100 行包装代码、模型试了 5 次。

框架免费送你 `write_todos`/planning/subagents——但它同时塞给模型 3 对重叠的命名让它去区分，而且不会告诉你它的工具和你的冲突了。就 Week 1 的目的（亲眼看清这个权衡）而言，当前行为本身就是答案。
