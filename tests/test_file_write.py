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
