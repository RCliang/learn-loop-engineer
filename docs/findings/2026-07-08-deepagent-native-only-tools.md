# 去掉共享工具后 —— Deepagent 原生 9 工具为何直接失败

**日期：** 2026-07-08
**任务：** `task_01_simple_script`（创建 `sandbox/hello.py`，运行，验证输出 "hello world"）
**触发场景：** 在 `create_deep_agent(..., tools=[])` 后重跑 `python -m cli run --agent both --task task_01_simple_script`
**前置文档：** [2026-07-07-deepagent-tool-namespace-collision.md](./2026-07-07-deepagent-tool-namespace-collision.md)

## TL;DR

上一篇 finding 提出了"去掉我们 3 个共享工具、只留 deepagents 9 个内置工具"作为方案 C 的等价做法。本实验直接验证：**在 `create_deep_agent(..., tools=[])` 配置下，deepagent 路径直接失败**。失败原因不是命名冲突，而是更根本的三层错位：路径约定错位 + 模型回避 `execute` + subagent 吞掉 token。handroll 路径不受影响，依旧 3 轮干净完成。

## 实验设置变更

`deepagent/agent.py` 一行改动：

```python
# 改动前
return create_deep_agent(
    model=model,
    tools=ALL_TOOLS_AS_CALLABLES,   # 3 个共享工具 + 9 个内置 = 12 个
    system_prompt=DEEP_AGENT_SYSTEM_PROMPT,
)

# 改动后
return create_deep_agent(
    model=model,
    tools=[],                        # 只用 9 个内置工具
    system_prompt=DEEP_AGENT_SYSTEM_PROMPT,
)
```

system prompt **保持不变**——两路看到相同 prompt，只有工具表面不同，这是单一变量。

### 改动后实测工具表面

通过 `agent.get_graph().nodes["tools"].data.tools_by_name` 抓取，确认 ToolNode 现在恰好暴露 9 个工具：

```
Total tools: 9
  - edit_file
  - execute
  - glob
  - grep
  - ls
  - read_file
  - task
  - write_file
  - write_todos
```

命名空间干净了——不再有 `write_file` / `file_write` 这种 3 对冲突。

## 观察现象

运行 `python -m cli run --agent both --task task_01_simple_script`：

| agent                 | success | turns | in_tokens | out_tokens | duration_s |
|-----------------------|---------|-------|-----------|------------|------------|
| handroll              | True    | 3     | 2361      | 196        | 8.51       |
| **deepagent（9 工具，本次）** | **False**   | **9**     | **18789**     | **402**        | **12.38**      |

两路对比讲清了故事：
- handroll 永远 3 轮、2 千多 input token，干净利落。
- 9 工具的 deepagent：**失败**，9 轮、18k token——工具表面干净（9 个内置工具无重名），任务却没完成。

