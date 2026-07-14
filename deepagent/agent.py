"""deepagent Code Agent —— LangChain deepagents 库的极薄包装。

设计：
- 只用 deepagents 的 9 个内置工具（不注入 handroll 的共享工具），
  让框架按其原生工具表面工作，与 handroll 形成纯框架 vs 纯手写的对比
- 共享 REACT 风格 system prompt（与 handroll.agent 等价语义）
- 默认启用 deepagents 的 write_todos / planning，作为额外 tool_call 记录
- 通过 agent.stream(stream_mode="updates") 事件流重构 RunLog

【和 DeepAgent 的对比】
- 这里的 `_ingest_event` 50 行做的事，handroll 是在 loop.py 里直接累加。
- 关键观察：DeepAgent 通过事件流重构状态，handroll 直接在循环中更新。

【工具表面变更说明】
此前本路径注入 handroll 的 3 个共享工具（bash_exec / file_read / file_write），
与 deepagents 内置工具形成 3 对命名冲突（详见 docs/findings/2026-07-07-...md）。
现在改为 tools=[]，让 deepagents 只暴露其 9 个内置工具，得到一份"纯框架"基线。
"""
from __future__ import annotations

import time

from rich import print as rprint

from langchain_openai import ChatOpenAI

try:
    from deepagents import create_deep_agent
except ImportError as e:
    raise ImportError(
        "deepagents 未安装。请确认 pyproject.toml 中包含 'deepagents>=0.0.5' "
        "并执行 pip install -e '.[dev]'"
    ) from e

try:
    from deepagents.backends import LocalShellBackend
except ImportError as e:
    raise ImportError(
        "LocalShellBackend 不可用，请确认 deepagents 版本支持 backends.local_shell"
    ) from e

from shared.utils.config import load_env
from shared.utils.sandbox import SANDBOX_DIR
from shared.tracker.run_logger import RunLog
from tasks.task_base import Task

from langchain_core.callbacks import BaseCallbackHandler


class _SystemPromptCapture(BaseCallbackHandler):
    """拦截模型调用，捕获 deepagents 运行时拼接的完整 system prompt。
    只在第一次 on_chat_model_start 时捕获（后续调用的 prompt 相同）。"""

    def __init__(self) -> None:
        self.captured: str = ""

    def on_chat_model_start(self, serialized, messages, **kwargs):
        if self.captured:
            return  # 只捕第一次
        for msg_list in messages:
            for msg in msg_list:
                if getattr(msg, "type", "") == "system":
                    content = msg.content
                    if isinstance(content, list):
                        # SystemMessage with content_blocks
                        texts = [
                            b.get("text", "")
                            for b in content
                            if isinstance(b, dict) and b.get("type") == "text"
                        ]
                        self.captured = "\n".join(texts)
                    else:
                        self.captured = str(content)
                    return

# 方案 A（v2）：虚拟路径模式。
#
# deepagents 的 FilesystemMiddleware 在中间件层调 validate_path()，
# 硬性拒绝所有 Windows 绝对路径（正则 ^[a-zA-Z]:）。所以不能给模型
# 看 Windows 绝对路径，否则 write_file / ls / read_file 全部报错。
#
# 正确做法：用 virtual_mode=True 的 LocalShellBackend，把 sandbox 目录
# 作为虚拟根。模型看到的文件路径是 /hello.py、/foo/bar.py 等 POSIX
# 虚拟路径，框架内部映射到 {root_dir}/hello.py = sandbox/hello.py。
# execute 工具的 cwd 同样是 sandbox，所以 shell 命令也用相对路径。
#
# 两路 prompt 保持完全一致（单一变量纪律）。

DEEP_AGENT_SYSTEM_PROMPT = """你是一个 Code Agent。你可以调用工具来完成任务。
策略（ReAct）：
1. 思考任务下一步该做什么
2. 如有必要，调用一个或多个工具
3. 观察工具结果
4. 重复直至任务完成，然后给出最终答案

所有文件操作都针对你的工作目录（虚拟根）。
文件路径请使用 POSIX 虚拟路径，以 / 开头，例如：
- /hello.py 表示工作目录下的 hello.py
- /scripts/run.py 表示工作目录下 scripts/run.py

执行 shell 命令时，当前工作目录已经是工作目录，直接用文件名即可（如 python hello.py）。"""


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
        tools=[],  # 只用 deepagents 的 9 个内置工具，不注入共享工具
        system_prompt=DEEP_AGENT_SYSTEM_PROMPT,
        # LocalShellBackend = FilesystemBackend + execute 工具（实现 SandboxBackendProtocol）。
        # 之前用 FilesystemBackend：文件能落盘，但 execute 工具一调就返回错误
        # （FilesystemBackend 不实现 SandboxBackendProtocol，见 deepagents graph.py:290-292），
        # 模型只能委派 task subagent 间接跑命令。换 LocalShellBackend 后，
        # execute 通过 subprocess.run(shell=True, cwd=SANDBOX_DIR) 直接在主机执行，
        # 模型可以自己跑 `python hello.py`，不必再委派 subagent。详见
        # docs/findings/2026-07-09-deepagent-backend-statebackend.md 和
        # docs/findings/2026-07-09-deepagent-localshell-validate-path.md（后者记录了
        # LocalShellBackend 在 --agent both 模式下因 validate_path 拒绝 Windows 绝对路径
        # 而非确定性失败的问题）。
        backend=LocalShellBackend(
            root_dir=str(SANDBOX_DIR),
            virtual_mode=True,  # 虚拟根模式：模型看到 /hello.py，框架映射到 sandbox/hello.py
            inherit_env=True,   # 让 PATH 上的 python 等命令对 agent 可见
        ),
    )


