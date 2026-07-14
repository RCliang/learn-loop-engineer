# 从一个 for 循环到一个能用的 Agent · 口播稿

> 平台风格：B 站技术教程。每段 `---` = 一个 step 边界。
> 念稿字数 ~2050 字，约 8 分 30 秒（4 字/秒）。配合视频网页点击推进。

---

先看个东西。

---

我给这个程序一个任务。就一句话：创建一个 hello.py 文件，然后运行它。

---

它自己想了一下，调了个工具写了文件。又调了个工具运行文件。看到输出是 hello world，判断任务做完了。

---

三轮对话，两次工具调用。整个过程没人插手。

---

这个 Agent 的核心代码，150 行 Python。

---

而且这件事可能跟你的直觉不一样。市面上你天天在用的 AI coding agent——Cursor、Claude Code、Cline——剥到底，核心都是一个 for 循环。

---

今天我们就从这个 for 循环开始，一步步把它变成你刚才看到的那个 Agent。四步，四个文件，v1 到 v4。

---

打开编辑器，从零开始。一个 Agent 最核心的结构到底是什么？

---

就是一个循环。反复调 LLM，直到任务做完。

---

```python
for turn in range(max_turns):
    resp = client.chat.completions.create(model=MODEL, messages=messages)
    reply = resp.choices[0].message.content
    messages.append({"role": "assistant", "content": reply})
```

就这么几行。这就是 v1。我们跑一下。

---

你看，LLM 很努力地告诉你"我帮你创建了 hello.py"。但实际什么都没发生。它只会说话，不会动手。

---

就像一个人坐椅子上跟你说"我帮你把门关了"。话说完了，门还开着。

---

问题很明确：Agent 需要一双手。要让它能做事，得解决三件事。

---

第一，告诉 LLM 它有哪些工具——这就是工具定义，一段 JSON Schema。

---

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

关键是那个 description。写得越清楚，LLM 选对工具的概率越高。这条不是废话，后面课程我会拿实验数据证明。

---

第二，解析 LLM 返回的工具调用。它说"我要调 file_write"，你得接得住。

---

第三，执行，然后把结果回传给 LLM。

---

```python
def execute_tool(name, args):
    if name == "bash_exec":
        proc = subprocess.run(args["command"], ...)
        return f"exit_code={proc.returncode}\nstdout: {proc.stdout}"
    elif name == "file_write":
        Path(args["path"]).write_text(args["content"])
        return f"已写入..."
```

---

循环里还得加一个判断。当 LLM 不再调用任何工具，就表示它认为任务做完了。这是 function calling 协议里一个隐式的约定——不调工具，就是"我做完了"。

---

```python
if not msg.tool_calls:
    print("✓ 任务完成")
    return
```

---

跑一下 v2。Turn 1 调 file_write 写文件，Turn 2 调 bash_exec 运行，Turn 3 看输出对，不再调工具，结束。能做事了。

---

但有个隐患。万一 LLM 出 bug，一直不停调同一个工具呢？反复跑同一个命令，永远停不下来。这就引出下一个组件。

---

没有刹车的 Agent 是危险的。不是它会伤害你，是它会烧光你的 token 账单。

---

给它装三道刹车。第一道，硬上限。max_turns 到了就停，无论如何，这是最后那根保险丝。

---

第二道，死循环检测。同一个操作连续做三次，强制停。

---

```python
h = hashlib.md5(json.dumps(last_action, sort_keys=True).encode()).hexdigest()
if self._action_hashes.count(h) >= 2:
    return True, "loop_detected"
```

实现就是把每次的操作 hash 一下存起来，发现这个 hash 已经出现两次了，就停。

---

第三道更高级，self-critique。再开一次 LLM 调用问它"任务做完了吗"。这条 v3 先不做，留到下一课展开。

---

这里有个点你得记住。Agent 可不可靠，不是看 LLM 有多强，是看 Evaluator 有多靠谱。LLM 越强 Agent 不一定越好，但 Evaluator 越靠谱，Agent 一定越可控。

---

看效果。构造一个一定会失败的命令，LLM 会反复重试。没有 Evaluator，它会一直跑下去。有了它，三次重复后自动停。

---

最后一个组件。Observation 格式化。

---

先看个问题。工具执行完了，结果长什么样？

---

直接把 subprocess 的原始输出扔给 LLM，是这样一坨。

---

```
{"ok": true, "exit_code": 0, "stdout": "hello world\n", "stderr": "", "duration_s": 0.123}
```

LLM 能看懂吗？能，但费劲。尤其出错的时候。

---

```
{"ok": false, "error_type": "TimeoutExpired", "message": "超时 30s", "stdout": "", "stderr": "", "exit_code": -1}
```

格式化之后呢？

---

```
[错误] bash_exec 失败: 命令超时(30s)
```

一目了然。LLM 立刻知道发生了什么、下一步该怎么处理。

---

```python
def format_observation(tool_name, result):
    if not result.get("ok"):
        return f"[错误] {tool_name} 失败: {result.get('message')}"
    if tool_name == "bash_exec":
        return f"退出代码: {result['exit_code']}\n输出:\n{result['stdout']}"
```

格式化的目标不是好看，是让 LLM 下一轮推理时能做出更好的决策。structured 还是 raw，这件事后面我们会做 A/B 实验，拿数据说话。

---

回顾一下。从一个空的 for 循环，加了四层东西。

---

第一层，v1，LLM 调用循环。能想，不能做。

---

第二层，v2，加上工具定义和执行。能做事了。

---

第三层，v3，Evaluator 三道刹车。知道什么时候该停。

---

第四层，v4，Observation 格式化。看得懂结果。

---

150 行，一个完整能跑的 Code Agent。

---

给你留个思考题。这 150 行，如果用 LangChain 的 create_react_agent 写，大概 5 行就够。

---

那它帮你省掉了什么？又偷偷加了什么？

---

下一课，我们把同样的任务用 LangChain 跑一遍，一行一行拆开看。你会发现，框架的 system prompt 比我们手写的长 30 倍，token 消耗高 31 倍，干的活却一样。这就是抽象的代价。

---

代码在 GitHub 仓库 lesson1/code 目录下，v1 到 v4 四个文件，照着从头敲一遍就懂了。下期见。
