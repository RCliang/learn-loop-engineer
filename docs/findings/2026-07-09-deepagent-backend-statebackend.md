# Week 2 方案 A 失败 → 真正的根因是 StateBackend

**日期：** 2026-07-09
**任务：** `task_01_simple_script`
**触发场景：** 执行 Week 2 方案 A（增强 system prompt），重跑 `python -m cli run --agent both --task task_01_simple_script`
**前置文档：**
- [2026-07-07-deepagent-tool-namespace-collision.md](./2026-07-07-deepagent-tool-namespace-collision.md)
- [2026-07-08-deepagent-native-only-tools.md](./2026-07-08-deepagent-native-only-tools.md)

## TL;DR

前一篇 finding 把 deepagent 9 工具路径的失败归因为"路径约定错位 + 模型回避 execute + subagent 吞 token"，并据此把 **方案 A（增强 system prompt）** 列为最高优先级。本实验直接执行方案 A：把沙箱绝对路径显式注入 prompt。**结果：方案 A 失败**——deepagent 依旧失败，21 轮、46k token。

但失败本身揭穿了真正的病根：**deepagents 的默认 backend 是 `StateBackend`，一个内存里的虚拟文件系统**（`graph.py:615`）。所有 `write_file` / `read_file` / `ls` / `glob` / `grep` 都读写 LangGraph state 里的一个 dict，**不碰磁盘**。而我们的 `success_criterion` 查的是真实磁盘 `SANDBOX_DIR/hello.py`——两套世界永远碰不上。同理，`execute` 工具在非 sandbox backend 上会直接返回错误（`graph.py:290-292`），所以模型（或它的 subagent）每次试 `execute` 都吃到错误，"我当前的工具集不包含执行 shell 命令的能力"这句话**事实上是对的**，不是模型犯傻。

把 backend 换成 `FilesystemBackend`（真实磁盘）后，deepagent 立刻成功。**同样 21 轮、同样 46k token，唯一变量是文件是否落盘**——干净到像对照组实验。

## 实验 1：方案 A（prompt 增强，StateBackend）

### 改动

两路 system prompt 同步改为（保持"两路看到相同 prompt"纪律）：

```python
_SANDBOX_ABS = str(SANDBOX_DIR).replace("\\", "/")

SYSTEM_PROMPT = f"""你是一个 Code Agent。你可以调用工具来完成任务。
策略（ReAct）：
1. 思考任务下一步该做什么
2. 如有必要，调用一个或多个工具
3. 观察工具结果
4. 重复直至任务完成，然后给出最终答案

所有文件操作都针对沙箱工作目录，该目录的绝对路径是：
{_SANDBOX_ABS}
读写文件时请使用基于该绝对路径的完整路径（例如 {_SANDBOX_ABS}/hello.py）。"""
```

`deepagent/agent.py` 的 `build_agent()` **不动**——仍用 `create_deep_agent` 的默认 backend。backend 此时是默认值（我们以为是磁盘，其实不是，见下）。

### 结果

| agent     | success | turns | in_tokens | out_tokens | duration_s |
|-----------|---------|-------|-----------|------------|------------|
| handroll  | True    | 3     | 2587      | 272        | 8.63       |
| deepagent | **False**   | **21**    | **46087**     | 834        | 18.11      |

RunLog：`outputs/runs/20260709_123726_980205_deepagent_task_01_simple_script.json`

模型这一次**第一次** write_file 用的就是正确的绝对路径：

```json
{"name": "write_file", "input": {"file_path": "E:/2026projects/loop-engineer/sandbox/hello.py", ...}}
```

prompt 起作用了——模型听话地用了我们给的绝对路径。然后它 `ls('/')`、`glob('*')` 到处找文件，又困惑地写了第二份到 `/hello.py`，再委派 `task` subagent 去"运行 `/hello.py`"，最后 read_file 自我安慰。final_answer 依旧自承失败：

> 由于当前环境没有提供 Shell 执行工具，我无法直接运行该文件……

### 一个反常现象

