# Week 1 Minimal Loop Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement handroll + deepagent paths that both complete `task_01_simple_script` and produce matching RunLog JSON.

**Architecture:** Mirror PLAN.md structure (handroll/ + deepagent/ + shared/ + tasks/ + cli.py). shared/ is the foundation both paths stand on. handroll/ is one file per loop component. deepagent/ is a thin wrapper over LangChain's `deepagents` library. OpenAI-compatible LLM client configurable via `.env`.

**Tech Stack:** Python ≥3.11, openai SDK, langchain + langchain-openai + langgraph + deepagents, rich, python-dotenv, pytest, ruff.

## Global Constraints

- Python ≥ 3.11 (uses `from __future__ import annotations` style + PEP 604 unions)
- LLM provider: OpenAI-compatible API via `LLM_BASE_URL` / `LLM_API_KEY` / `LLM_MODEL` env vars
- Tools return `dict` payloads (never raise); errors are payloads with `ok: False`
- All file/bash operations restricted to `<project>/sandbox/` (path resolve + prefix check)
- Tool schemas: `bash_exec`, `file_read`, `file_write` — same `name`/`description`/`input_schema` on both paths
- RunLog JSON schema is the shared comparison contract — both paths must populate the same fields
- Each core file's top-level docstring must include a `【和 DeepAgent 的对比】` section (added in Task 17 after both paths run)
- Existing root files (`loop.py`, `schemas.py`, `evaluator.py`, `README.md`) are archived to `docs/reference/` and rewritten from scratch
- Commit after every green test cycle; never batch multiple features in one commit

---

## File Structure

```
loop-engineer/
├── handroll/
│   ├── __init__.py                       # empty
│   ├── agent.py                          # run(task) -> RunLog orchestrator
│   ├── loop/
│   │   ├── __init__.py                   # empty
│   │   └── loop.py                       # run_loop + parse_response
│   ├── executor/
│   │   ├── __init__.py                   # empty
│   │   └── executor.py                   # TOOL_REGISTRY + execute_tool
│   ├── evaluator/
│   │   ├── __init__.py                   # empty
│   │   └── evaluator.py                  # Evaluator class
│   ├── observation/
│   │   ├── __init__.py                   # empty
│   │   └── formatter.py                  # format_observation
│   ├── planners/
│   │   └── __init__.py                   # empty placeholder (Week 3)
│   └── memory/
│       └── __init__.py                   # empty placeholder (Phase 2)
├── deepagent/
│   ├── __init__.py                       # empty
│   └── agent.py                          # build_agent + run(task) -> RunLog
├── shared/
│   ├── __init__.py                       # empty
│   ├── tools/
│   │   ├── __init__.py                   # empty
│   │   ├── schemas.py                    # ALL_TOOLS + ALL_TOOLS_AS_CALLABLES
│   │   ├── bash_exec.py                  # run(**kwargs) -> dict
│   │   ├── file_read.py                  # run(**kwargs) -> dict
│   │   └── file_write.py                 # run(**kwargs) -> dict
│   ├── utils/
│   │   ├── __init__.py                   # empty
│   │   ├── config.py                     # LLMConfig + load_env
│   │   ├── llm_client.py                 # chat() OpenAI-compatible
│   │   └── sandbox.py                    # SANDBOX_DIR + resolve_in_sandbox + reset_sandbox
│   └── tracker/
│       ├── __init__.py                   # empty
│       └── run_logger.py                 # RunLog dataclass
├── tasks/
│   ├── __init__.py                       # TASKS registry
│   ├── task_base.py                      # Task dataclass
│   └── benchmark/
│       ├── __init__.py                   # empty
│       └── task_01_simple_script.py      # TASK object + success()
├── tests/
│   ├── conftest.py                       # shared fixtures
│   ├── test_config.py
│   ├── test_sandbox.py
│   ├── test_run_logger.py
│   ├── test_bash_exec.py
│   ├── test_file_read.py
│   ├── test_file_write.py
│   ├── test_schemas.py
│   ├── test_llm_client.py
│   ├── test_executor.py
│   ├── test_formatter.py
│   ├── test_evaluator.py
│   ├── test_loop.py
│   ├── test_agent_handroll.py
│   └── test_task_01.py
├── sandbox/
│   └── .gitkeep
├── outputs/
│   └── runs/
│       └── .gitkeep
├── docs/
│   └── reference/                        # archived v0 code
│       ├── loop.py
│       ├── schemas.py
│       └── evaluator.py
├── cli.py
├── pyproject.toml
├── .env.example
├── .gitignore
└── README.md
```

**Responsibility split:** each `shared/` file is one concept (one tool, one helper). `handroll/` subdirs each hold one loop component. `deepagent/` is a single file because the framework does most of the work — that thinness is itself a learning point.

---

## Task 1: Project foundation and scaffolding

**Files:**
- Create: `pyproject.toml`, `.env.example`, `.gitignore`, `README.md` (overwrite)
- Create: every `__init__.py` listed above (empty files)
- Create: `sandbox/.gitkeep`, `outputs/runs/.gitkeep`
- Move: root `loop.py` / `schemas.py` / `evaluator.py` → `docs/reference/`

**Interfaces:**
- Produces: an importable Python package `loop-engineer` with subpackages `shared`, `handroll`, `deepagent`, `tasks`

- [ ] **Step 1: Archive existing root files**

```bash
mkdir -p docs/reference
git mv loop.py docs/reference/loop.py 2>/dev/null || mv loop.py docs/reference/loop.py
git mv schemas.py docs/reference/schemas.py 2>/dev/null || mv schemas.py docs/reference/schemas.py
git mv evaluator.py docs/reference/evaluator.py 2>/dev/null || mv evaluator.py docs/reference/evaluator.py
```

- [ ] **Step 2: Create .gitignore**

Create `.gitignore`:

```
__pycache__/
*.pyc
.pytest_cache/
.ruff_cache/
.venv/
.env
sandbox/*
!sandbox/.gitkeep
outputs/runs/*
!outputs/runs/.gitkeep
tmpclaude-*
```

- [ ] **Step 3: Create .env.example**

Create `.env.example`:

```
# LLM provider config — OpenAI-compatible endpoint
LLM_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=sk-your-key-here
LLM_MODEL=gpt-4o-mini
```

- [ ] **Step 4: Create pyproject.toml**

Create `pyproject.toml`:

```toml
[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "loop-engineer"
version = "0.1.0"
description = "Loop Engineering Lab — handroll vs deepagents comparison"
requires-python = ">=3.11"
dependencies = [
    "openai>=1.40",
    "langchain>=0.3",
    "langchain-openai>=0.2",
    "langgraph>=0.2",
    "deepagents>=0.0.5",
    "rich>=13",
    "python-dotenv>=1",
]

[project.optional-dependencies]
dev = ["pytest>=8", "ruff>=0.5"]

[tool.setuptools.packages.find]
where = ["."]
include = ["shared*", "handroll*", "deepagent*", "tasks*"]
exclude = ["tests*", "docs*", "sandbox*", "outputs*"]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["."]

[tool.ruff]
line-length = 100
target-version = "py311"
```

- [ ] **Step 5: Create directory skeleton and empty __init__.py files**

```bash
mkdir -p shared/tools shared/utils shared/tracker
mkdir -p handroll/loop handroll/executor handroll/evaluator handroll/observation handroll/planners handroll/memory
mkdir -p deepagent
mkdir -p tasks/benchmark
mkdir -p tests sandbox outputs/runs
```

Create these as empty files: `shared/__init__.py`, `shared/tools/__init__.py`, `shared/utils/__init__.py`, `shared/tracker/__init__.py`, `handroll/__init__.py`, `handroll/loop/__init__.py`, `handroll/executor/__init__.py`, `handroll/evaluator/__init__.py`, `handroll/observation/__init__.py`, `handroll/planners/__init__.py`, `handroll/memory/__init__.py`, `deepagent/__init__.py`, `tasks/benchmark/__init__.py`.

Create empty `sandbox/.gitkeep` and `outputs/runs/.gitkeep`.

- [ ] **Step 6: Overwrite README.md**

Overwrite `README.md`:

```markdown
# Loop Engineering Lab

> 通过手写 agent loop 与 deepagents 框架的对比实验，深度理解 loop engineering 各核心组件的实现原理。

## 快速开始

```bash
pip install -e ".[dev]"
cp .env.example .env   # 编辑 .env 填入 LLM 配置

