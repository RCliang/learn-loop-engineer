"""file_read 工具 —— 读取工作区内的文件。

设计：
- 相对路径锚定到 SANDBOX_DIR（见 resolve_in_sandbox）
- 失败（文件不存在 / OS 错误）返回错误 payload，不抛异常

注：resolve_in_sandbox 不做路径拦截，绝对路径原样透传。
"""
from __future__ import annotations

from shared.utils.sandbox import resolve_in_sandbox


def run(path: str, encoding: str = "utf-8") -> dict:
    try:
        resolved = resolve_in_sandbox(path)
        if not resolved.exists():
            return {
                "ok": False,
                "error_type": "FileNotFoundError",
                "message": f"文件不存在：{path}",
            }
        content = resolved.read_text(encoding=encoding)
        lines = content.count("\n") + (0 if content.endswith("\n") or content == "" else 1)
        return {
            "ok": True,
            "path": str(resolved),
            "content": content,
            "lines": lines,
        }
    except Exception as e:
        return {
            "ok": False,
            "error_type": type(e).__name__,
            "message": str(e),
        }
