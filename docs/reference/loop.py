"""
手写 Agent Loop — 核心实现
【学习重点】这是整个实验的核心文件。
  它把 Planner / Tool Use / Executor / Evaluator / Observation
  这五个组件手动串联成一个完整的 agent loop。

Loop 流程：
  ┌─────────────────────────────────────────────┐
  │  1. 构建 messages（Planner）                 │
  │  2. 调用 LLM（Tool Use）                     │
  │  3. 若 LLM 请求工具调用 → Executor 执行      │
  │  4. 格式化结果 → Observation                 │
  │  5. Evaluator 判断是否终止                   │
  │  6. 追加结果到 messages，进入下一轮          │
  └─────────────────────────────────────────────┘
"""
from __future__ import annotations
import anthropic
from rich import print as rprint

from shared.tools.schemas import ALL_TOOLS
from shared.utils.llm_client import chat
from shared.tracker.run_logger import RunLog
from handroll.executor.executor import execute_tool
from handroll.evaluator.evaluator import Evaluator
from handroll.observation.formatter import format_observation


def run_loop(
    task: str,
    system_prompt: str,
    run_log: RunLog,
    max_turns: int = 15,
) -> str:
    """
    执行一次完整的 agent loop。

    Args:
        task: 自然语言任务描述
        system_prompt: 来自 Planner 的系统提示
        run_log: 运行日志对象（由调用方传入并最终保存）
        max_turns: 最大 loop 轮次

    Returns:
        final_answer: agent 的最终回答
    """
    evaluator = Evaluator(max_turns=max_turns)
    messages: list[dict] = [{"role": "user", "content": task}]
    final_answer = ""

    for turn in range(max_turns):
        run_log.loop_turns = turn + 1
        rprint(f"\n[bold cyan]── Turn {turn + 1} ──[/bold cyan]")

        # ① 调用 LLM
        resp, in_tok, out_tok = chat(
            messages=messages,
            system=system_prompt,
            tools=ALL_TOOLS,
        )
        run_log.total_input_tokens += in_tok
        run_log.total_output_tokens += out_tok

        # ② 解析响应：收集文本和工具调用
        text_parts: list[str] = []
        tool_use_blocks: list[anthropic.types.ToolUseBlock] = []

        for block in resp.content:
            if block.type == "text":
                text_parts.append(block.text)
                rprint(f"[dim]{block.text[:300]}[/dim]")
            elif block.type == "tool_use":
                tool_use_blocks.append(block)

        last_text = "\n".join(text_parts)

        # ③ 若无工具调用，说明 LLM 认为任务完成
        if not tool_use_blocks:
            final_answer = last_text
            run_log.finish(success=True, stop_reason="task_complete", final_answer=final_answer)
            rprint("[green]✓ 任务完成（LLM 主动结束）[/green]")
            return final_answer

        # ④ 执行所有工具调用，收集 Observation
        # 先把 LLM 回复追加到 messages（含 tool_use blocks）
        messages.append({"role": "assistant", "content": resp.content})

        tool_results = []
        last_action = None
        for block in tool_use_blocks:
            rprint(f"[yellow]→ 工具调用：{block.name}({block.input})[/yellow]")
            obs = execute_tool(block.name, block.input, run_log)
            formatted_obs = format_observation(block.name, block.input, obs)
            rprint(f"[dim]{formatted_obs[:200]}[/dim]")
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": formatted_obs,
            })
            last_action = {"name": block.name, "input": block.input}

        # ⑤ 把工具结果作为 user 消息追加
        messages.append({"role": "user", "content": tool_results})

        # ⑥ Evaluator 判断是否终止
        should_stop, stop_reason = evaluator.should_stop(
            task=task,
            last_response=last_text,
            current_turn=turn + 1,
            last_action=last_action,
        )
        if should_stop:
            final_answer = last_text or "（无文本输出）"
            run_log.finish(
                success=(stop_reason == "task_complete"),
                stop_reason=stop_reason,
                final_answer=final_answer,
            )
            rprint(f"[{'green' if stop_reason == 'task_complete' else 'red'}]"
                   f"停止原因：{stop_reason}[/]")
            return final_answer

    # 超出最大轮次（理论上不会到这里，Evaluator 会先拦截）
    run_log.finish(success=False, stop_reason="max_turns", final_answer="")
    return ""
