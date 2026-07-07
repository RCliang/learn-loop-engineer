"""bash_exec 工具 —— 在沙箱工作目录中执行 shell 命令。

设计：
- 子进程 cwd 设为 sandbox/
- 超时默认 30s；超时返回错误 payload（不抛异常）
- Windows 下使用 cmd.exe；其他平台使用 /bin/bash

已知限制：cwd 限制无法阻止 LLM 通过绝对路径访问沙箱外文件。
Phase 3 会引入容器隔离。

【和 DeepAgent 的对比】
- DeepAgent 调用同一份 bash_exec.run() 工具；沙箱限制完全一致。
- 关键观察：两路的命令执行都在 sandbox/ 目录内，超时默认 30 秒。
"""
from __future__ import annotations

import subprocess
import sys
import time

from shared.utils.sandbox import SANDBOX_DIR


def run(command: str, timeout: int = 30) -> dict:
    start = time.time()
    try:
        if sys.platform.startswith("win"):
            proc = subprocess.run(
                command,
                cwd=str(SANDBOX_DIR),
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
        else:
            proc = subprocess.run(
                ["bash", "-c", command],
                cwd=str(SANDBOX_DIR),
                capture_output=True,
                text=True,
                timeout=timeout,
            )
        duration = time.time() - start
        ok = proc.returncode == 0
        return {
            "ok": ok,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
            "exit_code": proc.returncode,
            "duration_s": round(duration, 3),
        }
    except subprocess.TimeoutExpired as e:
        return {
            "ok": False,
            "error_type": "TimeoutExpired",
            "message": f"超时 {timeout}s",
            "stdout": e.stdout or "" if isinstance(e.stdout, str) else "",
            "stderr": e.stderr or "" if isinstance(e.stderr, str) else "",
            "exit_code": -1,
            "duration_s": round(time.time() - start, 3),
        }
