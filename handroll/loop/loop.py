"""核心 agent loop —— 6 步串联 Planner/ToolUse/Executor/Observation/Evaluator。

Loop 流程：
  ① 调 LLM（Tool Use 隐式发生）
  ② 解析：text blocks + tool_calls
  ③ 无 tool_calls → 任务完成
  ④ assistant 消息追加到 messages
  ⑤ 执行所有工具、格式化、作为 user 消息追加
  ⑥ Evaluator 判断是否继续

设计要点：
- run_log 贯穿全程，记录每个 llm_call / tool_call 事件
- 工具调用永远不抛异常（Executor 内部捕获）
- max_turns 由 Evaluator 兜底，loop 不会无限运行

【和 DeepAgent 的对比】（Task 18 补全）
"""
from __future__ import annotations

import json
from typing import Any

from rich import print as rprint

from shared.tools.schemas import ALL_TOOLS
from shared.tracker.run_logger import RunLog
from shared.utils.llm_client import chat
from handroll.executor.executor import execute_tool
from handroll.evaluator.evaluator import Evaluator
from handroll.observation.formatter import format_observation


def parse_response(resp: Any) -> tuple[list[str], list[dict]]:
    """把 OpenAI response 拆成 (text_parts, tool_calls)。
    tool_calls 元素结构：{id, name, input(dict)}。"""
    msg = resp.choices[0].message
    text = msg.content or ""
    text_parts = [text] if text else []
    tool_calls = []
    for tc in (msg.tool_calls or []):
        args = tc.function.arguments
        try:
            input_dict = json.loads(args) if isinstance(args, str) else dict(args)
        except json.JSONDecodeError:
            input_dict = {"_raw": args}
        tool_calls.append({
            "id": tc.id,
            "name": tc.function.name,
            "input": input_dict,
        })
    return text_parts, tool_calls


def run_loop(task, system_prompt: str, run_log: RunLog, max_turns: int = 15) -> RunLog:
    evaluator = Evaluator(max_turns=max_turns)
    messages: list[dict] = [{"role": "user", "content": task.prompt}]

    for turn in range(max_turns):
        run_log.loop_turns = turn + 1
        rprint(f"\n[bold cyan]── Turn {turn + 1} ──[/bold cyan]")

        # ① 调 LLM
        resp, in_tok, out_tok = chat(
            messages=messages,
            system=system_prompt,
            tools=ALL_TOOLS,
        )
        run_log.total_input_tokens += in_tok
        run_log.total_output_tokens += out_tok
        run_log.log_event(turn + 1, "llm_call", input_tokens=in_tok, output_tokens=out_tok)

        # ② 解析
        text_parts, tool_calls = parse_response(resp)
        for tp in text_parts:
            rprint(f"[dim]{tp[:300]}[/dim]")

        # ③ 无 tool_use → 任务完成
        if not tool_calls:
            final = "\n".join(text_parts)
            run_log.finish(success=True, stop_reason="task_complete", final_answer=final)
            rprint("[green]✓ 任务完成（LLM 主动结束）[/green]")
            return run_log

        # ④ 追加 assistant 消息（含原始 tool_calls 结构）
        assistant_msg = {"role": "assistant", "content": text_parts[0] if text_parts else ""}
        assistant_msg["tool_calls"] = [
            {
                "id": tc["id"],
                "type": "function",
                "function": {
                    "name": tc["name"],
                    "arguments": json.dumps(tc["input"], ensure_ascii=False),
                },
            }
            for tc in tool_calls
        ]
        messages.append(assistant_msg)

        # ⑤ 执行所有工具、格式化、作为 user 消息追加
        tool_results_for_api = []
        last_action = None
        for tc in tool_calls:
            rprint(f"[yellow]→ 工具调用：{tc['name']}({tc['input']})[/yellow]")
            obs = execute_tool(tc["name"], tc["input"], run_log)
            formatted = format_observation(tc["name"], tc["input"], obs)
            rprint(f"[dim]{formatted[:200]}[/dim]")
            tool_results_for_api.append({
                "role": "tool",
                "tool_call_id": tc["id"],
                "content": formatted,
            })
            last_action = {"name": tc["name"], "input": tc["input"]}
        messages.append({"role": "user", "content": tool_results_for_api})

        # ⑥ Evaluator
        should_stop, reason = evaluator.should_stop(
            task=task.prompt,
            last_response="\n".join(text_parts),
            current_turn=turn + 1,
            last_action=last_action,
        )
        if should_stop:
            final = "\n".join(text_parts) or "(无文本输出)"
            run_log.finish(
                success=(reason == "task_complete"),
                stop_reason=reason,
                final_answer=final,
            )
            rprint(f"[{'green' if reason == 'task_complete' else 'red'}]停止：{reason}[/]")
            return run_log

    run_log.finish(success=False, stop_reason="max_turns", final_answer="")
    return run_log
