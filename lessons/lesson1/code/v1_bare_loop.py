"""第一课 · 版本 1：最简 Agent 骨架 —— 只有 LLM 调用 + 硬上限终止。

这是最小的"Agent"：一个 for 循环里反复调 LLM，直到达到轮次上限。
此时 Agent 能"想"，但还不能"做"——没有工具，只能输出文字。

运行：python v1_bare_loop.py
"""
import os
from openai import OpenAI

# ---------- 配置 ----------
client = OpenAI(
    base_url=os.getenv("LLM_BASE_URL", "https://api.openai.com/v1"),
    api_key=os.getenv("LLM_API_KEY", "sk-xxx"),
)
MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")

# ---------- 核心循环 ----------
SYSTEM_PROMPT = "你是一个 Code Agent。请根据用户需求完成任务。"

def run_agent(user_task: str, max_turns: int = 5):
    """最简 agent：循环调 LLM，直到用完轮次。"""
    messages = [{"role": "user", "content": user_task}]

    for turn in range(max_turns):
        print(f"\n── Turn {turn + 1} ──")

        resp = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "system", "content": SYSTEM_PROMPT}] + messages,
        )
        reply = resp.choices[0].message.content or ""
        print(f"LLM: {reply[:200]}")

        messages.append({"role": "assistant", "content": reply})

        # 此时没有任何停止判断——跑满 max_turns 就结束
        # 问题：LLM 只能说话，不能执行任何操作

    print("\n[结束] 达到最大轮次")
    return messages


if __name__ == "__main__":
    run_agent("请创建一个 hello.py 文件，内容打印 'hello world'，然后运行它。")
