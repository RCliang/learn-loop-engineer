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

# 方案 A（v2）：相对路径模式。
#
# 两路 prompt 保持语义一致（单一变量纪律）：
# - deepagent 用虚拟路径（/hello.py）—— FilesystemMiddleware 会 validate_path
# - handroll 用相对路径（hello.py）—— resolve_in_sandbox() 拼到 SANDBOX_DIR
# 两者最终都落到 sandbox/hello.py，只是路径表达形式不同。
# 这是工具层语义差异所致，prompt 的核心指令相同。

REACT_SYSTEM_PROMPT = """你是一个 Code Agent。你可以调用工具来完成任务。
策略（ReAct）：
1. 思考任务下一步该做什么
2. 如有必要，调用一个或多个工具
3. 观察工具结果
4. 重复直至任务完成，然后给出最终答案

所有文件操作都针对当前工作目录。
文件路径请使用相对路径，例如：
- hello.py 表示工作目录下的 hello.py
- scripts/run.py 表示工作目录下 scripts/run.py

执行 shell 命令时，当前工作目录已经是工作目录，直接用文件名即可（如 python hello.py）。"""


def run(task: Task) -> RunLog:
    run_log = RunLog(
        task_id=task.id,
        agent_type="handroll",
        planner_strategy="react",
    )
    run_log.system_prompt = REACT_SYSTEM_PROMPT
    start = time.time()
    run_log = run_loop(task, REACT_SYSTEM_PROMPT, run_log, max_turns=15)
    run_log.duration_s = round(time.time() - start, 3)
    path = run_log.save()
    return run_log
