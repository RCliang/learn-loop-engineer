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