模型明明把文件写到了正确的绝对路径，为什么 `success_criterion` 仍找不到？运行后查磁盘：

```
SANDBOX_DIR/hello.py exists: False
E:/hello.py exists: False
sandbox contents: ['.gitkeep']
```

**两个 write_file 调用，两个 `ok: true`，磁盘上一个字节都没落。** 这不是路径错位能解释的——路径对了，文件也没出来。方案 A 的假设（"告诉模型正确路径就能修好"）被证伪。

## 真正的根因：StateBackend 是内存虚拟 FS

带着"文件为什么没落盘"的问题翻 deepagents 源码，三处证据拼出全貌：

### 证据 1：默认 backend 是 StateBackend

`deepagents/graph.py:615`：

```python
backend = backend if backend is not None else StateBackend()
```

`create_deep_agent(model, tools=[], system_prompt=...)` 不传 backend 时，默认就是 `StateBackend`。我们一直以为"内置工具读写项目磁盘"，**实际它读写的是 LangGraph state 里的一个 dict**。

### 证据 2：StateBackend.write 进内存，不碰磁盘

`deepagents/backends/state.py:249-265`：

```python
def write(self, file_path: str, content: str) -> WriteResult:
    """Create a new file with content.
    The update is queued directly via `CONFIG_KEY_SEND`."""
    files = self._read_files()
    if file_path in files:
        return WriteResult(error=f"Cannot write to {file_path} because it already exists...")
    new_file_data = create_file_data(content)
    self._send_files_update({file_path: self._prepare_for_storage(new_file_data)})
    return WriteResult(path=file_path)
```

`_read_files()` 读的是 LangGraph state 里的 files dict，`_send_files_update` 把更新塞回 state。**整个过程没有任何 `open()` / `os.open()` / 磁盘 I/O**。文件就是 dict 里一个 key。`WriteResult(path=file_path)` 返回"成功"，但这个"成功"指的是"成功写进了 state dict"——和磁盘无关。

这就是为什么 RunLog 里 `ok: true`、模型也以为自己写成功了，磁盘却空空如也。也解释了 `ls('/')` 为什么看不到东西——模型 ls 的是空荡荡的虚拟 FS 根。

### 证据 3：execute 在非 sandbox backend 上直接报错

`deepagents/graph.py:290-292`（create_deep_agent 的 docstring）：

> The `execute` tool allows running shell commands if the backend implements `SandboxBackendProtocol`. For non-sandbox backends, the `execute` tool will return an error message.

`StateBackend` 和 `FilesystemBackend` 都只实现 `BackendProtocol`，**不实现 `SandboxBackendProtocol`**（`backends/protocol.py:803`）。所以在默认配置下，`execute` 工具虽然暴露在工具表面里，**调一下就返回错误**。

这一条直接翻案了前一篇 finding 的根因 #2（"模型回避 execute"）。模型（或它的 subagent）**没有回避 execute——它试了，execute 本就不能用**。模型那句"当前环境没有提供 Shell 执行工具"，字面意思居然是对的：工具在，但不工作。

> 注：这是间接证据——subagent 内部的 execute 尝试不会冒泡到外层 stream（见前篇根因 #3 的 subagent token 黑盒）。但框架 docstring 是权威说明，且模型行为完全吻合。

## 实验 2：换 FilesystemBackend → 成功

带着"StateBackend 是病根"的假设，把 `build_agent()` 改一行：

```python
return create_deep_agent(
    model=model,
    tools=[],
    system_prompt=DEEP_AGENT_SYSTEM_PROMPT,
    backend=FilesystemBackend(virtual_mode=False),  # 真实磁盘后端
)
```

`FilesystemBackend`（`backends/filesystem.py:67`）直接用 `os.open` / `os.fdopen` 读写真实文件系统，相对路径从进程 CWD 解析。重跑：

| agent     | success | turns | in_tokens | out_tokens | duration_s |
|-----------|---------|-------|-----------|------------|------------|
| handroll  | True    | 3     | 2654      | 315        | 9.63       |
| deepagent | **True**    | 21    | 46705     | 778        | 21.30      |

