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