# 跑两路对比
python -m cli run --agent both --task task_01_simple_script
```

## 核心文件阅读顺序

1. `shared/tools/schemas.py` — 工具定义
2. `handroll/loop/loop.py` — ★ 核心 loop 实现
3. `handroll/executor/executor.py` — 工具分发
4. `handroll/evaluator/evaluator.py` — 终止判断
5. `handroll/observation/formatter.py` — 结果格式化
6. `deepagent/agent.py` — 框架等价实现（极薄）

详细设计见 `docs/superpowers/specs/2026-07-07-week1-minimal-loop-design.md`。
```

- [ ] **Step 7: Install and verify**

Run:

```bash
pip install -e ".[dev]"
python -c "import shared, handroll, deepagent, tasks; print('ok')"
```

Expected: prints `ok`, no errors.

- [ ] **Step 8: Commit**

```bash
git add -A
git commit -m "feat: project scaffolding for week 1"
```

---

## Task 2: `shared/utils/config.py` — env loading

**Files:**
- Create: `shared/utils/config.py`
- Test: `tests/test_config.py`

**Interfaces:**
- Produces: `LLMConfig` dataclass with `LLM_BASE_URL/LLM_API_KEY/LLM_MODEL` fields; `load_env() -> LLMConfig`

- [ ] **Step 1: Write failing test**

Create `tests/test_config.py`:

```python
import os
from shared.utils.config import LLMConfig, load_env

def test_load_env_reads_three_keys(monkeypatch):
    monkeypatch.setenv("LLM_BASE_URL", "https://example.com/v1")
    monkeypatch.setenv("LLM_API_KEY", "sk-test")
    monkeypatch.setenv("LLM_MODEL", "gpt-test")
    cfg = load_env()
    assert cfg.LLM_BASE_URL == "https://example.com/v1"
    assert cfg.LLM_API_KEY == "sk-test"
    assert cfg.LLM_MODEL == "gpt-test"

def test_load_env_missing_key_raises(monkeypatch):
    for k in ("LLM_BASE_URL", "LLM_API_KEY", "LLM_MODEL"):
        monkeypatch.delenv(k, raising=False)
    try:
        load_env()
    except RuntimeError:
        return
    raise AssertionError("expected RuntimeError on missing env")
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_config.py -v
```

Expected: ModuleNotFoundError or ImportError.

- [ ] **Step 3: Implement config.py**

Create `shared/utils/config.py`:

```python
"""LLM 配置加载 —— OpenAI 兼容端点的统一入口。

【和 DeepAgent 的对比】（Task 18 补全）
"""
from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class LLMConfig:
    LLM_BASE_URL: str
    LLM_API_KEY: str
    LLM_MODEL: str


_REQUIRED = ("LLM_BASE_URL", "LLM_API_KEY", "LLM_MODEL")


def load_env() -> LLMConfig:
    """从环境变量读取 LLM 配置。缺失则抛 RuntimeError。"""
    missing = [k for k in _REQUIRED if not os.getenv(k)]
    if missing:
        raise RuntimeError(f"missing env vars: {missing}")
    return LLMConfig(
        LLM_BASE_URL=os.environ["LLM_BASE_URL"],
        LLM_API_KEY=os.environ["LLM_API_KEY"],
        LLM_MODEL=os.environ["LLM_MODEL"],
    )
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_config.py -v
```

Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add shared/utils/config.py tests/test_config.py
git commit -m "feat(config): LLMConfig + load_env"
```

---

## Task 3: `shared/utils/sandbox.py` — path guard

**Files:**
- Create: `shared/utils/sandbox.py`
- Test: `tests/test_sandbox.py`

**Interfaces:**
- Produces: `SANDBOX_DIR: Path`, `resolve_in_sandbox(path: str) -> Path`, `reset_sandbox() -> None`
- Raises: `PermissionError` when path escapes sandbox

- [ ] **Step 1: Write failing test**

Create `tests/test_sandbox.py`:

```python
from pathlib import Path
import pytest
from shared.utils.sandbox import SANDBOX_DIR, resolve_in_sandbox, reset_sandbox


def test_sandbox_dir_is_real_dir():
    assert SANDBOX_DIR.exists()
    assert SANDBOX_DIR.is_dir()


def test_resolve_relative_path_inside_sandbox():
    resolved = resolve_in_sandbox("hello.py")
    assert resolved.parent == SANDBOX_DIR
    assert resolved.name == "hello.py"


def test_resolve_absolute_path_inside_sandbox():
    abs_path = str(SANDBOX_DIR / "sub" / "file.txt")
    resolved = resolve_in_sandbox(abs_path)
    assert resolved.is_relative_to(SANDBOX_DIR)


def test_resolve_path_outside_sandbox_raises():
    with pytest.raises(PermissionError):
        resolve_in_sandbox("../escape.py")
    with pytest.raises(PermissionError):
        resolve_in_sandbox("/etc/passwd")


def test_reset_sandbox_clears_files():
    (SANDBOX_DIR / "leftover.txt").write_text("x")
    reset_sandbox()
    contents = [p for p in SANDBOX_DIR.iterdir() if p.name != ".gitkeep"]
    assert contents == []
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_sandbox.py -v
```

Expected: ImportError.

- [ ] **Step 3: Implement sandbox.py**

Create `shared/utils/sandbox.py`:

```python
"""沙箱路径守卫 —— 把所有文件操作限制在项目根的 sandbox/ 目录下。

设计权衡：
- 主防线是路径 resolve 后的前缀检查（防 `../` 逃逸）
- bash_exec 用 cwd=sandbox/ 启动子进程（不能完全阻止绝对路径访问，已知限制）
- 完整容器隔离留给 Phase 3

【和 DeepAgent 的对比】（Task 18 补全）
"""
from __future__ import annotations

import shutil
from pathlib import Path

SANDBOX_DIR: Path = Path(__file__).resolve().parents[2] / "sandbox"


def resolve_in_sandbox(rel_or_abs_path: str) -> Path:
    """把用户提供的路径解析为 SANDBOX_DIR 下的绝对路径。
    解析后若不在 SANDBOX_DIR 子树内，抛 PermissionError。"""
    p = Path(rel_or_abs_path)
    if not p.is_absolute():
        p = SANDBOX_DIR / p
    resolved = p.resolve()
    try:
        resolved.relative_to(SANDBOX_DIR)
    except ValueError:
        raise PermissionError(
            f"path '{rel_or_abs_path}' resolves outside sandbox: {resolved}"
        )
    return resolved


def reset_sandbox() -> None:
    """清空 sandbox/ 目录（保留 .gitkeep）。"""
    SANDBOX_DIR.mkdir(parents=True, exist_ok=True)
    for p in SANDBOX_DIR.iterdir():
        if p.name == ".gitkeep":
            continue
        if p.is_dir():
            shutil.rmtree(p)
        else:
            p.unlink()
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_sandbox.py -v
```

Expected: 5 passed.

- [ ] **Step 5: Commit**

```bash
git add shared/utils/sandbox.py tests/test_sandbox.py
git commit -m "feat(sandbox): path guard + reset"
```

---

## Task 4: `shared/tracker/run_logger.py` — comparison contract

**Files:**
- Create: `shared/tracker/run_logger.py`
- Test: `tests/test_run_logger.py`

**Interfaces:**
- Produces: `RunLog` dataclass with `log_tool_call`, `log_event`, `finish`, `save` methods

- [ ] **Step 1: Write failing test**

Create `tests/test_run_logger.py`:

```python
import json
from shared.tracker.run_logger import RunLog


def test_default_construction():
    log = RunLog(task_id="t1", agent_type="handroll")
    assert log.success is False
    assert log.tool_calls == []
    assert log.notes == []


def test_log_tool_call_appends():
    log = RunLog(task_id="t1", agent_type="handroll")
    log.log_tool_call("bash_exec", {"command": "ls"}, {"ok": True, "exit_code": 0})
    assert len(log.tool_calls) == 1
    assert log.tool_calls[0]["name"] == "bash_exec"
    assert log.tool_calls[0]["ok"] is True


def test_log_event_appends():
    log = RunLog(task_id="t1", agent_type="handroll")
    log.log_event(turn=1, kind="llm_call", input_tokens=10, output_tokens=5)
    assert log.events[0] == {
        "turn": 1, "kind": "llm_call", "input_tokens": 10, "output_tokens": 5
    }


def test_finish_sets_status():
    log = RunLog(task_id="t1", agent_type="handroll")
    log.finish(success=True, stop_reason="task_complete", final_answer="done")
    assert log.success is True
    assert log.stop_reason == "task_complete"
    assert log.final_answer == "done"