RunLog：`outputs/runs/20260709_151129_395769_deepagent_task_01_simple_script.json`

运行后磁盘验证：

```
SANDBOX_DIR/hello.py exists: True
content: "print('hello world')\n"
```

**成功了。**

### 这个对照干净到离谱

把实验 1（StateBackend）和实验 2（FilesystemBackend）并排看：

| 配置                | success | turns | in_tokens | out_tokens |
|---------------------|---------|-------|-----------|------------|
| StateBackend        | False   | 21    | 46087     | 834        |
| FilesystemBackend   | **True**   | **21**    | **46705**     | 778        |

**轮次完全相同、token 几乎相同（差 618，<2%）、模型行为轨迹几乎相同**（都是 write_file → ls → glob/write → task subagent → read_file）。唯一变量是文件有没有落到磁盘——而这就是 success 翻转的全部原因。

这等于一次天然的对照实验：模型做了完全一样的工作量，区别只在那条 `WriteResult` 到底落到了 dict 还是 inode。方案 A 的 prompt 起的作用微乎其微——模型在两次实验里都用对了绝对路径，问题从来不在 prompt。

## 对前一篇 findings 根因的修正

本实验之后，[2026-07-08 那篇](./2026-07-08-deepagent-native-only-tools.md) 的四个根因需要重新审视：

| 原根因 | 原结论 | 修正 |
|--------|--------|------|
| #1 路径约定错位 | 模型用 `/sandbox/hello.py`，文件落到盘根 | **降级为症状**。真问题是 StateBackend，文件压根没落盘。即便模型用对绝对路径（本实验已验证），StateBackend 下照样失败。路径混乱只是模型在虚拟 FS 里摸索时的表象。 |
| #2 模型回避 execute | execute 在工具表面里，模型却不用 | **翻案**。execute 在非 sandbox backend 上调一下就报错。模型（subagent）试过，被框架挡回来了，才说"没有 shell 工具"。是框架的限制，不是模型的判断失误。 |
| #3 subagent 是 token 黑盒 | subagent 内部 token 算外层账，事件不冒泡 | **保留**。这条和 backend 无关，依旧成立。 |
| #4 `ok: true` 是估计值 | RunLog 的 ok=True 是 `_ingest_event` 默认值 | **保留并加强**。本实验里 ok=true 还有第二层误导：StateBackend 的 `WriteResult(path=...)` 本身就返回"成功"（写进 dict 成功），ToolMessage 里也不会有错误信号。即便实现了方案 B（捕获 ToolMessage），在 StateBackend 下也只能看到"成功写进 dict"——仍无法发现文件没落盘。 |

最大的教训：**前一篇把"模型表现差"当成了 deepagent 路径的失败原因**（路径乱选、回避 execute、subagent 浪费）。实际上模型做的事相当合理——在一个内存虚拟 FS 里，write 出来的东西它自己 ls 不到、execute 又不能用，它当然会反复探查、委派 subagent、最后自承失败。**是 backend 配置把模型放进了一个注定失败的迷宫，不是模型走错了路。**

## handroll 为什么一直免疫

handroll 的共享工具（`file_write` / `file_read` / `bash_exec`）是我们自己写的，直接 `open()` / `subprocess`，**完全不经过 deepagents 的 backend 层**。所以：

- `file_write(path="hello.py")` → `resolve_in_sandbox` → `SANDBOX_DIR/hello.py` → `open()` 写磁盘。
- `bash_exec(command="python hello.py")` → `subprocess.run`，cwd 设到 sandbox，真在 shell 里跑。

没有 backend 抽象，就没有"写进 dict 还是写进磁盘"的歧义。handroll 的 3 轮 / 2.6k token 不是因为它"更聪明"，而是因为它的工具语义和验证逻辑天然对齐——都直接操作磁盘。

