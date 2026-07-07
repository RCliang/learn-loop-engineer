"""Task 数据类 —— 两路共用的任务定义。

设计：
- prompt 是发给 agent 的自然语言指令
- success_criterion 接收 final_answer 字符串，返回 bool
  （内部可直接检查 sandbox/ 文件系统状态，不经过 sandbox 守卫）
- sandbox_seed 在 run 前预置文件（Week 1 暂未用到）

【和 DeepAgent 的对比】
- DeepAgent 使用同一套 Task 数据类；prompt 和 success_criterion 定义共享。
- 关键观察：任务抽象层完全共享，确保两路对比的公平性。
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
