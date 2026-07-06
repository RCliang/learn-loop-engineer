"""
Evaluator — 判断 agent loop 是否应该终止
【学习重点】终止条件是 loop 工程中最容易被忽视的组件。
  - self_critique: 让 LLM 自判断任务是否完成
  - max_turns: 硬上限保险丝
  - loop_detection: 检测重复 action，避免死循环
"""
import hashlib
from shared.utils.llm_client import chat

SELF_CRITIQUE_PROMPT = """
你是一个任务完成度评估员。

原始任务：
{task}

当前 agent 的最新回复：
{last_response}

请判断：这个任务是否已经完成？

回答格式（只能回答以下两种之一）：
- COMPLETE: <简短说明完成原因>
- INCOMPLETE: <说明还缺什么>
""".strip()


class Evaluator:
    """
    组合三种终止判断策略：
    1. self_critique  — LLM 自评（软判断，可能误判）
    2. max_turns      — 硬上限（兜底保险丝）
    3. loop_detection — 重复 action 检测
    """

    def __init__(self, max_turns: int = 15):
        self.max_turns = max_turns
        self._action_hashes: list[str] = []

    def should_stop(
        self,
        task: str,
        last_response: str,
        current_turn: int,
        last_action: dict | None = None,
    ) -> tuple[bool, str]:
        """
        返回 (should_stop, stop_reason)
        stop_reason: "task_complete" | "max_turns" | "loop_detected"
        """
        # --- 策略 1：硬上限 ---
        if current_turn >= self.max_turns:
            return True, "max_turns"

        # --- 策略 2：死循环检测 ---
        if last_action:
            h = hashlib.md5(str(last_action).encode()).hexdigest()
            if self._action_hashes.count(h) >= 2:
                return True, "loop_detected"
            self._action_hashes.append(h)

        # --- 策略 3：self-critique（LLM 自判断） ---
        prompt = SELF_CRITIQUE_PROMPT.format(task=task, last_response=last_response)
        resp, _, _ = chat(messages=[{"role": "user", "content": prompt}], max_tokens=256)
        verdict = resp.content[0].text.strip()
        if verdict.startswith("COMPLETE"):
            return True, "task_complete"

        return False, ""
