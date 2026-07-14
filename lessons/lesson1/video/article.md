# 第一课：从一个 for 循环到一个能用的 Agent

> 本文件 = 原始教学分镜脚本（保留不删）。`script.md` 是平台化口播稿，
> 本文件是画面信息密度源。开发章节画面时回这里抽细节。

> 系列：从零构建 Agent 应用
> 时长预估：20-25 分钟
> 目标：观众跟完这期视频后，能用 150 行 Python 写出一个可工作的 Code Agent

---

## 开场 Hook（0:00 - 1:30）

**【画面】** 终端录屏：运行 v4_final.py，Agent 自动创建 hello.py 并运行成功

**【口播】**

大家好，从今天开始我们做一个系列——从零构建 Agent 应用。

先看一个效果：我给 Agent 一个任务——"创建一个 hello.py 文件，然后运行它"。

（指向终端）你看，它自己思考了一下，调了 file_write 写了文件，然后调了 bash_exec 运行，看到输出是 hello world，判断任务完成了。

整个过程 3 轮对话，2 次工具调用。

这个 Agent 的核心代码，只有 150 行。

而且我要告诉你一个可能颠覆直觉的事实：**市面上你天天在用的 AI coding agent——Cursor、Claude Code、Cline——它们的核心，都是一个 for 循环。**

今天我们就从一个空的 for 循环开始，一步步把它变成刚才你看到的这个 Agent。

---

## 第一段：最小循环 —— 能想，但不能做（1:30 - 5:00）

**【画面】** 打开 v1_bare_loop.py，从空文件开始写

**【口播】**

好，打开编辑器，我们从零开始。

一个 Agent 最最最核心的结构是什么？就是一个循环——反复调 LLM，直到任务完成。

```python
for turn in range(max_turns):
    resp = client.chat.completions.create(model=MODEL, messages=messages)
    reply = resp.choices[0].message.content
    messages.append({"role": "assistant", "content": reply})
```

就这几行。这就是 v1。

我们跑一下看看什么效果。

（运行 v1）

你看，LLM 很努力地告诉你"我帮你创建了 hello.py"，但实际上什么都没发生。因为它只能说话，不能动手。

这就像一个人坐在椅子上告诉你"我帮你把门关了"——嘴上说完了，门还开着。

**此时的问题很明确：Agent 需要"手"。**

---

## 第二段：加上工具 —— 能做事了（5:00 - 12:00）

**【画面】** 打开 v2_with_tools.py

**【口播】**

要让 Agent 能做事，我们需要解决三个问题：

1. **告诉 LLM 它有哪些工具**（tools schema）
2. **解析 LLM 的工具调用请求**（parse tool_calls）
3. **实际执行工具并把结果回传**（execute + feedback）

先看第一个——工具定义。这其实就是一段 JSON Schema，告诉 LLM：你有 `bash_exec` 和 `file_write` 两个工具可以用。

```python
TOOLS = [{
    "type": "function",
    "function": {
        "name": "bash_exec",
        "description": "在工作目录中执行 shell 命令",
        "parameters": {...}
    }
}]
```

关键点：**description 写得越清晰，LLM 选对工具的概率越高。** 这不是废话——后面的课程我们会用实验数据证明这一点。

然后是执行器——拿到 LLM 返回的工具名和参数，实际执行：

```python
def execute_tool(name, args):
    if name == "bash_exec":
        proc = subprocess.run(args["command"], ...)
        return f"exit_code={proc.returncode}\nstdout: {proc.stdout}"
    elif name == "file_write":
        Path(args["path"]).write_text(args["content"])
        return f"已写入..."
```

最后是循环里的改动——加一个关键判断：

```python
if not msg.tool_calls:
    print("✓ 任务完成")
    return
```

**当 LLM 不再调用任何工具，就表示它认为任务完成了。** 这是 OpenAI function calling 协议的一个隐式约定。

（运行 v2）

这次你看——Turn 1 它调了 file_write 创建文件，Turn 2 调了 bash_exec 运行文件，Turn 3 看到输出正确，不再调用工具，结束。

**能做事了。** 但有一个隐患——

如果 LLM 出了 bug，一直不停地调工具怎么办？比如它反复运行同一个命令，永远停不下来？

这就引出了下一个组件。

---

## 第三段：Evaluator —— 给 Agent 装刹车（12:00 - 17:00）

**【画面】** 打开 v3_with_evaluator.py，重点展示 Evaluator 类

**【口播】**

