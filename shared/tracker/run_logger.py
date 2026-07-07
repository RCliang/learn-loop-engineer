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