> ⚠️ **turns 列要先打个星号看**：handroll 和 deepagent 的 `loop_turns` 量的不是同一个东西，详细拆解见下面[「⚠️ 指标修正」](#-指标修正loop_turns-数的不是-llm-调用)一节。简言之：handroll 的 3 = 3 次 LLM 调用；deepagent 的 9 ≈ 3 次 LLM 调用被图的节点粒度膨胀到 9 个 stream 事件。**真正的差距在 token，不在 turns。**

## ⚠️ 指标修正：`loop_turns` 数的不是 LLM 调用

在深入根因之前，必须先纠正上面这张表的一个误导。

- **handroll** 的 `loop_turns` = `for turn in range(max_turns)` 循环次数 = **LLM 调用数**。3 轮 = 模型想了 3 次。
- **deepagent** 的 `loop_turns` = `agent.stream(stream_mode="updates")` 产出的事件数 = **LangGraph 节点更新数**。9 轮 ≠ 模型想了 9 次。

### deepagents 的图其实有 6 个节点

通过 `agent.get_graph().nodes` 抓取，编译图不止 `model ↔ tools` 两个节点，还有两个中间件节点：

```
__start__
  → PatchToolCallsMiddleware.before_agent    ← 中间件，run 启动时跑一次
  → model                                    ← 真正的 LLM 调用
  → TodoListMiddleware.after_model           ← 中间件，每次 model 后跑，决定路由
  → tools (条件性)                           ← 工具执行
__end__
```

`TodoListMiddleware.after_model` 是 deepagents 的 todo-list 中间件，在**每次** LLM 调用后都跑一遍做路由判断，**每个节点更新都发一个 stream 事件**。所以一次"模型决策 + 工具调用"会被数成 ~3 个事件。

### 实测事件拆解

用诊断脚本流式打印每个事件的节点名（这次重跑出 12 事件，结构与 9-turn run 一致，只是模型多做了一次 `read_file` 探查）：

| #   | 节点                                  | LLM 调用？ | 做了什么                                     |
|-----|---------------------------------------|-----------|----------------------------------------------|
| 1   | `PatchToolCallsMiddleware.before_agent` | ❌         | run 启动中间件                                |
| 2   | **`model`**                           | ✅ #1      | 决定调 `write_file`                           |
| 3   | `TodoListMiddleware.after_model`      | ❌         | 路由到 tools                                  |
| 4   | `tools`                               | ❌         | 执行 write_file                               |
| 5   | **`model`**                           | ✅ #2      | 决定调 `task` subagent                        |
| 6   | `TodoListMiddleware.after_model`      | ❌         | 路由到 tools                                  |
| 7   | `tools`                               | ❌         | 执行 task subagent（**18k token 大头藏这一条**）|
| 8   | **`model`**                           | ✅ #3      | 决定调 `read_file`                            |
| 9   | `TodoListMiddleware.after_model`      | ❌         | 路由到 tools                                  |
| 10  | `tools`                               | ❌         | 执行 read_file                                |
| 11  | **`model`**                           | ✅ #4      | 最终回答                                      |
| 12  | `TodoListMiddleware.after_model`      | ❌         | 路由到 `__end__`                              |

（原 9-turn run 结构相同，只是模型在 subagent 回报后直接放弃，少了一次 read_file 往返，所以 9 而非 12。）

### 按类别归类

| 类别                                          | 事件数 | 占比   |
|-----------------------------------------------|--------|--------|
| 真正的 LLM 调用（`model` 节点）                | 3-4    | ~33%   |
| 中间件过路（`before_agent` + 每次 `after_model`）| 4-5    | ~42%   |
| 工具执行（`tools` 节点）                       | 2-3    | ~25%   |

**9 turns ≈ 3 次 LLM 调用**，和 handroll 的 3 次几乎打平。turns 这一列 deepagent 看起来差 3 倍，**纯粹是图粒度的测量假象**。

### 那 token 为什么还是差 8 倍

turns 打平了，token 差距（18k vs 2.3k）却是真的，三个来源：

1. **工具 schema 重复计费** —— 每次 `model` 调用都在 context 里塞 9 个工具的完整 schema（`write_todos`、`task` subagent 的描述特别冗长）。handroll 只塞 3 个。光定义每次就多 ~1-2k token，3-4 次调用累计多 4-8k。
2. **subagent 黑盒** —— 事件 7 那个 `tools` 节点内部，subagent 跑了自己的多轮 LLM 调用（推理、尝试 execute、失败、回报）。这些调用的 token **全算在 outer 的 `usage_metadata` 里**，但它们的 stream 事件**不冒泡**——所以 turn 数没涨、token 却炸了。详细见根因 #3。
3. **中间件状态** —— `TodoListMiddleware` 往 context 注入 todo-list 状态，每次又是一份开销。

**结论：deepagent 的真正代价不在"多想了几次"，而在每次想的 context 被框架的 schema 和中间件撑大了，外加 subagent 把内部 token 全记到外层账上。**

## 证据：deepagent 路径的完整轨迹

RunLog（`outputs/runs/20260708_195154_092780_deepagent_task_01_simple_script.json`）记录了**两次工具调用**：

```json
"tool_calls": [
  {
    "name": "write_file",
    "input": {
      "file_path": "/sandbox/hello.py",
      "content": "print('hello world')\n"
    },
    "ok": true,
    "duration_s": 0.0,
    "exit_code": null
  },
  {
    "name": "task",
    "input": {
      "description": "在当前工作目录 /sandbox/ 下，运行命令 `python hello.py`，并将命令的输出返回给我。",
      "subagent_type": "general-purpose"
    },
    "ok": true,
    "duration_s": 0.0,
    "exit_code": null
  }
]
```

模型的 `final_answer` 自我承认失败：

> 我已成功创建了 `/sandbox/hello.py` 文件……不过，我当前的工具集不包含执行 shell 命令的能力，因此无法直接运行该 Python 文件来验证输出。

注意模型说"我当前的工具集不包含执行 shell 命令的能力"——**这是错的**，`execute` 工具就在它的工具表面里。它没用。

### 关键反差

- `loop_turns = 9`，但 `tool_calls` 只有 2 条。**这并不是 subagent 在外层账上多跑了 7 轮**——见上面[「⚠️ 指标修正」](#-指标修正loop_turns-数的不是-llm-调用)，9 个事件里有 4-5 个是中间件过路、2-3 个是 tools 节点，真正的 LLM 调用只有 ~3 次。subagent 的内部轮次藏在事件 7 那个 `tools` 节点里、不冒泡，但它的 token 算在外层账上（见根因 #3）。
- `total_input_tokens = 18789`，对于一个"创建并运行 hello.py"的任务高得离谱。这是 schema 重复计费 + subagent 黑盒 + 中间件状态三件事的叠加，详见指标修正节末尾。
- 项目 `sandbox/` 目录在运行后**仍然为空**——文件根本没落到验证逻辑要查的位置。

## 根因 #1 —— 路径约定不匹配

模型调用 `write_file(file_path="/sandbox/hello.py")`，用了 Unix 风格的绝对路径 `/sandbox/...`。deepagents 内置 `write_file` 从 LangGraph 进程的 CWD（项目根）运行，把这条路径交给文件系统。

在 Windows 上用 Python 验证落点：

```python
>>> from pathlib import Path
>>> Path("/sandbox/hello.py").resolve()
WindowsPath('E:/sandbox/hello.py')
>>> Path("/sandbox/hello.py").exists()
False
>>> Path("E:/sandbox").exists()
False
```

也就是说：
- 模型心智里的"沙箱根" = `/sandbox/`
- 文件系统的真实解析 = `E:\sandbox\hello.py`（当前盘根）
- 任务验证逻辑查的位置 = `E:\2026projects\loop-engineer\sandbox\hello.py`（项目 sandbox）

**三套路径，两两不一致。** 文件没有落到验证要查的目录，`success_criterion` 直接返回 `False`。

更微妙的是：`E:\sandbox\` 这个目录根本不存在。deepagents 的 `write_file` 大概率在尝试创建该路径时失败或写到了某处不可见的位置（RunLog 的 `ok: true` 是我们 `_ingest_event` 的默认估计值，不是真实结果——见根因 #4）。

## 根因 #2 —— 模型回避 `execute`，改用 `task` subagent

`execute` 工具明确在工具表面里，描述是"在隔离沙箱环境中执行 shell 命令"。但模型没选它，而是调用了 `task` subagent 去代为运行 `python hello.py`。

可能的原因：
1. `execute` 的描述里有大量"避免用 find/grep/cat，改用 grep/glob/read_file 工具"的工作流规训，可能让模型对直接 shell 调用产生犹豫。
2. `task` subagent 描述里有"处理复杂多步任务"的暗示，模型可能把"运行一个文件"误判为需要委派。
3. 模型在 system prompt 里读到"所有文件操作被限制在当前工作目录"，可能误以为没有 shell 工具。

无论原因是什么，结果是模型把一个本可一步完成的命令执行，委派给了一个无状态的 subagent。subagent 有自己的工具表面（同样是这 9 个内置工具），它内部又得重新推理路径、重新尝试——这正好解释了下面的 token 放大。

## 根因 #3 —— Subagent 是 token 黑盒

> **修正说明**：本节初版把 `loop_turns=9` 与 `tool_calls=2` 的差距归因于"subagent 内部轮次冒泡到了外层 stream"。**这是错的**，已在上面[「⚠️ 指标修正」](#-指标修正loop_turns-数的不是-llm-调用)纠正：9 个事件全是外层图的节点（model + 中间件 + tools），subagent 的内部事件不冒泡。本节保留下来的有效结论是关于 **token** 的盲区，不是 turns。

`task` subagent 在事件 7 那个 `tools` 节点内部跑了自己的 LangGraph：自己的 LLM 调用、自己的工具尝试、自己的失败重试。`_ingest_event` 只消费最外层事件的 `AIMessage.tool_calls`——subagent 的内部 tool_calls **不会出现在我们的 RunLog 里**。

但 token 统计躲不开：subagent 内部所有 LLM 调用的 token **会聚合进外层的 `usage_metadata`**。`total_input_tokens = 18789` 里，外层那 3 次 `model` 调用可能只占 ~6-8k，剩下 ~10k 是 subagent 内部黑盒消耗的——它可能试了 `execute`、又 `ls` 探查、又 `read_file` 确认，最终回报失败。这 ~10k token 的细节，RunLog 里一个字都没有。

这是 deepagents 框架的"抽象税"最尖锐的体现：**subagent 让对比记录出现了一个"看得见 token、却看不见行为"的盲区**。handroll 路径没有 subagent 概念，每个工具调用都在 RunLog 里明明白白。

要补这个盲区，光实现方案 B（捕获 ToolMessage）还不够——还得能穿透 subagent 的内部流，把 subagent 的 tool_calls 也摊到 RunLog 里。这是 Week 2 之后的工程。

## 根因 #4 —— `ok: true` 是估计值，不是事实

RunLog 里两条 tool_call 都标了 `"ok": true, "exit_code": null`。这是上一篇已经记录的问题的延续：`_ingest_event` 在 `AIMessage.tool_calls` 分支里**默认写 `ok=True`**（`deepagent/agent.py:84`），而真正的 `ToolMessage` 结果（含错误信号）走的是另一个事件，我们目前 `pass` 掉了：

```python
elif msg_type == "tool":
    # ToolMessage: 工具结果。若 log_tool_call 时 ok=True 是估计值，这里可校正
    pass
```

所以 `write_file` 即便真的失败了（比如 `E:\sandbox\` 不存在导致写文件异常），RunLog 里仍然显示 `ok: true`。这让人很难从 RunLog 单方面判断到底是"文件写错地方"还是"文件根本没写出来"。要区分两者，必须实现方案 B（捕获 ToolMessage）。

## 教学要点更新

把上一篇的 takeaway 推进一层：

- **handroll** = 3 个工具、30 行编排代码、工具描述与沙箱约定自洽，模型一次就成功。
- **deepagent + 纯内置（9 个）** = 没有任何工具对接项目 sandbox 约定，模型按内置工具的绝对路径心智模型走，文件落空，**直接失败**。

框架免费送你 `write_todos` / planning / subagents，但它的文件系统工具假设自己的"项目根"就是世界中心，不会迁就你外部的 sandbox 约定。**"公平对比"不是简单地把一边的工具拿掉**——你需要要么让两边的路径约定一致（方案 A 的 prompt 工程、或让 deepagents 的工具认识到 sandbox），要么接受两边在做"不同的事"的对比。

## Week 2 方案再评估

在本次实验之后，原方案优先级需要重排：

- **方案 A（增强 system prompt）** —— 现在是**最高优先级**且最便宜。告诉模型"沙箱目录的绝对路径是 `<项目根>/sandbox/`，bash CWD 已在该目录下"，预期能修掉 9 工具版的路径错位。
- **方案 B（记录 ToolMessage 结果）** —— 仍是高优先级。本次实验中 `write_file` 到底成功没成功，RunLog 看不出来；必须捕获 ToolMessage 才能区分"文件写错地方"和"文件写失败"。
- **方案 C（过滤内置工具，只留共享工具）** —— 与本次实验相反的方向。如果想让 deepagent 用我们的共享工具而不被内置工具干扰，需要在 `create_deep_agent` 之后替换 ToolNode（脆弱、易在升级时失效）。本次实验证明了"只留内置"行不通，那"只留共享"是不是更好？值得作为下一个实验。
