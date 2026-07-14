# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Purpose

This is **Loop Engineering Lab** — a comparative experiment that answers *"what does a framework handle for you, and what must you implement yourself?"* by implementing the same Code Agent twice:

- `handroll/` — manually written agent loop, every component explicit
- `deepagent/` — thin wrapper around the `deepagents` library (LangChain + LangGraph)

The two paths share the same task definitions, tool implementations, and `RunLog` output contract so results are directly comparable.

## Common Commands

```bash
# Install (editable, with dev deps)
pip install -e ".[dev]"

# Configure LLM (OpenAI-compatible endpoint)
cp .env.example .env   # then edit to fill LLM_BASE_URL / LLM_API_KEY / LLM_MODEL

# Run an agent on a task
python -m cli run --agent handroll  --task task_01_simple_script
python -m cli run --agent deepagent --task task_01_simple_script
python -m cli run --agent both      --task task_01_simple_script

# List available tasks
python -m cli tasks

# Tests (pytest, pythonpath="." is set in pyproject.toml)
pytest                              # all
pytest tests/test_loop.py           # one file
pytest tests/test_loop.py::test_xxx # single test

# Lint / format (ruff, line-length=100, target py311)
ruff check .
ruff format .
```

Run outputs land in `outputs/runs/<timestamp>_<agent>_<task>.json` (gitignored). The sandbox is wiped via `reset_sandbox()` before each `_run_one`.

## Architecture

### The 6-step loop (conceptual)

```
Planner → Tool Use → Executor → Observation → Evaluator → (back to Planner)
```

`handroll/loop/loop.py` implements this as six explicit numbered steps inside one `for turn in range(max_turns)` loop. `deepagent/agent.py` hides the same loop behind `agent.stream(stream_mode="updates")` and reconstructs state by ingesting events.

### The two paths and how they map

| Concern | handroll | deepagent |
|---------|----------|-----------|
| Entry | `handroll/agent.py:run(task)` | `deepagent/agent.py:run(task)` |
| Loop | `handroll/loop/loop.py:run_loop` | `deepagents` internal graph |
| Tool dispatch | `handroll/executor/executor.py` (`TOOL_REGISTRY` dict) | framework ToolNode (9 built-in tools) |
| Termination | `handroll/evaluator/evaluator.py` (max_turns / loop-detect / self-critique) | framework decides + `task.success_criterion` |
| Result formatting | `handroll/observation/formatter.py` | framework converts ToolMessage → messages |
| Tools used | 3 shared tools (`bash_exec`, `file_read`, `file_write`) | 9 framework-native tools only (`tools=[]`) |

Both `run(task)` functions return a `shared/tracker/run_logger.py:RunLog`. The CLI calls `_run_one` → per-agent `run` → prints a comparison table.

### Shared layer (`shared/`)

Everything in `shared/` is used by **both** paths — this is what makes the comparison fair. Do not add path-specific behavior here without updating both agents.

- `shared/tools/schemas.py` — tool JSON Schemas, dual-exported:
  - `ALL_TOOLS` — OpenAI tools-API format (used by handroll via `shared/utils/llm_client.chat`)
  - `ALL_TOOLS_AS_CALLABLES` — LangChain `StructuredTool` (available to deepagent, currently **not injected**; deepagent runs framework-native only)
  - `to_langchain_tool(schema, fn)` derives both from one source so descriptions stay in sync.
