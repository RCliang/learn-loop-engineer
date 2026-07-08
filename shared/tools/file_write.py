"""file_write 工具 —— 写入工作区内文件。

设计：
- 自动创建父目录
- 已存在文件直接覆盖
- 相对路径锚定到 SANDBOX_DIR（见 resolve_in_sandbox）

注：resolve_in_sandbox 不做路径拦截，绝对路径原样透传。
"""
from __future__ import annotations

from shared.utils.sandbox import resolve_in_sandbox


def run(path: str, content: str, encoding: str = "utf-8") -> dict:
    try:
        resolved = resolve_in_sandbox(path)
        resolved.parent.mkdir(parents=True, exist_ok=True)
        data = content.encode(encoding)
        resolved.write_bytes(data)
        return {
            "ok": True,
            "path": str(resolved),
            "bytes": len(data),
        }
    except Exception as e:
        return {
            "ok": False,
            "error_type": type(e).__name__,
            "message": str(e),
        }
