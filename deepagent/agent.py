"""deepagent Code Agent —— LangChain deepagents 库的极薄包装。

设计：
- 共享 handroll 路的工具（ALL_TOOLS_AS_CALLABLES）保证对比公平
- 共享 REACT 风格 system prompt（与 handroll.agent 等价语义）
- 默认启用 deepagents 的 write_todos / planning，作为额外 tool_call 记录
- 通过 agent.stream(stream_mode="updates") 事件流重构 RunLog

【和 DeepAgent 的对比】
- 这里的 `_ingest_event` 50 行做的事，handroll 是在 loop.py 里直接累加。
- 关键观察：DeepAgent 通过事件流重构状态，handroll 直接在循环中更新。
"""
from __future__ import annotations

import time
from typing import Any

from rich import print as rprint

from langchain_openai import ChatOpenAI

try:
    from deepagents import create_deep_agent
except ImportError as e:
    raise ImportError(
        "deepagents 未安装。请确认 pyproject.toml 中包含 'deepagents>=0.0.5' "
        "并执行 pip install -e '.[dev]'"
    ) from e

from shared.tools.schemas import ALL_TOOLS_AS_CALLABLES
from shared.utils.config import load_env
from shared.tracker.run_logger import RunLog
from tasks.task_base import Task

DEEP_AGENT_SYSTEM_PROMPT = """你是一个 Code Agent。你可以调用工具来完成任务。
策略（ReAct）：
1. 思考任务下一步该做什么
2. 如有必要，调用一个或多个工具
3. 观察工具结果
4. 重复直至任务完成，然后给出最终答案

所有文件操作被限制在当前工作目录（sandbox/）。"""


def build_agent():
    cfg = load_env()
    model = ChatOpenAI(
        model=cfg.LLM_MODEL,
        api_key=cfg.LLM_API_KEY,
        base_url=cfg.LLM_BASE_URL,
        temperature=0,
    )
    return create_deep_agent(
        model=model,
        tools=ALL_TOOLS_AS_CALLABLES,
        system_prompt=DEEP_AGENT_SYSTEM_PROMPT,
    )


def _ingest_event(
    event: dict,
    run_log: RunLog,
    in_tok: int,
    out_tok: int,
    final_text: str,
) -> tuple[int, int, str]:
    """从 LangGraph stream_mode='updates' 事件中提取信息。
    返回更新后的 (in_tok, out_tok, final_text)。"""
    for _node_name, state in event.items():
        messages = state.get("messages", []) if isinstance(state, dict) else []
        for msg in messages:
            msg_type = getattr(msg, "type", "") or msg.__class__.__name__
            if msg_type == "ai":
                # AIMessage: 提取 content / tool_calls / usage
                content = getattr(msg, "content", "") or ""
                if isinstance(content, str) and content.strip():
                    final_text = content
                usage = getattr(msg, "usage_metadata", None) or {}
                in_tok += usage.get("input_tokens", 0) or 0
                out_tok += usage.get("output_tokens", 0) or 0
                tool_calls = getattr(msg, "tool_calls", None) or []
                for tc in tool_calls:
                    name = tc.get("name", "<unknown>")
                    args = tc.get("args", {}) or {}
                    run_log.log_tool_call(name, args, {"ok": True, "duration_s": 0.0})
                    rprint(f"[yellow]→ deepagent tool: {name}({args})[/yellow]")
            elif msg_type == "tool":
                # ToolMessage: 工具结果。若 log_tool_call 时 ok=True 是估计值，这里可校正
                pass
    return in_tok, out_tok, final_text


def run(task: Task) -> RunLog:
    run_log = RunLog(
        task_id=task.id,
        agent_type="deepagent",
        planner_strategy="react",
    )
    run_log.notes.append("loop_turns 是 LangGraph 节点更新次数，非严格 LLM 调用次数")
    run_log.notes.append("write_todos 调用计入了 tool_calls（如发生）")

    agent = build_agent()
    start = time.time()
    in_tok_total = 0
    out_tok_total = 0
    final_text = ""
    turn_count = 0

    try:
        for event in agent.stream(
            {"messages": [{"role": "user", "content": task.prompt}]},
            stream_mode="updates",
        ):
            turn_count += 1
            in_tok_total, out_tok_total, final_text = _ingest_event(
                event, run_log, in_tok_total, out_tok_total, final_text
            )
    except Exception as e:
        run_log.notes.append(f"runtime_error: {type(e).__name__}: {e}")
        run_log.finish(success=False, stop_reason="error", final_answer=final_text)
        run_log.loop_turns = turn_count
        run_log.total_input_tokens = in_tok_total
        run_log.total_output_tokens = out_tok_total
        run_log.duration_s = round(time.time() - start, 3)
        run_log.save()
        return run_log

    run_log.loop_turns = turn_count
    run_log.total_input_tokens = in_tok_total
    run_log.total_output_tokens = out_tok_total
    if in_tok_total == 0:
        run_log.notes.append("token_usage_unavailable（模型未返回 usage）")
    run_log.duration_s = round(time.time() - start, 3)
    run_log.finish(
        success=task.success_criterion(final_text),
        stop_reason="task_complete",
        final_answer=final_text,
    )
    run_log.save()
    return run_log
