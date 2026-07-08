"""沙箱工作区 —— agent 的统一工作目录与运行间清理。

这不是安全边界，只是工作区约定：
- SANDBOX_DIR 是一个普通目录，agent 工具默认把相对路径锚定到这里
- reset_sandbox 在每次 run 前清空，保证实验可重复
- bash_exec 把子进程 cwd 设到这里，让相对命令"能用"

历史上这里曾有一个路径前缀检查（防 `../` 逃逸），但它是自愿式的：
只有 file_read/file_write 调它，bash_exec 的绝对路径和 deepagents 内置工具
都能绕过。装样子不如不装，已移除。如需真隔离，应上容器 / namespaces。
"""
from __future__ import annotations

import shutil
from pathlib import Path

SANDBOX_DIR: Path = Path(__file__).resolve().parents[2] / "sandbox"


def resolve_in_sandbox(rel_or_abs_path: str) -> Path:
    """把路径解析为 SANDBOX_DIR 下的绝对路径。
    相对路径前置 SANDBOX_DIR；绝对路径原样返回（不做任何拦截）。"""
    p = Path(rel_or_abs_path)
    if not p.is_absolute():
        p = SANDBOX_DIR / p
    return p.resolve()


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
