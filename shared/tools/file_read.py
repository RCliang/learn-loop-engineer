"""file_read 工具 —— 读取沙箱内的文件。

设计：
- 通过 resolve_in_sandbox 强制路径在 sandbox/ 子树内
- 失败（文件不存在 / 权限）返回错误 payload，不抛异常

【和 DeepAgent 的对比】
- DeepAgent 调用同一份 file_read.run() 工具；路径守卫完全一致。
- 关键观察：两路的文件读取都经过 resolve_in_sandbox 验证路径安全性。
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
    except PermissionError as e:
        return {
            "ok": False,
            "error_type": "PermissionError",
            "message": str(e),
        }
    except Exception as e:
        return {
            "ok": False,
            "error_type": type(e).__name__,
            "message": str(e),
        }
