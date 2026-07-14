"""第一课 · 版本 2：给 Agent 装上工具 —— 能做事了。

关键变化：
1. 定义了 tools schema，告诉 LLM "你有哪些工具可以用"
2. 解析 LLM 返回的 tool_calls
3. 用 executor 执行工具，把结果回传给 LLM
4. 当 LLM 不再调用工具时，认为任务完成

这就是 ReAct 模式的核心：思考 → 行动 → 观察 → 重复。

运行：python v2_with_tools.py
"""
import json
import os
import subprocess
from pathlib import Path

from openai import OpenAI

# ---------- 配置 ----------
client = OpenAI(
    base_url=os.getenv("LLM_BASE_URL", "https://api.openai.com/v1"),
    api_key=os.getenv("LLM_API_KEY", "sk-xxx"),
)
MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
SANDBOX = Path("./sandbox")
SANDBOX.mkdir(exist_ok=True)

# ---------- 工具定义（告诉 LLM 它能做什么）----------
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "bash_exec",
            "description": "在工作目录中执行 shell 命令",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "要执行的命令"}
                },
                "required": ["command"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "file_write",
            "description": "在工作目录中创建或覆盖文件",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "文件相对路径"},
                    "content": {"type": "string", "description": "文件内容"},
                },
                "required": ["path", "content"],
            },
        },
    },
]

# ---------- 工具执行器 ----------
def execute_tool(name: str, args: dict) -> str:
    """执行工具，返回结果字符串。永远不抛异常。"""
    if name == "bash_exec":
        try:
            proc = subprocess.run(
                args["command"], shell=True, cwd=str(SANDBOX),
                capture_output=True, text=True, timeout=30,
            )
            return f"exit_code={proc.returncode}\nstdout: {proc.stdout}\nstderr: {proc.stderr}"
        except subprocess.TimeoutExpired:
            return "错误：命令超时(30s)"
    elif name == "file_write":
        try:
            p = SANDBOX / args["path"]
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(args["content"], encoding="utf-8")
            return f"已写入 {len(args['content'])} 字节到 {args['path']}"
        except Exception as e:
            return f"写入失败：{e}"
    return f"未知工具：{name}"


# ---------- 核心循环 ----------
SYSTEM_PROMPT = """你是一个 Code Agent。你可以调用工具来完成任务。
策略：思考 → 调用工具 → 观察结果 → 重复，直到任务完成后给出最终答案（不再调用工具）。
文件路径请使用相对路径，如 hello.py。"""

def run_agent(user_task: str, max_turns: int = 10):
    messages = [{"role": "user", "content": user_task}]

    for turn in range(max_turns):
        print(f"\n── Turn {turn + 1} ──")

        resp = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "system", "content": SYSTEM_PROMPT}] + messages,
            tools=TOOLS,
        )
        msg = resp.choices[0].message
        text = msg.content or ""
        if text:
            print(f"LLM: {text[:200]}")

        # 没有工具调用 → 任务完成
        if not msg.tool_calls:
            print("\n✓ 任务完成（LLM 不再调用工具）")
            return text

        # 追加 assistant 消息（必须包含 tool_calls 结构）
        messages.append(msg.model_dump())

        # 执行每个工具调用，把结果作为 tool 消息回传
        for tc in msg.tool_calls:
            name = tc.function.name
            args = json.loads(tc.function.arguments)
            print(f"  → 工具: {name}({args})")

            result = execute_tool(name, args)
            print(f"  ← 结果: {result[:150]}")

            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": result,
            })

    print("\n[结束] 达到最大轮次")
    return None


if __name__ == "__main__":
    run_agent("请创建一个 hello.py 文件，内容打印 'hello world'，然后运行它。")