def _ingest_event(
    event: dict,
    run_log: RunLog,
    in_tok: int,
    out_tok: int,
    final_text: str,
) -> tuple[int, int, str, int]:
    """从 LangGraph stream_mode='updates' 事件中提取信息。
    返回更新后的 (in_tok, out_tok, final_text, llm_calls)。
    llm_calls = AIMessage 数量，用于与 handroll 的 loop_turns 对齐口径。"""
    llm_calls = 0
    for _node_name, state in event.items():
        messages = state.get("messages", []) if isinstance(state, dict) else []
        for msg in messages:
            msg_type = getattr(msg, "type", "") or msg.__class__.__name__
            if msg_type == "ai":
                # AIMessage: 提取 content / tool_calls / usage
                llm_calls += 1
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
                    tc_id = tc.get("id", "")
                    # 先记一条"待确认"记录；ToolMessage 到达时用真实结果回写
                    run_log.tool_calls.append({
                        "name": name,
                        "input": args,
                        "ok": True,  # 估计值，待 ToolMessage 校正
                        "duration_s": 0.0,
                        "exit_code": None,
                        "_tool_call_id": tc_id,
                        "_pending": True,
                    })
                    rprint(f"[yellow]→ deepagent tool: {name}({args})[/yellow]")
            elif msg_type == "tool":
                # ToolMessage: 工具真实执行结果（status / content）
                # 回写之前 AIMessage 阶段记录的"待确认"条目
                content = getattr(msg, "content", "") or ""
                tc_id = getattr(msg, "tool_call_id", None) or ""
                status = getattr(msg, "status", "success")  # "success" | "error"
                is_ok = (status != "error")
                # 从尾部向前找匹配的 pending 记录
                for recorded in reversed(run_log.tool_calls):
                    if recorded.get("_tool_call_id") == tc_id and recorded.get("_pending"):
                        recorded["ok"] = is_ok
                        recorded["_pending"] = False
                        recorded["output_preview"] = content[:500]
                        if not is_ok:
                            rprint(f"[red]✗ tool failed: {recorded['name']} — {content[:120]}[/red]")
                        break
    return in_tok, out_tok, final_text, llm_calls


def _cleanup_internal_fields(run_log: RunLog) -> None:
    """清除 tool_calls 中的内部追踪字段（_tool_call_id / _pending），
    这些字段仅用于 AIMessage → ToolMessage 的关联匹配，不应出现在最终 JSON 中。"""
    _INTERNAL_KEYS = ("_tool_call_id", "_pending")
    for tc in run_log.tool_calls:
        for key in _INTERNAL_KEYS:
            tc.pop(key, None)


def run(task: Task) -> RunLog:
    run_log = RunLog(
        task_id=task.id,
        agent_type="deepagent",
        planner_strategy="react",
    )
    run_log.notes.append("loop_turns 与 handroll 对齐口径：LLM 调用次数（AIMessage 数量）")
    run_log.notes.append("write_todos 调用计入了 tool_calls（如发生）")

    prompt_capture = _SystemPromptCapture()
    agent = build_agent()
    start = time.time()
    in_tok_total = 0
    out_tok_total = 0
    final_text = ""
    llm_call_count = 0  # 与 handroll loop_turns 对齐：LLM 调用次数

    try:
        for event in agent.stream(
            {"messages": [{"role": "user", "content": task.prompt}]},
            stream_mode="updates",
            config={"callbacks": [prompt_capture]},
        ):
            in_tok_total, out_tok_total, final_text, llm_calls = _ingest_event(
                event, run_log, in_tok_total, out_tok_total, final_text
            )
            llm_call_count += llm_calls
    except Exception as e:
        run_log.notes.append(f"runtime_error: {type(e).__name__}: {e}")
        run_log.system_prompt = prompt_capture.captured
        _cleanup_internal_fields(run_log)
        run_log.finish(success=False, stop_reason="error", final_answer=final_text)
        run_log.loop_turns = llm_call_count
        run_log.total_input_tokens = in_tok_total
        run_log.total_output_tokens = out_tok_total
        run_log.duration_s = round(time.time() - start, 3)
        run_log.save()
        return run_log

    run_log.system_prompt = prompt_capture.captured
    run_log.loop_turns = llm_call_count
    run_log.total_input_tokens = in_tok_total
    run_log.total_output_tokens = out_tok_total
    if in_tok_total == 0:
        run_log.notes.append("token_usage_unavailable（模型未返回 usage）")
    run_log.duration_s = round(time.time() - start, 3)
    _cleanup_internal_fields(run_log)
    run_log.finish(
        success=task.success_criterion(final_text),
        stop_reason="task_complete",
        final_answer=final_text,
    )
    run_log.save()
    return run_log
