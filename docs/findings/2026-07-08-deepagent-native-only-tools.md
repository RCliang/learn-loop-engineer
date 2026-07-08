# 去掉共享工具后 —— Deepagent 原生 9 工具为何直接失败

**日期：** 2026-07-08
**任务：** `task_01_simple_script`（创建 `sandbox/hello.py`，运行，验证输出 "hello world"）
**触发场景：** 在 `create_deep_agent(..., tools=[])` 后重跑 `python -m cli run --agent both --task task_01_simple_script`
**前置文档：** [2026-07-07-deepagent-tool-namespace-collision.md](./2026-07-07-deepagent-tool-namespace-collision.md)

## TL;DR

上一篇 finding 提出了"去掉我们 3 个共享工具、只留 deepagents 9 个内置工具"作为方案 C 的等价做法。本实验直接验证：**把 `tools=ALL_TOOLS_AS_CALLABLES` 改成 `tools=[]` 后，deepagent 路径从"成功但难看"变成"直接失败"**。失败原因不再是命名冲突，而是更根本的三层错位：路径约定错位 + 模型回避 `execute` + subagent 吞掉 token。handroll 路径不受影响，依旧 3 轮干净完成。

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
| deepagent（12 工具）  | True    | 21    | 47202     | 563        | 12.64      |
| **deepagent（9 工具，本次）** | **False**   | **9**     | **18789**     | **402**        | **12.38**      |

三路对比讲清了故事：
- handroll 永远 3 轮、2 千多 input token，干净利落。
- 上一版 12 工具的 deepagent：成功，但 21 轮、47k token——被命名冲突和 CWD 错位反复折磨。
- 本次 9 工具的 deepagent：**失败**，9 轮、18k token——命名冲突没了，结果更糟。

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

- `loop_turns = 9`，但 `tool_calls` 只有 2 条。差的 7 轮去哪了？—— 全在 `task` subagent 内部消耗掉了（见根因 #3）。
- `total_input_tokens = 18789`，对于一个"创建并运行 hello.py"的任务高得离谱。原因同样是 subagent。
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

### 和上一篇的对照

上一篇（12 工具）里，模型也选了内置 `write_file`，但用的是**相对路径** `sandbox/hello.py`，从项目根解析恰好命中项目 sandbox 目录，所以文件落对了位置。本次（9 工具）模型改用了**绝对路径** `/sandbox/hello.py`——可能是 system prompt 里"当前工作目录（sandbox/）"这句话让模型把 `/sandbox/` 当成了真实的文件系统根。

## 根因 #2 —— 模型回避 `execute`，改用 `task` subagent

`execute` 工具明确在工具表面里，描述是"在隔离沙箱环境中执行 shell 命令"。但模型没选它，而是调用了 `task` subagent 去代为运行 `python hello.py`。

可能的原因：
1. `execute` 的描述里有大量"避免用 find/grep/cat，改用 grep/glob/read_file 工具"的工作流规训，可能让模型对直接 shell 调用产生犹豫。
2. `task` subagent 描述里有"处理复杂多步任务"的暗示，模型可能把"运行一个文件"误判为需要委派。
3. 模型在 system prompt 里读到"所有文件操作被限制在当前工作目录"，可能误以为没有 shell 工具。

无论原因是什么，结果是模型把一个本可一步完成的命令执行，委派给了一个无状态的 subagent。subagent 有自己的工具表面（同样是这 9 个内置工具），它内部又得重新推理路径、重新尝试——这正好解释了下面的 token 放大。

## 根因 #3 —— Subagent 吞掉 token，但不留轨迹

`loop_turns = 9` 与 `tool_calls` 数 = 2 的差距，是 subagent 内部消耗的明证。`_ingest_event` 只消费最外层 LangGraph 事件的 `AIMessage.tool_calls`——subagent 在自己的子图里跑，它内部的 LLM 调用、工具调用、token 消耗**不会作为顶层事件冒泡**到我们的 RunLog。

但 token 统计躲不开：`total_input_tokens = 18789` 包含了 subagent 内部所有的 LLM 调用。这些 token 花在了我们看不见的地方——subagent 可能内部又试了 `execute`、又 `ls` 探查、又 `read_file` 确认，最终回报失败。这 18k token 的细节，RunLog 里一个字都没有。

