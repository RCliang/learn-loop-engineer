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
    original_run = exec_mod.bash_exec.run
    original_registry = exec_mod.TOOL_REGISTRY["bash_exec"]
    exec_mod.bash_exec.run = lambda **kw: (_ for _ in ()).throw(RuntimeError("boom"))
    exec_mod.TOOL_REGISTRY["bash_exec"] = exec_mod.bash_exec.run
    try:
        result = execute_tool("bash_exec", {"command": "x"}, log)
    finally:
        exec_mod.bash_exec.run = original_run
        exec_mod.TOOL_REGISTRY["bash_exec"] = original_registry
    assert result["ok"] is False
    assert result["error_type"] == "RuntimeError"
