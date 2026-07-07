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