没有刹车的 Agent 是危险的。不是因为它会伤害你，而是因为它会烧光你的 token 账单。

我们给它装三个刹车：

**刹车 1：硬上限。** max_turns 到了就停，无论如何。这是最后的保险丝。

**刹车 2：死循环检测。** 如果 Agent 连续 3 次做完全相同的操作（hash 一致），强制停止。这对应 LLM 陷入循环的情况——比如它反复尝试一个不存在的命令。

```python
h = hashlib.md5(json.dumps(last_action, sort_keys=True).encode()).hexdigest()
if self._action_hashes.count(h) >= 2:
    return True, "loop_detected"
```

**刹车 3（高级）：self-critique。** 用另一次 LLM 调用问"任务完成了吗？"。这个我们在 v3 中先不实现，留到下一课展开讲。

核心 insight 是：**Evaluator 是 Agent 可靠性的关键组件。** 不是 LLM 越强 Agent 就越好——是 Evaluator 越靠谱，Agent 才越可控。

（演示死循环场景——可以构造一个会失败的命令让 LLM 反复重试）

你看，如果没有 Evaluator，这里会一直跑下去。有了它，3 次重复后自动停止。

---

## 第四段：Observation 格式化 —— 让 Agent 看得懂结果（17:00 - 21:00）

**【画面】** 打开 v4_final.py，对比 raw 结果和格式化后的结果

**【口播】**

最后一个组件——Observation 格式化。

先看一个问题：工具执行完了，结果长什么样？

如果我们直接把 subprocess 的原始输出扔给 LLM：

```
{"ok": true, "exit_code": 0, "stdout": "hello world\n", "stderr": "", "duration_s": 0.123}
```

LLM 能理解吗？能，但费力。尤其当错误发生时：

```
{"ok": false, "error_type": "TimeoutExpired", "message": "超时 30s", "stdout": "", "stderr": "", "exit_code": -1}
```

格式化之后呢？

```
[错误] bash_exec 失败: 命令超时(30s)
```

一目了然。LLM 立刻知道发生了什么、该怎么处理。

```python
def format_observation(tool_name, result):
    if not result.get("ok"):
        return f"[错误] {tool_name} 失败: {result.get('message')}"
    if tool_name == "bash_exec":
        return f"退出代码: {result['exit_code']}\n输出:\n{result['stdout']}"
```

**格式化的目标不是美观，是让 LLM 在下一轮推理时做出更好的决策。**

这个设计选择——structured vs raw——实际上是可以量化对比的。后面我们会做 A/B 实验，用数据告诉你哪种格式更省 token、成功率更高。

---

## 收尾总结 + 预告（21:00 - 23:00）

**【画面】** 一张四层结构的图：v1→v2→v3→v4

**【口播】**

好，回顾一下今天我们做了什么。从一个空的 for 循环，逐步加入了四层能力：

| 版本 | 加入的能力 | Agent 的状态 |
|------|-----------|-------------|
| v1 | LLM 调用循环 | 能想，不能做 |
| v2 | 工具定义 + 执行 | 能做事了 |
| v3 | Evaluator 三层刹车 | 知道什么时候停 |
| v4 | Observation 格式化 | 看得懂结果 |

最终代码 150 行，是一个完整的、可运行的 Code Agent。

但我要给你留一个思考题：

这 150 行代码，如果用 LangChain 的 `create_react_agent` 来写，只需要大约 5 行。那它帮你省掉了什么？它又偷偷加了什么？

下一课，我们就把同样的任务用 LangChain deepagents 跑一遍，然后一行一行拆开看——框架到底做了什么。

我们会发现：框架的 system prompt 比我们手写的长 30 倍，token 消耗高 31 倍，但完成同样的任务。这是"抽象的代价"。

好，第一课就到这里。代码在 GitHub 仓库的 lesson1/code 目录下，v1 到 v4 四个文件，你可以照着从头写一遍。

我们下期见。

---

## 拍摄 / 剪辑备注

- **开场**用终端录屏 + 画中画人脸，建立"这不是 PPT 课"的调性
- **代码段**建议用 VS Code 的 zen mode + 大字号，每次只展示当前版本新增的关键代码
- **v1→v2→v3→v4 的过渡**可以用"文件切换"的动画，让观众感受到渐进演化
- **运行演示**每个版本都实际跑一次，让观众看到输出变化
- **收尾的表格**用后期叠加动画，从左到右逐行出现
- 全片不放 BGM 或极低音量纯音乐，技术视频吵了反而分心
