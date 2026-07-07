"""handroll Code Agent 入口 —— 组装 task + loop + RunLog。

设计：
- REACT_SYSTEM_PROMPT 在此定义（Week 3 会参数化为 cot/react/plan_and_execute）
- 单一入口 run(task) -> RunLog，被 cli.py 调用

【和 DeepAgent 的对比】
- DeepAgent 的 `agent.py` 是 100 行；这里 30 行。
- 关键观察：差距在 loop/executor/evaluator/observation 的代码量——这里模块化更彻底。
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