这也解释了为什么"12 工具版"（注入共享工具到 deepagent）能勉强成功：模型一旦选中共享 `file_write`（而非内置 `write_file`），就走真实磁盘，绕开了 StateBackend。共享工具是"唯一能把文件送到验证逻辑要查位置"的工具——这句话前一篇说过，现在有了更精确的版本：**共享工具是唯一不经 backend 的工具**。

## 新的 baseline 配置

本 PR 已把 deepagent 路径的 baseline 改为：

```python
create_deep_agent(
    model=model,
    tools=[],
    system_prompt=DEEP_AGENT_SYSTEM_PROMPT,
    backend=FilesystemBackend(virtual_mode=False),
)
```

理由：

1. **公平对比**。handroll 的工具操作真实磁盘，deepagent 也应该。StateBackend 默认值让 deepagent 在一个内存沙盒里空转，不是"纯框架能力"的公平测量。
2. **success_criterion 是磁盘语义**。它 `subprocess.run` 真跑 `SANDBOX_DIR/hello.py`。只有真实磁盘 backend 能和它对齐。
3. **保留 9 工具纯度**。仍用 `tools=[]`，不注入共享工具。换 backend 不破坏"纯框架 vs 纯手写"的对比维度，反而修好了它。

`virtual_mode=False` 显式指定，避免 deepagents 0.6.0 默认值变更引入的 deprecation 警告，也表明"我们就是要真实 FS 访问，不要虚拟路径锚定"。安全上：这是教育项目，本就无敏感数据，FilesystemBackend 的"agent 能读任意文件"风险不适用。

## Week 2 方案再评估（再次重排）

| 方案 | 原评估 | 本轮后 |
|------|--------|--------|
| **方案 A（prompt 增强）** | 最高优先级、最便宜 | **已执行，证伪**。prompt 不是病根。改动作为副作用保留（模型用对绝对路径有微弱好处），但不再是"修方案"。 |
| **方案 B（捕获 ToolMessage）** | 高优先级 | **降级**。在 FilesystemBackend 下，ToolMessage 能反映磁盘写入成功/失败，价值恢复。但单靠它仍无法穿透 subagent 内部。 |
| **方案 C（只留共享工具）** | 待试 | **意义改变**。共享工具不经 backend，本来就是"真磁盘"路径。在 FilesystemBackend baseline 下，方案 C 变成"用我们的工具替换内置工具"的对比，不再背"修 success"的包袱。 |
| **新方案 D（穿透 subagent 流）** | —— | **最高优先级**。21 轮 / 46k token 里约一半花在 subagent 黑盒。不把 subagent 的 tool_calls 摊到 RunLog，deepagent 的 token 账永远是一本糊涂账。 |
| **新方案 E（换 SandboxBackend）** | —— | 若想让模型自己也能 `execute`（而非靠 success_criterion 代跑），需要换成实现 `SandboxBackendProtocol` 的 backend。代价：要接 docker / 真沙箱，工程量大。对当前 task_01 不必要。 |

**下一个实验**：方案 D。在 FilesystemBackend baseline 上，想办法把 `task` subagent 的内部 tool_calls 也记进 RunLog，看清那 ~10k token 到底花在哪几步。

## 教学要点

- **框架的"默认值"是最容易踩的坑**。`create_deep_agent` 的默认 `StateBackend` 对一个 Web agent（状态隔离、无磁盘依赖）是合理的；对一个要和磁盘 success_criterion 对齐的 Code Agent 就是陷阱。读 docstring 看到默认 backend 时，第一反应该是"它把文件写到哪了"，而不是假设它写磁盘。
- **"模型表现差"和"环境配错了"要先分清**。前一篇花了大篇幅分析模型的路径选择、execute 回避、subagent 浪费——全是真的，但全是**次要**的。模型在一个注定失败的迷宫里表现得其实相当合理。换掉迷宫（backend），同样聪明的模型立刻就成功了。
- **对照实验的力量**。实验 1 vs 实验 2，轮次和 token 几乎完全相同，唯一变量是 backend。这种"只改一个变量、其他全锁住"的对照，比任何源码分析都更有说服力。StateBackend 是病根这个结论，不是猜的，是控出来的。
