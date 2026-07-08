from shared.tools.file_read import run
from shared.utils.sandbox import SANDBOX_DIR


def test_read_existing_file():
    (SANDBOX_DIR / "sample.txt").write_text("hello\nworld\n", encoding="utf-8")
    result = run(path="sample.txt")
    assert result["ok"] is True
    assert "hello" in result["content"]
    assert result["lines"] == 2


def test_read_missing_file():
    result = run(path="nope.txt")
    assert result["ok"] is False
    assert result["error_type"] == "FileNotFoundError"
