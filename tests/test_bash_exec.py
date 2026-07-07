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
