"""Evaluator —— 判断 agent loop 何时终止。

三策略组合（按优先级）：
1. max_turns      硬上限兜底
2. loop_detect    同一 action hash 出现 ≥3 次即停止
3. self_critique  LLM 自评（实际 Week 1 几乎不触发，因无 tool_use 时已在 loop 内停止）

【和 DeepAgent 的对比】
- DeepAgent 没有内置 Evaluator；终止全靠 LLM 自己说"完成"。
- 关键观察：这里的三层终止策略(max/loop/self_critique)提供更强保障。
"""
from __future__ import annotations

import hashlib
from typing import Any

from shared.utils.llm_client import chat

SELF_CRITIQUE_PROMPT = """你是一个任务完成度评估员。

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
        # 策略 1：硬上限
        if current_turn >= self.max_turns:
            return True, "max_turns"

        # 策略 2：死循环检测
        if last_action:
            h = hashlib.md5(str(last_action).encode()).hexdigest()
            if self._action_hashes.count(h) >= 2:
                return True, "loop_detected"
            self._action_hashes.append(h)

        # 策略 3：self-critique
        prompt = SELF_CRITIQUE_PROMPT.format(task=task, last_response=last_response)
        resp, _, _ = chat(
            messages=[{"role": "user", "content": prompt}],
            system="你是一个评估员。",
            tools=[],
            max_tokens=128,
        )
        verdict = self._extract_text(resp).strip()
        if verdict.startswith("COMPLETE"):
            return True, "task_complete"
        return False, ""

    @staticmethod
    def _extract_text(resp: Any) -> str:
        # OpenAI SDK: resp.choices[0].message.content
        try:
            return resp.choices[0].message.content or ""
        except (AttributeError, IndexError):
            return ""
