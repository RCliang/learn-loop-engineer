"""第一课 · 版本 4（最终版）：加上 Observation 格式化 —— 完整的 Agent。

关键变化：
1. 工具结果不再是原始字符串，而是经过格式化后更容易被 LLM 理解
2. 错误信息有统一前缀，LLM 能一眼看出什么失败了
3. 加上 token 统计和结构化日志，方便复盘

这就是一个完整的、可运行的 Agent 了。整个核心不到 150 行。
回顾一下我们从 v1 到 v4 逐步加入的 4 个组件：

  v1: LLM 调用循环（能想）
  v2: + 工具定义与执行（能做）
  v3: + Evaluator（会停）
  v4: + Observation 格式化（看得懂）

运行：python v4_final.py
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
    {
        "type": "function",
        "function": {
            "name": "file_read",
            "description": "读取工作目录中的文件内容",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "文件相对路径"},
                },
                "required": ["path"],
            },
        },
    },
]

# ---------- 工具执行器（永远不抛异常）----------
def execute_tool(name: str, args: dict) -> dict:
    """执行工具，返回结构化 dict。约定：ok=True 表示成功。"""
    if name == "bash_exec":
        try:
            proc = subprocess.run(
                args["command"], shell=True, cwd=str(SANDBOX),
                capture_output=True, text=True, timeout=30,
            )
            return {"ok": proc.returncode == 0, "exit_code": proc.returncode,
                    "stdout": proc.stdout, "stderr": proc.stderr}
        except subprocess.TimeoutExpired:
            return {"ok": False, "error": "TimeoutExpired", "message": "命令超时(30s)"}
    elif name == "file_write":
        try:
            p = SANDBOX / args["path"]
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(args["content"], encoding="utf-8")
            return {"ok": True, "path": args["path"], "bytes": len(args["content"])}
        except Exception as e:
            return {"ok": False, "error": type(e).__name__, "message": str(e)}
    elif name == "file_read":
        try:
            p = SANDBOX / args["path"]
            if not p.exists():
                return {"ok": False, "error": "FileNotFound", "message": f"文件不存在: {args['path']}"}
            content = p.read_text(encoding="utf-8")
            return {"ok": True, "path": args["path"], "content": content}
        except Exception as e:
            return {"ok": False, "error": type(e).__name__, "message": str(e)}
    return {"ok": False, "error": "UnknownTool", "message": f"未知工具: {name}"}


# ---------- Observation 格式化器 ----------
def format_observation(tool_name: str, result: dict) -> str:
    """把结构化的工具结果转成 LLM 容易理解的文本。"""
    if not result.get("ok"):
        return f"[错误] {tool_name} 失败: {result.get('message', '未知错误')}"

    if tool_name == "bash_exec":
        parts = [f"退出代码: {result['exit_code']}"]
        if result.get("stdout"):
            parts.append(f"输出:\n{result['stdout']}")
        if result.get("stderr"):
            parts.append(f"错误输出:\n{result['stderr']}")
        return "\n".join(parts)
    elif tool_name == "file_write":
        return f"✓ 已写入 {result['bytes']} 字节到 {result['path']}"
    elif tool_name == "file_read":
        return f"文件内容 ({result['path']}):\n{result['content']}"
    return json.dumps(result, ensure_ascii=False)


# ---------- Evaluator ----------
class Evaluator:
    def __init__(self, max_turns: int = 10):
        self.max_turns = max_turns
        self._action_hashes: list[str] = []

    def should_stop(self, turn: int, last_action: dict | None) -> tuple[bool, str]:
        if turn >= self.max_turns:
            return True, "max_turns"
        if last_action:
            h = hashlib.md5(json.dumps(last_action, sort_keys=True).encode()).hexdigest()
            if self._action_hashes.count(h) >= 2:
                return True, "loop_detected"
            self._action_hashes.append(h)
        return False, ""


# ---------- 核心循环（完整版）----------
SYSTEM_PROMPT = """你是一个 Code Agent。你可以调用工具来完成任务。
策略（ReAct）：
1. 思考任务下一步该做什么
2. 调用一个或多个工具
3. 观察工具结果
4. 重复直至任务完成，然后给出最终答案（不再调用任何工具）

文件路径请使用相对路径，如 hello.py。"""

def run_agent(user_task: str, max_turns: int = 10) -> dict:
    """运行 Agent，返回运行统计。"""
    messages = [{"role": "user", "content": user_task}]
    evaluator = Evaluator(max_turns=max_turns)
    stats = {"turns": 0, "tool_calls": 0, "input_tokens": 0, "output_tokens": 0}

    for turn in range(max_turns):
        stats["turns"] = turn + 1
        print(f"\n{'='*50}")
        print(f"  Turn {turn + 1}")
        print(f"{'='*50}")

        # ① 调 LLM
        resp = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "system", "content": SYSTEM_PROMPT}] + messages,
            tools=TOOLS,
        )
        # 统计 token
        if resp.usage:
            stats["input_tokens"] += resp.usage.prompt_tokens
            stats["output_tokens"] += resp.usage.completion_tokens

        msg = resp.choices[0].message
        text = msg.content or ""
        if text:
            print(f"\n💭 思考: {text[:300]}")

        # ② 没有工具调用 → 任务完成
        if not msg.tool_calls:
            print(f"\n{'='*50}")
            print(f"  ✅ 任务完成")
            print(f"{'='*50}")
            print(f"\n最终回答: {text[:500]}")
            stats["success"] = True
            stats["stop_reason"] = "task_complete"
            _print_stats(stats)
            return stats

        # ③ 追加 assistant 消息
        messages.append(msg.model_dump())

        # ④ 执行工具 + 格式化观察结果
        last_action = None
        for tc in msg.tool_calls:
            name = tc.function.name
            args = json.loads(tc.function.arguments)
            stats["tool_calls"] += 1
            print(f"\n🔧 工具调用: {name}")
            print(f"   参数: {json.dumps(args, ensure_ascii=False)[:150]}")

            result = execute_tool(name, args)
            observation = format_observation(name, result)
            print(f"   结果: {observation[:200]}")

            messages.append({
                "role": "tool",
                "tool_call_id": tc.id,
                "content": observation,
            })
            last_action = {"name": name, "args": args}

        # ⑤ Evaluator 检查
        should_stop, reason = evaluator.should_stop(turn + 1, last_action)
        if should_stop:
            print(f"\n⚠️  Evaluator 终止: {reason}")
            stats["success"] = False
            stats["stop_reason"] = reason
            _print_stats(stats)
            return stats

    stats["success"] = False
    stats["stop_reason"] = "max_turns"
    _print_stats(stats)
    return stats


def _print_stats(stats: dict):
    print(f"\n{'─'*40}")
    print(f"  📊 运行统计")
    print(f"{'─'*40}")
    print(f"  轮次: {stats['turns']}")
    print(f"  工具调用: {stats['tool_calls']} 次")
    print(f"  Token: {stats['input_tokens']} in / {stats['output_tokens']} out")
    print(f"  结果: {'✅ 成功' if stats.get('success') else '❌ 未完成'}")
    print(f"  终止原因: {stats.get('stop_reason', 'unknown')}")


if __name__ == "__main__":
    run_agent("请创建一个 hello.py 文件，内容打印 'hello world'，然后运行它。")
