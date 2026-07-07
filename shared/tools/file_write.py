"""file_write 工具 —— 写入沙箱内文件。

设计：
- 自动创建父目录
- 已存在文件直接覆盖
- 通过 resolve_in_sandbox 强制路径在 sandbox/ 子树内

【和 DeepAgent 的对比】
- DeepAgent 调用同一份 file_write.run() 工具；路径守卫完全一致。
- 关键观察：两路的文件写入都经过 resolve_in_sandbox 验证路径安全性。
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