这是 deepagents 框架的"抽象税"最尖锐的体现：**subagent 是黑盒，对比记录看不到它的内部行为**。handroll 路径没有 subagent 概念，每个工具调用都在 RunLog 里明明白白。

## 根因 #4 —— `ok: true` 是估计值，不是事实

RunLog 里两条 tool_call 都标了 `"ok": true, "exit_code": null`。这是上一篇已经记录的问题的延续：`_ingest_event` 在 `AIMessage.tool_calls` 分支里**默认写 `ok=True`**（`deepagent/agent.py:84`），而真正的 `ToolMessage` 结果（含错误信号）走的是另一个事件，我们目前 `pass` 掉了：

```python
elif msg_type == "tool":
    # ToolMessage: 工具结果。若 log_tool_call 时 ok=True 是估计值，这里可校正
    pass
```

所以 `write_file` 即便真的失败了（比如 `E:\sandbox\` 不存在导致写文件异常），RunLog 里仍然显示 `ok: true`。这让人很难从 RunLog 单方面判断到底是"文件写错地方"还是"文件根本没写出来"。要区分两者，必须实现方案 B（捕获 ToolMessage）。

## 反讽：去掉命名冲突，结果更糟

直觉上，去掉 3 个共享工具应该让对比更"干净"——没有 `write_file`/`file_write` 的二选一困惑，模型应该表现更好。实际相反：

| 维度             | 12 工具（含共享） | 9 工具（纯内置） |
|------------------|-------------------|------------------|
| 命名冲突         | 3 对              | 0 对             |
| 任务成功         | ✅ True            | ❌ False          |
| 总轮次           | 21                | 9                |
| 总 input token   | 47202             | 18789            |
| 失败模式         | CWD 错位 → 5 次 bash 重试 | 路径错位 → 文件落错位置 + subagent 黑盒 |

原因在于：**我们的共享工具是唯一一个把文件强制写到项目 `sandbox/` 的工具**。去掉它之后，工具表面里没有任何工具会自然地把文件送到验证逻辑要查的位置。deepagents 的 `write_file` 用绝对路径，模型心智模型里的"沙箱根"和真实文件系统根对不上，于是文件失踪。

命名冲突是表象，**路径约定的根本性错位**才是病根。去掉冲突只是把病根暴露得更明显。

## 教学要点更新

把上一篇的 takeaway 推进一层：

- **handroll** = 3 个工具、30 行编排代码、工具描述与沙箱约定自洽，模型一次就成功。
- **deepagent + 共享工具（12 个）** = 命名冲突让模型选错工具，但所选工具**碰巧**用相对路径命中了 sandbox，所以勉强成功。
- **deepagent + 纯内置（9 个）** = 命名冲突消失，但没有任何工具对接项目 sandbox 约定，模型按内置工具的绝对路径心智模型走，文件落空，**直接失败**。

框架免费送你 `write_todos` / planning / subagents，但它的文件系统工具假设自己的"项目根"就是世界中心，不会迁就你外部的 sandbox 约定。**"公平对比"不是简单地把一边的工具拿掉**——你需要要么让两边的路径约定一致（方案 A 的 prompt 工程、或让 deepagents 的工具认识到 sandbox），要么接受两边在做"不同的事"的对比。

## Week 2 方案再评估

在本次实验之后，原方案优先级需要重排：

- **方案 A（增强 system prompt）** —— 现在是**最高优先级**且最便宜。告诉模型"沙箱目录的绝对路径是 `<项目根>/sandbox/`，bash CWD 已在该目录下"，预期能同时修掉 12 工具版的 CWD 错位和 9 工具版的路径错位。
- **方案 B（记录 ToolMessage 结果）** —— 仍是高优先级。本次实验中 `write_file` 到底成功没成功，RunLog 看不出来；必须捕获 ToolMessage 才能区分"文件写错地方"和"文件写失败"。
- **方案 C（过滤内置工具，只留共享工具）** —— 与本次实验相反的方向。如果想让 deepagent 用我们的共享工具而不被内置工具干扰，需要在 `create_deep_agent` 之后替换 ToolNode（脆弱、易在升级时失效）。本次实验证明了"只留内置"行不通，那"只留共享"是不是更好？值得作为下一个实验。
