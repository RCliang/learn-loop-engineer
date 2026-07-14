"""第一课 · 版本 3：加上 Evaluator —— Agent 学会了自我保护。

关键变化：
1. 死循环检测：如果 Agent 连续 3 次做完全相同的操作，强制停止
2. max_turns 兜底：无论如何不会无限循环
3. （可选）self-critique：让另一个 LLM 调用判断"任务做完了吗"

为什么需要 Evaluator？
- LLM 可能陷入死循环（反复执行相同命令）
- LLM 可能永远不说"完成"（一直尝试新操作）
- 没有刹车的 Agent 会烧光你的 token

运行：python v3_with_evaluator.py
"""
import hashlib
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

# ---------- 工具定义 ----------
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


# ---------- Evaluator：三层刹车 ----------
class Evaluator:
    def __init__(self, max_turns: int = 10):
        self.max_turns = max_turns
        self._action_hashes: list[str] = []

    def should_stop(self, turn: int, last_action: dict | None) -> tuple[bool, str]:
        """返回 (是否停止, 原因)"""
        # 刹车 1：硬上限
        if turn >= self.max_turns:
            return True, "max_turns"

        # 刹车 2：死循环检测（同一 action 出现 ≥3 次）
        if last_action:
            h = hashlib.md5(json.dumps(last_action, sort_keys=True).encode()).hexdigest()
            if self._action_hashes.count(h) >= 2:
                return True, "loop_detected"
            self._action_hashes.append(h)

        return False, ""


# ---------- 核心循环 ----------
SYSTEM_PROMPT = """你是一个 Code Agent。你可以调用工具来完成任务。
策略：思考 → 调用工具 → 观察结果 → 重复，直到任务完成后给出最终答案（不再调用工具）。
文件路径请使用相对路径，如 hello.py。"""

def run_agent(user_task: str, max_turns: int = 10):
    messages = [{"role": "user", "content": user_task}]
    evaluator = Evaluator(max_turns=max_turns)

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
            print("\n✓ 任务完成（LLM 主动结束）")
            return text

        # 追加 assistant 消息
        messages.append(msg.model_dump())

        # 执行工具
        last_action = None
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
            last_action = {"name": name, "args": args}

        # Evaluator 检查
        should_stop, reason = evaluator.should_stop(turn + 1, last_action)
        if should_stop:
            print(f"\n⚠ Evaluator 终止: {reason}")
            return None

    print("\n[结束] 达到最大轮次")
    return None


if __name__ == "__main__":
    run_agent("请创建一个 hello.py 文件，内容打印 'hello world'，然后运行它。")
