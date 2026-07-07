"""沙箱路径守卫 —— 把所有文件操作限制在项目根的 sandbox/ 目录下。

设计权衡：
- 主防线是路径 resolve 后的前缀检查（防 `../` 逃逸）
- bash_exec 用 cwd=sandbox/ 启动子进程（不能完全阻止绝对路径访问，已知限制）
- 完整容器隔离留给 Phase 3

【和 DeepAgent 的对比】（Task 18 补全）
"""
from __future__ import annotations

import shutil
from pathlib import Path

SANDBOX_DIR: Path = Path(__file__).resolve().parents[2] / "sandbox"


def resolve_in_sandbox(rel_or_abs_path: str) -> Path:
    """把用户提供的路径解析为 SANDBOX_DIR 下的绝对路径。
    解析后若不在 SANDBOX_DIR 子树内，抛 PermissionError。"""
    p = Path(rel_or_abs_path)
    if not p.is_absolute():
        p = SANDBOX_DIR / p
    resolved = p.resolve()
    try:
        resolved.relative_to(SANDBOX_DIR)
    except ValueError:
        raise PermissionError(
            f"path '{rel_or_abs_path}' resolves outside sandbox: {resolved}"
        )
    return resolved


def reset_sandbox() -> None:
    """清空 sandbox/ 目录（保留 .gitkeep）。"""
    SANDBOX_DIR.mkdir(parents=True, exist_ok=True)
    for p in SANDBOX_DIR.iterdir():
        if p.name == ".gitkeep":
            continue
        if p.is_dir():
            shutil.rmtree(p)
        else:
            p.unlink()