- `shared/tools/{bash_exec,file_read,file_write}.py` — tool implementations. **Tools never raise**; they return `{"ok": False, "error_type": ..., "message": ...}` payloads so the loop stays clean.
- `shared/tracker/run_logger.py` — `RunLog` dataclass. The contract both paths must satisfy. Notable fields: `loop_turns`, `total_input_tokens`, `total_output_tokens`, `system_prompt`, `tool_calls`, `events`, `notes`. `notes` is the canonical place to record any cross-path caliber difference.
- `shared/utils/sandbox.py` — `SANDBOX_DIR` (repo-root `sandbox/`), `resolve_in_sandbox`, `reset_sandbox`. Read the module docstring: the sandbox is a **working directory, not a security boundary**. The old path-prefix guard was intentionally removed because it was voluntary (bash + deepagents bypassed it). For real isolation use containers/namespaces.
- `shared/utils/config.py` — `load_env()` reads `LLM_BASE_URL` / `LLM_API_KEY` / `LLM_MODEL` from `.env` (or existing env vars; `override=False`).
- `shared/utils/llm_client.py` — OpenAI-compatible chat wrapper used by handroll.

### Tasks (`tasks/`)

`tasks/task_base.py:Task` is a dataclass: `id`, `prompt`, `success_criterion: Callable[[str], bool]`, optional `sandbox_seed`. Success criteria can inspect the sandbox filesystem directly (not through the sandbox guard). Tasks register in `tasks/__init__.py:TASKS`. Only `task_01_simple_script` is currently implemented end-to-end.

## Critical cross-path semantics

When changing either path, preserve these invariants or the comparison becomes meaningless.

### 1. Metric calibers (see `RunLog.notes`)

- **`loop_turns`** is defined as **LLM call count** for both paths.
  - handroll: increments per `chat()` call
  - deepagent: counts `AIMessage`s in the event stream (a single LLM call historically bloated into ~3 LangGraph "updates" — do not regress to counting updates)
- **`tool_calls[].ok`**: deepagent must record `_pending` on AIMessage, then back-fill from `ToolMessage.status` (`success`/`error`) and strip `_pending`/`_tool_call_id` via `_cleanup_internal_fields` before `save()`. handroll gets `ok` directly from the tool result.
- **`system_prompt`**: deepagent uses `_SystemPromptCapture` callback to grab the *framework-assembled* prompt (which is ~30× larger than handroll's); handroll stores the constant. Both are recorded so prompt-level diffs are auditable.

### 2. Path semantics differ by design

- handroll: **relative paths** (`hello.py`), resolved via `resolve_in_sandbox` → `sandbox/hello.py`.
- deepagent: `LocalShellBackend(virtual_mode=True, root_dir=sandbox)` makes the model see POSIX virtual paths (`/hello.py`) for file tools, but the `execute` tool's shell `cwd` is the real sandbox dir so shell commands use relative paths.

This produces a known "cognitive gap" in deepagent: file tools and `execute` live in different path spaces. It is documented extensively in `docs/findings/2026-07-10-virtual-mode-and-infra-alignment.md`. Do **not** try to "fix" it by injecting shared tools into deepagent — that creates the namespace collision described in `docs/findings/2026-07-07-deepagent-tool-namespace-collision.md` and was deliberately reverted (`tools=[]`).

### 3. Backend choice is load-bearing

`deepagent/agent.py` uses `LocalShellBackend` specifically. `FilesystemBackend`/`StateBackend` were tried first and failed for documented reasons: `StateBackend` is an in-memory virtual FS (no disk persistence), and `FilesystemBackend` doesn't implement `SandboxBackendProtocol` so the `execute` tool returns errors and forces subagent delegation. See `docs/findings/2026-07-09-deepagent-backend-statebackend.md`.

## Conventions

- Python ≥ 3.11. Each module has a Chinese-language docstring that often includes a `【和 DeepAgent 的对比】` section — these are the author's design notes comparing what the framework handles vs what's hand-written. Preserve them when editing; they're part of the experiment's record.
- The repo uses OpenAI-compatible endpoints (not the Anthropic API directly), despite `PLAN.md` references to `ANTHROPIC_API_KEY` — trust `.env.example` over the plan doc.
- `docs/findings/` is a chronological debugging log. New significant debugging insights go there as dated files, not into CLAUDE.md.
- `sandbox/` and `outputs/runs/` are gitignored except for `.gitkeep`. Don't commit run artifacts.
