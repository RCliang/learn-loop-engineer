from pathlib import Path
from shared.utils.sandbox import SANDBOX_DIR, resolve_in_sandbox, reset_sandbox


def test_sandbox_dir_is_real_dir():
    assert SANDBOX_DIR.exists()
    assert SANDBOX_DIR.is_dir()


def test_resolve_relative_path_inside_sandbox():
    resolved = resolve_in_sandbox("hello.py")
    assert resolved.parent == SANDBOX_DIR
    assert resolved.name == "hello.py"


def test_resolve_absolute_path_passes_through():
    # resolve_in_sandbox 不再拦截绝对路径，只做锚定 + resolve
    abs_path = str(SANDBOX_DIR / "sub" / "file.txt")
    resolved = resolve_in_sandbox(abs_path)
    assert resolved.is_relative_to(SANDBOX_DIR)


def test_reset_sandbox_clears_files():
    (SANDBOX_DIR / "leftover.txt").write_text("x")
    reset_sandbox()
    contents = [p for p in SANDBOX_DIR.iterdir() if p.name != ".gitkeep"]
    assert contents == []