def test_save_writes_json(tmp_path):
    log = RunLog(task_id="t1", agent_type="handroll")
    log.finish(True, "task_complete", "hi")
    path = log.save(dir=str(tmp_path))
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["task_id"] == "t1"
    assert data["agent_type"] == "handroll"
    assert data["success"] is True
    assert "tool_calls" in data
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_run_logger.py -v
```

Expected: ImportError.

- [ ] **Step 3: Implement run_logger.py**

Create `shared/tracker/run_logger.py`:

```python
"""RunLog —— 两路共用的运行日志契约。

设计目的：让 handroll 与 deepagent 的输出可横向对比。
任何字段口径差异通过 notes 字段标注（如 loop_turns 的口径差异）。

【和 DeepAgent 的对比】（Task 18 补全）
"""
from __future__ import annotations

import json
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass
class RunLog:
    task_id: str
    agent_type: str  # "handroll" | "deepagent"
    planner_strategy: str = "react"
    success: bool = False
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    loop_turns: int = 0
    stop_reason: str = ""
    duration_s: float = 0.0
    final_answer: str = ""
    tool_calls: list[dict[str, Any]] = field(default_factory=list)
    events: list[dict[str, Any]] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def log_tool_call(self, name: str, input: dict, result: dict) -> None:
        self.tool_calls.append({
            "name": name,
            "input": input,
            "ok": result.get("ok", False),
            "duration_s": result.get("duration_s", 0.0),
            "exit_code": result.get("exit_code"),
        })

    def log_event(self, turn: int, kind: str, **fields: Any) -> None:
        entry = {"turn": turn, "kind": kind}
        entry.update(fields)
        self.events.append(entry)

    def finish(self, success: bool, stop_reason: str, final_answer: str) -> None:
        self.success = success
        self.stop_reason = stop_reason
        self.final_answer = final_answer

    def save(self, dir: str = "outputs/runs") -> Path:
        out_dir = Path(dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        fname = f"{ts}_{self.agent_type}_{self.task_id}.json"
        path = out_dir / fname
        path.write_text(
            json.dumps(asdict(self), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return path
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_run_logger.py -v
```

Expected: 5 passed.

- [ ] **Step 5: Commit**

```bash
git add shared/tracker/run_logger.py tests/test_run_logger.py
git commit -m "feat(run_logger): RunLog dataclass with save/events/tool_calls"
```

---

## Task 5: `shared/tools/bash_exec.py`

**Files:**
- Create: `shared/tools/bash_exec.py`
- Test: `tests/test_bash_exec.py`

**Interfaces:**
- Produces: `run(command: str, timeout: int = 30) -> dict`
- Returns: `{"ok": bool, "stdout": str, "stderr": str, "exit_code": int, "duration_s": float}` on success; on timeout `{"ok": False, "error_type": "TimeoutExpired", ...}`

- [ ] **Step 1: Write failing test**

Create `tests/test_bash_exec.py`:

```python
from shared.tools.bash_exec import run


def test_run_echo():
    result = run(command="echo hello")
    assert result["ok"] is True
    assert result["exit_code"] == 0
    assert "hello" in result["stdout"]
    assert result["duration_s"] >= 0


def test_run_failure_exit_code():
    result = run(command="python -c \"import sys; sys.exit(2)\"")
    assert result["ok"] is False
    assert result["exit_code"] == 2


def test_run_timeout():
    result = run(command="python -c \"import time; time.sleep(5)\"", timeout=1)
    assert result["ok"] is False
    assert result["error_type"] == "TimeoutExpired"


def test_run_cwd_is_sandbox():
    from shared.utils.sandbox import SANDBOX_DIR
    result = run(command="echo %cd%" if _is_windows() else "pwd")
    # On Windows, %cd% expands in cmd; we use a python-based check instead
    result2 = run(command="python -c \"import os; print(os.getcwd())\"")
    assert str(SANDBOX_DIR) in result2["stdout"]


def _is_windows():
    import sys
    return sys.platform.startswith("win")
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_bash_exec.py -v
```

Expected: ImportError.

- [ ] **Step 3: Implement bash_exec.py**

Create `shared/tools/bash_exec.py`:

```python
"""bash_exec 工具 —— 在沙箱工作目录中执行 shell 命令。

设计：
- 子进程 cwd 设为 sandbox/
- 超时默认 30s；超时返回错误 payload（不抛异常）
- Windows 下使用 cmd.exe；其他平台使用 /bin/bash

已知限制：cwd 限制无法阻止 LLM 通过绝对路径访问沙箱外文件。
Phase 3 会引入容器隔离。

【和 DeepAgent 的对比】（Task 18 补全）
"""
from __future__ import annotations

import subprocess
import sys
import time

from shared.utils.sandbox import SANDBOX_DIR


def run(command: str, timeout: int = 30) -> dict:
    start = time.time()
    try:
        if sys.platform.startswith("win"):
            proc = subprocess.run(
                command,
                cwd=str(SANDBOX_DIR),
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
        else:
            proc = subprocess.run(
                ["bash", "-c", command],
                cwd=str(SANDBOX_DIR),
                capture_output=True,
                text=True,
                timeout=timeout,
            )
        duration = time.time() - start
        ok = proc.returncode == 0
        return {
            "ok": ok,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
            "exit_code": proc.returncode,
            "duration_s": round(duration, 3),
        }
    except subprocess.TimeoutExpired as e:
        return {
            "ok": False,
            "error_type": "TimeoutExpired",
            "message": f"超时 {timeout}s",
            "stdout": e.stdout or "" if isinstance(e.stdout, str) else "",
            "stderr": e.stderr or "" if isinstance(e.stderr, str) else "",
            "exit_code": -1,
            "duration_s": round(time.time() - start, 3),
        }
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_bash_exec.py -v
```

Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add shared/tools/bash_exec.py tests/test_bash_exec.py
git commit -m "feat(bash_exec): sandboxed shell exec tool"
```

---

## Task 6: `shared/tools/file_read.py`

**Files:**
- Create: `shared/tools/file_read.py`
- Test: `tests/test_file_read.py`

**Interfaces:**
- Produces: `run(path: str, encoding: str = "utf-8") -> dict`

- [ ] **Step 1: Write failing test**

Create `tests/test_file_read.py`:

```python
from shared.tools.file_read import run
from shared.utils.sandbox import SANDBOX_DIR, reset_sandbox


def setup_function():
    reset_sandbox()


def test_read_existing_file():
    (SANDBOX_DIR / "sample.txt").write_text("hello\nworld\n", encoding="utf-8")
    result = run(path="sample.txt")
    assert result["ok"] is True
    assert "hello" in result["content"]
    assert result["lines"] == 2


def test_read_missing_file():
    result = run(path="nope.txt")
    assert result["ok"] is False
    assert result["error_type"] == "FileNotFoundError"


def test_read_outside_sandbox():
    result = run(path="../../etc/passwd")
    assert result["ok"] is False
    assert result["error_type"] == "PermissionError"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_file_read.py -v
```

Expected: ImportError.

- [ ] **Step 3: Implement file_read.py**

Create `shared/tools/file_read.py`:

```python
"""file_read 工具 —— 读取沙箱内的文件。

设计：
- 通过 resolve_in_sandbox 强制路径在 sandbox/ 子树内
- 失败（文件不存在 / 权限）返回错误 payload，不抛异常

【和 DeepAgent 的对比】（Task 18 补全）
"""
from __future__ import annotations

from shared.utils.sandbox import resolve_in_sandbox


def run(path: str, encoding: str = "utf-8") -> dict:
    try:
        resolved = resolve_in_sandbox(path)
        if not resolved.exists():
            return {
                "ok": False,
                "error_type": "FileNotFoundError",
                "message": f"文件不存在：{path}",
            }
        content = resolved.read_text(encoding=encoding)
        lines = content.count("\n") + (0 if content.endswith("\n") or content == "" else 1)
        return {
            "ok": True,
            "path": str(resolved),
            "content": content,
            "lines": lines,
        }
    except PermissionError as e:
        return {
            "ok": False,
            "error_type": "PermissionError",
            "message": str(e),
        }
    except Exception as e:
        return {
            "ok": False,
            "error_type": type(e).__name__,
            "message": str(e),
        }
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_file_read.py -v
```

Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add shared/tools/file_read.py tests/test_file_read.py
git commit -m "feat(file_read): sandboxed file read tool"
```

---

## Task 7: `shared/tools/file_write.py`

**Files:**
- Create: `shared/tools/file_write.py`
- Test: `tests/test_file_write.py`

**Interfaces:**
- Produces: `run(path: str, content: str, encoding: str = "utf-8") -> dict`

- [ ] **Step 1: Write failing test**

Create `tests/test_file_write.py`:

```python
from shared.tools.file_write import run
from shared.utils.sandbox import SANDBOX_DIR, reset_sandbox


def setup_function():
    reset_sandbox()


def test_write_creates_file():
    result = run(path="out.txt", content="hello world")
    assert result["ok"] is True
    assert result["bytes"] == 11
    assert (SANDBOX_DIR / "out.txt").read_text() == "hello world"


def test_write_auto_creates_parent_dirs():
    result = run(path="sub/dir/file.txt", content="x")
    assert result["ok"] is True
    assert (SANDBOX_DIR / "sub" / "dir" / "file.txt").read_text() == "x"


def test_write_outside_sandbox_rejected():
    result = run(path="../escape.txt", content="x")
    assert result["ok"] is False
    assert result["error_type"] == "PermissionError"


def test_write_overwrites_existing():
    (SANDBOX_DIR / "exists.txt").write_text("old")
    run(path="exists.txt", content="new")
    assert (SANDBOX_DIR / "exists.txt").read_text() == "new"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_file_write.py -v
```

Expected: ImportError.

- [ ] **Step 3: Implement file_write.py**

Create `shared/tools/file_write.py`:

```python
"""file_write 工具 —— 写入沙箱内文件。

设计：
- 自动创建父目录
- 已存在文件直接覆盖
- 通过 resolve_in_sandbox 强制路径在 sandbox/ 子树内

【和 DeepAgent 的对比】（Task 18 补全）
"""
from __future__ import annotations

from shared.utils.sandbox import resolve_in_sandbox


def run(path: str, content: str, encoding: str = "utf-8") -> dict:
    try:
        resolved = resolve_in_sandbox(path)
        resolved.parent.mkdir(parents=True, exist_ok=True)
        data = content.encode(encoding)
        resolved.write_bytes(data)
        return {
            "ok": True,
            "path": str(resolved),
            "bytes": len(data),
        }
    except PermissionError as e:
        return {
            "ok": False,
            "error_type": "PermissionError",
            "message": str(e),
        }
    except Exception as e:
        return {
            "ok": False,
            "error_type": type(e).__name__,
            "message": str(e),
        }
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_file_write.py -v
```

Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add shared/tools/file_write.py tests/test_file_write.py
git commit -m "feat(file_write): sandboxed file write tool"
```

---

## Task 8: `shared/tools/schemas.py` — schema registry + LangChain adapters

**Files:**
- Create: `shared/tools/schemas.py`
- Test: `tests/test_schemas.py`

**Interfaces:**
- Produces: `ALL_TOOLS: list[dict]`, `ALL_TOOLS_AS_CALLABLES: list` (LangChain tools), `to_langchain_tool(schema: dict, fn: callable) -> BaseTool`

- [ ] **Step 1: Write failing test**

Create `tests/test_schemas.py`:

```python
from shared.tools.schemas import ALL_TOOLS, ALL_TOOLS_AS_CALLABLES


def test_all_tools_has_three_schemas():
    assert len(ALL_TOOLS) == 3
    names = {t["name"] for t in ALL_TOOLS}
    assert names == {"bash_exec", "file_read", "file_write"}


def test_each_schema_has_required_fields():
    for t in ALL_TOOLS:
        assert "name" in t
        assert "description" in t
        assert "input_schema" in t
        assert t["input_schema"]["type"] == "object"


def test_callables_match_schemas():
    assert len(ALL_TOOLS_AS_CALLABLES) == 3
    schema_names = {t["name"] for t in ALL_TOOLS}
    callable_names = {t.name for t in ALL_TOOLS_AS_CALLABLES}
    assert schema_names == callable_names


def test_callable_descriptions_match_schemas():
    by_schema = {t["name"]: t["description"] for t in ALL_TOOLS}
    for tool in ALL_TOOLS_AS_CALLABLES:
        assert tool.description == by_schema[tool.name]
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_schemas.py -v
```

Expected: ImportError.

- [ ] **Step 3: Implement schemas.py**

Create `shared/tools/schemas.py`:

```python
"""工具 JSON Schema 注册表 + LangChain 适配。

双形式导出：
- ALL_TOOLS              给 handroll 直接构造 OpenAI tools API 请求
- ALL_TOOLS_AS_CALLABLES 给 deepagents 经 LangChain 调度

两套形式共享相同的 name/description/input_schema，
通过 to_langchain_tool(schema, fn) 派生保证一致。

【和 DeepAgent 的对比】（Task 18 补全）
"""
from __future__ import annotations

from typing import Callable

from langchain_core.tools import StructuredTool


def _schema(name: str, description: str, properties: dict, required: list[str]) -> dict:
    return {
        "name": name,
        "description": description,
        "input_schema": {
            "type": "object",
            "properties": properties,
            "required": required,
        },
    }


BASH_EXEC_SCHEMA = _schema(
    name="bash_exec",
    description=(
        "在沙箱 shell（限制在 sandbox/ 工作目录）中执行一条 bash 命令，"
        "返回 stdout、stderr 和 exit_code。超时默认 30 秒。"
    ),
    properties={
        "command": {"type": "string", "description": "要执行的 bash 命令"},
        "timeout": {"type": "integer", "description": "超时秒数，默认 30", "default": 30},
    },
    required=["command"],
)

FILE_READ_SCHEMA = _schema(
    name="file_read",
    description="读取 sandbox/ 工作目录下的文件内容，返回文本字符串。",
    properties={
        "path": {"type": "string", "description": "文件路径（相对 sandbox/ 或绝对）"},
        "encoding": {"type": "string", "description": "文件编码，默认 utf-8", "default": "utf-8"},
    },
    required=["path"],
)

FILE_WRITE_SCHEMA = _schema(
    name="file_write",
    description=(
        "将内容写入 sandbox/ 工作目录下的文件。"
        "若文件不存在则创建，若存在则覆盖。自动创建缺失的父目录。"
    ),
    properties={
        "path": {"type": "string", "description": "文件路径"},
        "content": {"type": "string", "description": "要写入的内容"},
        "encoding": {"type": "string", "description": "文件编码，默认 utf-8", "default": "utf-8"},
    },
    required=["path", "content"],
)

ALL_TOOLS = [BASH_EXEC_SCHEMA, FILE_READ_SCHEMA, FILE_WRITE_SCHEMA]


def to_langchain_tool(schema: dict, fn: Callable) -> StructuredTool:
    """从 schema dict + Python 函数派生一个 LangChain StructuredTool。
    共享 schema 的 name/description/input_schema，保证两路 LLM 看到相同描述。"""
    return StructuredTool.from_function(
        func=fn,
        name=schema["name"],
        description=schema["description"],
        args_schema=None,  # input_schema 不直接用 pydantic；依赖 StructuredTool 推断
    )


# 注：LangChain 工具的 args schema 通过函数签名推断（**kwargs 不行，需显式参数）
# 因此我们直接 wrap 一个有签名的函数
from shared.tools import bash_exec as _bash
from shared.tools import file_read as _fread
from shared.tools import file_write as _fwrite


def _bash_wrapped(command: str, timeout: int = 30) -> dict:
    """bash_exec 的 LangChain 入口（签名必须显式，不能用 **kwargs）"""
    return _bash.run(command=command, timeout=timeout)


def _file_read_wrapped(path: str, encoding: str = "utf-8") -> dict:
    return _fread.run(path=path, encoding=encoding)


def _file_write_wrapped(path: str, content: str, encoding: str = "utf-8") -> dict:
    return _fwrite.run(path=path, content=content, encoding=encoding)


ALL_TOOLS_AS_CALLABLES = [
    to_langchain_tool(BASH_EXEC_SCHEMA, _bash_wrapped),
    to_langchain_tool(FILE_READ_SCHEMA, _file_read_wrapped),
    to_langchain_tool(FILE_WRITE_SCHEMA, _file_write_wrapped),
]
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_schemas.py -v
```

Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add shared/tools/schemas.py tests/test_schemas.py
git commit -m "feat(schemas): dual-form tool registry (dict + LangChain)"
```

---

## Task 9: `shared/utils/llm_client.py` — OpenAI-compatible chat

**Files:**
- Create: `shared/utils/llm_client.py`
- Test: `tests/test_llm_client.py`

**Interfaces:**
- Produces: `chat(messages: list[dict], system: str, tools: list[dict], max_tokens: int = 1024) -> tuple[object, int, int]`

- [ ] **Step 1: Write failing test**

Create `tests/test_llm_client.py`:

```python
from unittest.mock import patch, MagicMock
from shared.utils.llm_client import chat


def _fake_response(text="ok", tool_calls=None, in_tok=10, out_tok=5):
    msg = MagicMock()
    msg.content = text
    msg.tool_calls = tool_calls or []
    resp = MagicMock()
    resp.choices = [MagicMock(message=msg)]
    resp.usage = MagicMock(prompt_tokens=in_tok, completion_tokens=out_tok)
    return resp


def test_chat_returns_response_and_tokens(monkeypatch):
    monkeypatch.setenv("LLM_BASE_URL", "https://x/v1")
    monkeypatch.setenv("LLM_API_KEY", "sk-x")
    monkeypatch.setenv("LLM_MODEL", "gpt-x")
    fake = _fake_response(in_tok=20, out_tok=7)
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = fake
    with patch("shared.utils.llm_client._get_client", return_value=mock_client):
        resp, in_tok, out_tok = chat(
            messages=[{"role": "user", "content": "hi"}],
            system="you are helpful",
            tools=[],
        )
    assert in_tok == 20
    assert out_tok == 7


def test_chat_passes_tools_through(monkeypatch):
    monkeypatch.setenv("LLM_BASE_URL", "https://x/v1")
    monkeypatch.setenv("LLM_API_KEY", "sk-x")
    monkeypatch.setenv("LLM_MODEL", "gpt-x")
    fake = _fake_response()
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = fake
    with patch("shared.utils.llm_client._get_client", return_value=mock_client):
        chat(
            messages=[{"role": "user", "content": "hi"}],
            system="s",
            tools=[{"name": "bash_exec", "description": "x", "input_schema": {}}],
        )
    call_kwargs = mock_client.chat.completions.create.call_args.kwargs
    assert "tools" in call_kwargs
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_llm_client.py -v
```

Expected: ImportError.

- [ ] **Step 3: Implement llm_client.py**

Create `shared/utils/llm_client.py`:

```python
"""OpenAI 兼容 chat 客户端 —— handroll 路直接使用。

deepagent 路不直接用此客户端，而是构造一个配置了相同 base_url/api_key/model
的 langchain_openai.ChatOpenAI 实例。

设计：
- 模块级 _client 单例（首次 chat() 时 lazy init）
- tools 参数透传给 OpenAI tools API
- 返回 (response, input_tokens, output_tokens)，token 从 response.usage 提取

【和 DeepAgent 的对比】（Task 18 补全）
"""
from __future__ import annotations

from typing import Any

from openai import OpenAI

from shared.utils.config import load_env

_client: OpenAI | None = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        cfg = load_env()
        _client = OpenAI(base_url=cfg.LLM_BASE_URL, api_key=cfg.LLM_API_KEY)
    return _client


def _to_openai_tools(schemas: list[dict]) -> list[dict]:
    return [
        {
            "type": "function",
            "function": {
                "name": s["name"],
                "description": s["description"],
                "parameters": s["input_schema"],
            },
        }
        for s in schemas
    ]


def chat(
    messages: list[dict],
    system: str,
    tools: list[dict],
    max_tokens: int = 1024,
) -> tuple[Any, int, int]:
    """OpenAI 兼容 chat 调用。返回 (response, input_tokens, output_tokens)。"""
    client = _get_client()
    cfg = load_env()
    full_messages = [{"role": "system", "content": system}] + messages
    kwargs: dict[str, Any] = {
        "model": cfg.LLM_MODEL,
        "messages": full_messages,
        "max_tokens": max_tokens,
    }
    if tools:
        kwargs["tools"] = _to_openai_tools(tools)
    resp = client.chat.completions.create(**kwargs)
    in_tok = getattr(resp.usage, "prompt_tokens", 0) if resp.usage else 0
    out_tok = getattr(resp.usage, "completion_tokens", 0) if resp.usage else 0
    return resp, in_tok, out_tok
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_llm_client.py -v
```

Expected: 2 passed.

- [ ] **Step 5: Commit**

```bash
git add shared/utils/llm_client.py tests/test_llm_client.py
git commit -m "feat(llm_client): OpenAI-compatible chat wrapper"
```

---

## Task 10: `handroll/executor/executor.py`

**Files:**
- Create: `handroll/executor/executor.py`
- Test: `tests/test_executor.py`

**Interfaces:**
- Consumes: `bash_exec.run`, `file_read.run`, `file_write.run`, `RunLog`
- Produces: `TOOL_REGISTRY: dict`, `execute_tool(name: str, input: dict, run_log: RunLog) -> dict`

- [ ] **Step 1: Write failing test**

Create `tests/test_executor.py`:

```python
from handroll.executor.executor import execute_tool, TOOL_REGISTRY
from shared.tracker.run_logger import RunLog


def _new_log():
    return RunLog(task_id="t", agent_type="handroll")


def test_registry_has_three_tools():
    assert set(TOOL_REGISTRY) == {"bash_exec", "file_read", "file_write"}


def test_execute_known_tool_logs():
    log = _new_log()
    result = execute_tool("bash_exec", {"command": "echo hi"}, log)
    assert result["ok"] is True
    assert len(log.tool_calls) == 1
    assert log.tool_calls[0]["name"] == "bash_exec"


def test_execute_unknown_tool_returns_error():
    log = _new_log()
    result = execute_tool("nonexistent", {}, log)
    assert result["ok"] is False
    assert result["error_type"] == "UnknownTool"
    assert len(log.tool_calls) == 1


def test_execute_handles_exception():
    log = _new_log()
    # Patch bash_exec.run to raise
    from handroll.executor import executor as exec_mod
    original = exec_mod.bash_exec.run
    exec_mod.bash_exec.run = lambda **kw: (_ for _ in ()).throw(RuntimeError("boom"))
    try:
        result = execute_tool("bash_exec", {"command": "x"}, log)
    finally:
        exec_mod.bash_exec.run = original
    assert result["ok"] is False
    assert result["error_type"] == "RuntimeError"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_executor.py -v
```

Expected: ImportError.

- [ ] **Step 3: Implement executor.py**

Create `handroll/executor/executor.py`:

```python
"""Executor —— 工具调用分发器。

设计：
- TOOL_REGISTRY 把工具名映射到 run 函数
- 所有异常捕获并转为错误 payload（保险丝；工具本身不应抛异常）
- 每次 execute 都通过 run_log.log_tool_call 记录

【和 DeepAgent 的对比】（Task 18 补全）
"""
from __future__ import annotations

from shared.tools import bash_exec, file_read, file_write
from shared.tracker.run_logger import RunLog

TOOL_REGISTRY = {
    "bash_exec": bash_exec.run,
    "file_read": file_read.run,
    "file_write": file_write.run,
}


def execute_tool(name: str, input: dict, run_log: RunLog) -> dict:
    if name not in TOOL_REGISTRY:
        err = {
            "ok": False,
            "error_type": "UnknownTool",
            "message": f"未知工具：{name}",
        }
        run_log.log_tool_call(name, input, err)
        return err
    try:
        result = TOOL_REGISTRY[name](**input)
        run_log.log_tool_call(name, input, result)
        return result
    except Exception as e:
        err = {
            "ok": False,
            "error_type": type(e).__name__,
            "message": str(e),
        }
        run_log.log_tool_call(name, input, err)
        return err
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_executor.py -v
```

Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add handroll/executor/executor.py tests/test_executor.py
git commit -m "feat(executor): tool dispatch with error capture"
```

---

## Task 11: `handroll/observation/formatter.py`

**Files:**
- Create: `handroll/observation/formatter.py`
- Test: `tests/test_formatter.py`

**Interfaces:**
- Produces: `format_observation(tool_name: str, tool_input: dict, result: dict, mode: str = "structured") -> str`

- [ ] **Step 1: Write failing test**

Create `tests/test_formatter.py`:

```python
from handroll.observation.formatter import format_observation


def test_bash_exec_success_structured():
    out = format_observation(
        "bash_exec", {"command": "echo hi"},
        {"ok": True, "stdout": "hi\n", "stderr": "", "exit_code": 0},
    )
    assert "退出代码 0" in out
    assert "hi" in out


def test_bash_exec_failure_structured():
    out = format_observation(
        "bash_exec", {"command": "x"},
        {"ok": False, "error_type": "TimeoutExpired", "message": "超时 30s"},
    )
    assert "[错误]" in out
    assert "TimeoutExpired" in out


def test_file_read_success_structured():
    out = format_observation(
        "file_read", {"path": "a.py"},
        {"ok": True, "content": "print('x')\n", "lines": 1},
    )
    assert "已读取" in out
    assert "print('x')" in out


def test_file_write_success_structured():
    out = format_observation(
        "file_write", {"path": "a.py", "content": "x"},
        {"ok": True, "bytes": 1},
    )
    assert "已写入" in out
    assert "1 字节" in out


def test_raw_mode_returns_json():
    out = format_observation(
        "bash_exec", {"command": "x"},
        {"ok": True, "stdout": "hi", "exit_code": 0},
        mode="raw",
    )
    assert '"stdout"' in out
    assert '"exit_code"' in out
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_formatter.py -v
```

Expected: ImportError.

- [ ] **Step 3: Implement formatter.py**

Create `handroll/observation/formatter.py`:

```python
"""Observation 格式化器 —— 把工具返回的 dict 渲染成 LLM 易消化的字符串。

设计：
- structured（默认）：每工具一个对齐模板，错误统一前缀 [错误]
- raw：直接 json.dumps（Week 2 做 A/B 对比时启用）

【和 DeepAgent 的对比】（Task 18 补全）
"""
from __future__ import annotations

import json


def format_observation(tool_name: str, tool_input: dict, result: dict, mode: str = "structured") -> str:
    if mode == "raw":
        return json.dumps(result, ensure_ascii=False, indent=2)
    if not result.get("ok"):
        return _format_error(tool_name, result)
    if tool_name == "bash_exec":
        return _format_bash_success(result)
    if tool_name == "file_read":
        return _format_read_success(tool_input, result)
    if tool_name == "file_write":
        return _format_write_success(tool_input, result)
    return json.dumps(result, ensure_ascii=False, indent=2)


def _format_error(tool_name: str, result: dict) -> str:
    return f"[错误] {tool_name} 失败：{result.get('message', '')}（类型：{result.get('error_type', 'Unknown')}）"


def _format_bash_success(result: dict) -> str:
    return (
        f"退出代码 {result.get('exit_code', -1)}\n"
        f"--- stdout ---\n{result.get('stdout', '')}\n"
        f"--- stderr ---\n{result.get('stderr', '')}"
    )


def _format_read_success(tool_input: dict, result: dict) -> str:
    return f"已读取 {tool_input.get('path')}（{result.get('lines', 0)} 行）：\n\n{result.get('content', '')}"


def _format_write_success(tool_input: dict, result: dict) -> str:
    return f"已写入 {result.get('bytes', 0)} 字节到 {tool_input.get('path')}"
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_formatter.py -v
```

Expected: 5 passed.

- [ ] **Step 5: Commit**

```bash
git add handroll/observation/formatter.py tests/test_formatter.py
git commit -m "feat(formatter): structured + raw observation formats"
```

---

## Task 12: `handroll/evaluator/evaluator.py`

**Files:**
- Create: `handroll/evaluator/evaluator.py`
- Test: `tests/test_evaluator.py`

**Interfaces:**
- Produces: `Evaluator` class with `should_stop(task, last_response, current_turn, last_action) -> tuple[bool, str]`

- [ ] **Step 1: Write failing test**

Create `tests/test_evaluator.py`:

```python
from unittest.mock import patch, MagicMock
from handroll.evaluator.evaluator import Evaluator


def test_max_turns_returns_stop():
    ev = Evaluator(max_turns=3)
    stop, reason = ev.should_stop(task="x", last_response="y", current_turn=3, last_action=None)
    assert stop is True
    assert reason == "max_turns"


def test_max_turns_not_reached():
    ev = Evaluator(max_turns=3)
    with patch("handroll.evaluator.evaluator.chat") as mock_chat:
        mock_chat.return_value = (MagicMock(content=[MagicMock(text="INCOMPLETE")]), 0, 0)
        stop, _ = ev.should_stop(task="x", last_response="y", current_turn=1, last_action=None)
    assert stop is False


def test_loop_detection_after_three_same_actions():
    ev = Evaluator(max_turns=10)
    action = {"name": "bash_exec", "input": {"command": "ls"}}
    with patch("handroll.evaluator.evaluator.chat") as mock_chat:
        mock_chat.return_value = (MagicMock(content=[MagicMock(text="INCOMPLETE")]), 0, 0)
        ev.should_stop("x", "y", 1, action)
        ev.should_stop("x", "y", 2, action)
        stop, reason = ev.should_stop("x", "y", 3, action)
    assert stop is True
    assert reason == "loop_detected"


def test_self_critique_complete():
    ev = Evaluator(max_turns=10)
    with patch("handroll.evaluator.evaluator.chat") as mock_chat:
        mock_chat.return_value = (MagicMock(content=[MagicMock(text="COMPLETE: done")]), 0, 0)
        stop, reason = ev.should_stop(task="x", last_response="done", current_turn=1, last_action=None)
    assert stop is True
    assert reason == "task_complete"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_evaluator.py -v
```

Expected: ImportError.

- [ ] **Step 3: Implement evaluator.py**

Create `handroll/evaluator/evaluator.py`:

```python
"""Evaluator —— 判断 agent loop 何时终止。

三策略组合（按优先级）：
1. max_turns      硬上限兜底
2. loop_detect    同一 action hash 出现 ≥3 次即停止
3. self_critique  LLM 自评（实际 Week 1 几乎不触发，因无 tool_use 时已在 loop 内停止）

【和 DeepAgent 的对比】（Task 18 补全）
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
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_evaluator.py -v
```

Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add handroll/evaluator/evaluator.py tests/test_evaluator.py
git commit -m "feat(evaluator): max_turns + loop_detect + self_critique"
```

---

## Task 13: `handroll/loop/loop.py` — core 6-step loop

**Files:**
- Create: `handroll/loop/loop.py`
- Test: `tests/test_loop.py`

**Interfaces:**
- Consumes: `chat`, `ALL_TOOLS`, `execute_tool`, `format_observation`, `Evaluator`, `Task`, `RunLog`
- Produces: `run_loop(task, system_prompt, run_log, max_turns) -> RunLog`, `parse_response(resp) -> tuple[list[str], list[dict]]`

- [ ] **Step 1: Write failing test**

Create `tests/test_loop.py`. We define a local `_StubTask` with the same shape as the real `Task` dataclass (added in Task 14), so loop tests don't depend on `tasks.task_base`:

```python
from __future__ import annotations
from dataclasses import dataclass
from unittest.mock import patch, MagicMock

from handroll.loop.loop import run_loop, parse_response
from shared.tracker.run_logger import RunLog


@dataclass
class _StubTask:
    """Mirror of tasks.task_base.Task shape; lets loop tests run before Task exists."""
    id: str
    prompt: str
    success_criterion: object


def _fake_resp(text="", tool_calls=None, in_tok=10, out_tok=5):
    msg = MagicMock()
    msg.content = text
    msg.tool_calls = tool_calls or []
    resp = MagicMock()
    resp.choices = [MagicMock(message=msg)]
    resp.usage = MagicMock(prompt_tokens=in_tok, completion_tokens=out_tok)
    return resp


def _task():
    return _StubTask(id="t1", prompt="do it", success_criterion=lambda x: True)


def test_parse_response_extracts_text_and_tool_calls():
    msg = MagicMock()
    msg.content = "thinking"
    msg.tool_calls = [
        MagicMock(id="1", type="function",
                  function=MagicMock(name="bash_exec", arguments='{"command": "ls"}'))
    ]
    resp = MagicMock()
    resp.choices = [MagicMock(message=msg)]
    text_parts, tool_calls = parse_response(resp)
    assert text_parts == ["thinking"]
    assert tool_calls[0]["name"] == "bash_exec"
    assert tool_calls[0]["input"] == {"command": "ls"}


def test_run_loop_completes_when_no_tool_calls():
    log = RunLog(task_id="t", agent_type="handroll")
    seq = [_fake_resp(text="all done", tool_calls=[])]
    with patch("handroll.loop.loop.chat", side_effect=seq) as mc, \
         patch("handroll.loop.loop.Evaluator"):
        result_log = run_loop(_task(), "sys", log, max_turns=5)
    assert result_log.success is True
    assert result_log.stop_reason == "task_complete"
    assert result_log.final_answer == "all done"
    assert mc.call_count == 1


def test_run_loop_executes_then_completes():
    log = RunLog(task_id="t", agent_type="handroll")
    tool_call_mock = MagicMock(
        id="1", type="function",
        function=MagicMock(name="bash_exec", arguments='{"command": "echo hi"}')
    )
    seq = [
        _fake_resp(text="thinking", tool_calls=[tool_call_mock]),
        _fake_resp(text="done", tool_calls=[]),
    ]
    with patch("handroll.loop.loop.chat", side_effect=seq), \
         patch("handroll.loop.loop.Evaluator"):
        result_log = run_loop(_task(), "sys", log, max_turns=5)
    assert result_log.success is True
    assert len(result_log.tool_calls) == 1
    assert result_log.tool_calls[0]["name"] == "bash_exec"


def test_run_loop_respects_max_turns():
    log = RunLog(task_id="t", agent_type="handroll")
    tool_call_mock = MagicMock(
        id="1", type="function",
        function=MagicMock(name="bash_exec", arguments='{"command": "true"}')
    )
    # Always returns a tool call — never completes
    seq = [_fake_resp(tool_calls=[tool_call_mock]) for _ in range(20)]
    with patch("handroll.loop.loop.chat", side_effect=seq), \
         patch("handroll.loop.loop.Evaluator") as MockEv:
        # Make Evaluator trigger max_turns at turn 3
        MockEv.return_value.should_stop.side_effect = [
            (False, ""),
            (False, ""),
            (True, "max_turns"),
        ]
        result_log = run_loop(_task(), "sys", log, max_turns=3)
    assert result_log.success is False
    assert result_log.stop_reason == "max_turns"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_loop.py -v
```

Expected: ImportError (`handroll.loop.loop` doesn't exist yet).

- [ ] **Step 3: Implement loop.py**

Create `handroll/loop/loop.py`:

```python
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
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_loop.py -v
```

Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add handroll/loop/loop.py tests/test_loop.py
git commit -m "feat(loop): core 6-step agent loop with parse_response"
```

---

## Task 14: `tasks/task_base.py` + `tasks/benchmark/task_01_simple_script.py`

**Files:**
- Create: `tasks/task_base.py`
- Create: `tasks/benchmark/task_01_simple_script.py`
- Modify: `tasks/__init__.py` (add TASKS registry)
- Test: `tests/test_task_01.py`

**Interfaces:**
- Produces: `Task` dataclass with `id/prompt/success_criterion/sandbox_seed`; `TASKS: dict[str, Task]` registry in `tasks/__init__.py`

- [ ] **Step 1: Write failing test**

Create `tests/test_task_01.py`:

```python
from tasks import TASKS
from tasks.benchmark.task_01_simple_script import TASK, success
from shared.utils.sandbox import SANDBOX_DIR, reset_sandbox


def setup_function():
    reset_sandbox()


def test_task_registered():
    assert "task_01_simple_script" in TASKS
    assert TASKS["task_01_simple_script"] is TASK


def test_success_false_when_no_file():
    reset_sandbox()
    assert success("any answer") is False


def test_success_true_when_hello_py_runs_hello_world():
    (SANDBOX_DIR / "hello.py").write_text("print('hello world')\n", encoding="utf-8")
    assert success("any answer") is True


def test_success_false_when_output_wrong():
    (SANDBOX_DIR / "hello.py").write_text("print('goodbye')\n", encoding="utf-8")
    assert success("any answer") is False
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_task_01.py -v
```

Expected: ImportError.

- [ ] **Step 3: Implement task_base.py**

Create `tasks/task_base.py`:

```python
"""Task 数据类 —— 两路共用的任务定义。

设计：
- prompt 是发给 agent 的自然语言指令
- success_criterion 接收 final_answer 字符串，返回 bool
  （内部可直接检查 sandbox/ 文件系统状态，不经过 sandbox 守卫）
- sandbox_seed 在 run 前预置文件（Week 1 暂未用到）

【和 DeepAgent 的对比】（Task 18 补全）
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable


@dataclass
class Task:
    id: str
    prompt: str
    success_criterion: Callable[[str], bool]
    sandbox_seed: list[tuple[str, str]] = field(default_factory=list)
```

- [ ] **Step 4: Implement task_01_simple_script.py**

Create `tasks/benchmark/task_01_simple_script.py`:

```python
"""task_01_simple_script —— Week 1 验收任务。

任务：让 agent 在 sandbox/ 下创建 hello.py 并运行验证输出。

注意：success_criterion 直接操作磁盘（不经 sandbox 守卫），
因为它是评估代码而非 agent 代码。

【和 DeepAgent 的对比】（Task 18 补全）
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from shared.utils.sandbox import SANDBOX_DIR
from tasks.task_base import Task


def success(final_answer: str) -> bool:
    """(a) sandbox/hello.py 存在；(b) 运行后 stdout 含 'hello world'。"""
    hello_py: Path = SANDBOX_DIR / "hello.py"
    if not hello_py.exists():
        return False
    try:
        result = subprocess.run(
            [sys.executable, str(hello_py)],
            capture_output=True,
            timeout=5,
        )
    except subprocess.TimeoutExpired:
        return False
    return b"hello world" in result.stdout.lower()


TASK = Task(
    id="task_01_simple_script",
    prompt=(
        "请在当前工作目录下创建一个名为 hello.py 的 Python 文件，"
        "内容为：打印字符串 'hello world'。"
        "创建完成后，运行该文件验证输出正确。"
    ),
    success_criterion=success,
)
```

- [ ] **Step 5: Implement tasks/__init__.py registry**

Overwrite `tasks/__init__.py`:

```python
from tasks.benchmark.task_01_simple_script import TASK as _TASK_01

TASKS = {
    "task_01_simple_script": _TASK_01,
}

__all__ = ["TASKS"]
```

- [ ] **Step 6: Run test to verify it passes**

```bash
pytest tests/test_task_01.py -v
```

Expected: 4 passed.

Also re-run `tests/test_loop.py` to confirm the Task dataclass matches what loop expects — `_StubTask` in that test mirrors Task's shape, so it should still pass:

```bash
pytest tests/test_loop.py -v
```

Expected: still 4 passed.

- [ ] **Step 7: Commit**

```bash
git add tasks/ tests/test_task_01.py
git commit -m "feat(tasks): Task dataclass + task_01_simple_script + TASKS registry"
```

---

## Task 15: `handroll/agent.py` — orchestrator

**Files:**
- Create: `handroll/agent.py`

**Interfaces:**
- Consumes: `run_loop`, `Task`, `RunLog`, `REACT_SYSTEM_PROMPT` defined inline
- Produces: `run(task: Task) -> RunLog`

- [ ] **Step 1: Implement agent.py** (no unit test — orchestration glue; verified by end-to-end run in Task 18)

Create `handroll/agent.py`:

```python
"""handroll Code Agent 入口 —— 组装 task + loop + RunLog。

设计：
- REACT_SYSTEM_PROMPT 在此定义（Week 3 会参数化为 cot/react/plan_and_execute）
- 单一入口 run(task) -> RunLog，被 cli.py 调用

【和 DeepAgent 的对比】（Task 18 补全）
"""
from __future__ import annotations

import time

from handroll.loop.loop import run_loop
from shared.tracker.run_logger import RunLog
from tasks.task_base import Task

REACT_SYSTEM_PROMPT = """你是一个 Code Agent。你可以调用工具来完成任务。
策略（ReAct）：
1. 思考任务下一步该做什么
2. 如有必要，调用一个或多个工具
3. 观察工具结果
4. 重复直至任务完成，然后给出最终答案

所有文件操作被限制在当前工作目录（sandbox/）。"""


def run(task: Task) -> RunLog:
    run_log = RunLog(
        task_id=task.id,
        agent_type="handroll",
        planner_strategy="react",
    )
    start = time.time()
    run_log = run_loop(task, REACT_SYSTEM_PROMPT, run_log, max_turns=15)
    run_log.duration_s = round(time.time() - start, 3)
    path = run_log.save()
    return run_log
```

- [ ] **Step 2: Smoke check**

```bash
python -c "from handroll.agent import run; print('ok')"
```

Expected: prints `ok`.

- [ ] **Step 3: Commit**

```bash
git add handroll/agent.py
git commit -m "feat(handroll.agent): orchestrator with REACT system prompt"
```

---

## Task 16: `cli.py` — unified entrypoint

**Files:**
- Create: `cli.py`

**Interfaces:**
- Produces: argparse CLI with subcommands `run` and `tasks`

- [ ] **Step 1: Implement cli.py**

Create `cli.py`:

```python
"""统一 CLI 入口。

用法：
  python -m cli run --agent handroll --task task_01_simple_script
  python -m cli run --agent deepagent --task task_01_simple_script
  python -m cli run --agent both    --task task_01_simple_script
  python -m cli tasks
"""
from __future__ import annotations

import argparse
import sys

from rich.console import Console
from rich.table import Table

from shared.utils.sandbox import reset_sandbox
from tasks import TASKS


def _run_one(agent_name: str, task):
    reset_sandbox()
    if agent_name == "handroll":
        from handroll.agent import run as agent_run
    elif agent_name == "deepagent":
        from deepagent.agent import run as agent_run
    else:
        raise ValueError(f"unknown agent: {agent_name}")
    return agent_run(task)


def cmd_run(args):
    if args.task not in TASKS:
        print(f"unknown task: {args.task}", file=sys.stderr)
        sys.exit(2)
    task = TASKS[args.task]
    agents = ["handroll", "deepagent"] if args.agent == "both" else [args.agent]

    logs = []
    for ag in agents:
        print(f"\n=== running {ag} on {task.id} ===")
        try:
            log = _run_one(ag, task)
        except Exception as e:
            print(f"[{ag}] FAILED: {type(e).__name__}: {e}", file=sys.stderr)
            continue
        logs.append((ag, log))

    if logs:
        _print_table(logs)


def _print_table(logs):
    console = Console()
    table = Table(title="Run Summary")
    table.add_column("agent")
    table.add_column("success")
    table.add_column("turns")
    table.add_column("in_tokens")
    table.add_column("out_tokens")
    table.add_column("duration_s")
    for ag, log in logs:
        table.add_row(
            ag,
            str(log.success),
            str(log.loop_turns),
            str(log.total_input_tokens),
            str(log.total_output_tokens),
            f"{log.duration_s:.2f}",
        )
    console.print(table)


def cmd_tasks(args):
    print("Available tasks:")
    for tid, t in TASKS.items():
        print(f"  - {tid}: {t.prompt[:60]}...")


def main(argv=None):
    parser = argparse.ArgumentParser(prog="loop-engineer")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_run = sub.add_parser("run", help="run an agent on a task")
    p_run.add_argument("--agent", required=True, choices=["handroll", "deepagent", "both"])
    p_run.add_argument("--task", required=True)
    p_run.set_defaults(func=cmd_run)

    p_tasks = sub.add_parser("tasks", help="list available tasks")
    p_tasks.set_defaults(func=cmd_tasks)

    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Smoke check**

```bash
python -m cli tasks
```

Expected output:

```
Available tasks:
  - task_01_simple_script: 请在当前工作目录下创建一个名为 hello.py 的 Python 文件...
```

```bash
python -m cli run --agent handroll --task task_01_simple_script
```

Expected: connects to LLM (per `.env`), runs the loop, writes RunLog JSON to `outputs/runs/`, prints summary table.

- [ ] **Step 3: Commit**

```bash
git add cli.py
git commit -m "feat(cli): unified run/tasks entrypoint with rich table"
```

---

## Task 17: `deepagent/agent.py` — deepagents wrapper

**Files:**
- Create: `deepagent/agent.py`

**Interfaces:**
- Consumes: `create_deep_agent` from `deepagents`, `ChatOpenAI`, `ALL_TOOLS_AS_CALLABLES`, `load_env`, `RunLog`, `Task`
- Produces: `run(task: Task) -> RunLog`

- [ ] **Step 1: Implement deepagent/agent.py**

Create `deepagent/agent.py`:

```python
"""deepagent Code Agent —— LangChain deepagents 库的极薄包装。

设计：
- 共享 handroll 路的工具（ALL_TOOLS_AS_CALLABLES）保证对比公平
- 共享 REACT 风格 system prompt（与 handroll.agent 等价语义）
- 默认启用 deepagents 的 write_todos / planning，作为额外 tool_call 记录
- 通过 agent.stream(stream_mode="updates") 事件流重构 RunLog

【和 DeepAgent 的对比】（Task 18 补全）
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
```

- [ ] **Step 2: Smoke check (deepagent path requires LLM credentials)**

```bash
python -m cli run --agent deepagent --task task_01_simple_script
```

Expected: connects to LLM, deepagents streams events, RunLog JSON saved to `outputs/runs/`, summary table printed.

If `deepagents` import fails, follow the error message instructions (ensure `pip install -e ".[dev]"` picked up the package).

- [ ] **Step 3: Commit**

```bash
git add deepagent/agent.py
git commit -m "feat(deepagent): deepagents wrapper with event-stream RunLog"
```

---

## Task 18: End-to-end comparison + comparison docstrings

**Files:**
- Modify: `shared/utils/config.py`, `shared/utils/sandbox.py`, `shared/utils/llm_client.py`, `shared/tracker/run_logger.py`, `shared/tools/{schemas,bash_exec,file_read,file_write}.py`, `handroll/{loop/loop,executor/executor,evaluator/evaluator,observation/formatter,agent}.py`, `tasks/benchmark/task_01_simple_script.py`, `deepagent/agent.py`

**Goal:** Run both paths on task_01, observe RunLogs side by side, then go back and fill in each core file's `【和 DeepAgent 的对比】` docstring section based on actual observations.

- [ ] **Step 1: Run both paths**

```bash
python -m cli run --agent both --task task_01_simple_script
```

Expected output: rich summary table with both rows; success=True for both (or note failures).

- [ ] **Step 2: Inspect the two RunLog JSONs**

```bash
ls outputs/runs/
# Pick the two most recent files (one handroll, one deepagent)
```

Compare:
- `loop_turns` ratio (deepagent should be ~2x)
- `total_input_tokens` / `total_output_tokens` (similar magnitude; deepagent may be higher if `write_todos` engaged)
- `tool_calls` list (deepagent may include `write_todos`)
- `notes` (each path annotates its own caveats)

- [ ] **Step 3: Write comparison docstrings**

For each file in the Files list above, replace the `【和 DeepAgent 的对比】（Task 18 补全）` placeholder with 2-4 lines of concrete observations. Use the table below as a starting point — adapt based on what you actually saw:

| handroll 文件 | 与 DeepAgent 的对比要点 |
|---|---|
| `shared/utils/llm_client.py` | DeepAgent 用 `langchain_openai.ChatOpenAI`；这边直接用 `openai` SDK。底层是同一个端点。 |
| `shared/tools/schemas.py` | 两路共享此处的 schema dict；DeepAgent 通过 `to_langchain_tool` 包装成 StructuredTool。 |
| `shared/utils/sandbox.py` | 沙箱是项目级共享，DeepAgent 也走同一份工具实现，路径限制一致。 |
| `shared/tracker/run_logger.py` | DeepAgent 不主动产出 RunLog；本文件是手工对齐口径的产物。 |
| `handroll/loop/loop.py` | DeepAgent 把整个 6 步循环隐藏在 `agent.stream()` 后面；这里每个步骤都是显式代码。 |
| `handroll/executor/executor.py` | DeepAgent 通过 `@tool` 装饰器 + ToolNode 自动调度；这里是手写 registry。 |
| `handroll/evaluator/evaluator.py` | DeepAgent 没有内置 Evaluator；终止全靠 LLM 自己说"完成"。 |
| `handroll/observation/formatter.py` | DeepAgent 自动把 ToolMessage 反馈给模型；这里手动 format + 追加 messages。 |
| `handroll/agent.py` | DeepAgent 的 `agent.py` 是 100 行；这里 30 行。差距在 loop/executor/evaluator/observation 的代码量。 |
| `tasks/benchmark/task_01_simple_script.py` | 任务定义两路共享，success_criterion 不依赖 agent 实现。 |
| `deepagent/agent.py` | 这里 `_ingest_event` 50 行做的事，handroll 是在 loop.py 里直接累加。 |

For each docstring, replace the placeholder line `【和 DeepAgent 的对比】（Task 18 补全）` with:

```python
【和 DeepAgent 的对比】
- DeepAgent 用 ___；这里 ___。
- 关键观察：___（来自 Step 2 的 RunLog 对比）。
```

- [ ] **Step 4: Verify all docstrings are filled (no remaining placeholders)**

Search for any remaining `Task 18 补全` placeholder:

```bash
grep -rn "Task 18 补全" --include="*.py" .
```

Expected: no matches.

- [ ] **Step 5: Run full test suite**

```bash
pytest -v
```

Expected: all tests still pass.

- [ ] **Step 6: Commit**

```bash
git add -A
git commit -m "docs: fill in DeepAgent comparison docstrings across core files"
```

---

## Final Verification Checklist

After Task 18 completes, verify against spec Section 10:

- [ ] `pip install -e ".[dev]"` succeeds on a clean clone
- [ ] `cp .env.example .env` + filled-in LLM config → CLI runs
- [ ] `python -m cli run --agent handroll --task task_01_simple_script` → success, `sandbox/hello.py` exists and runs
- [ ] `python -m cli run --agent deepagent --task task_01_simple_script` → same
- [ ] Both runs produce RunLog JSON in `outputs/runs/`
- [ ] `python -m cli run --agent both --task task_01_simple_script` prints side-by-side table
- [ ] Every core file has `【和 DeepAgent 的对比】` docstring section (no `Task 18 补全` placeholders remain)
- [ ] `pytest -v` is all green
