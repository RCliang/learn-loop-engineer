"""task_01_simple_script —— Week 1 验收任务。

任务：让 agent 在 sandbox/ 下创建 hello.py 并运行验证输出。

注意：success_criterion 直接操作磁盘（不经 sandbox 守卫），
因为它是评估代码而非 agent 代码。

【和 DeepAgent 的对比】
- 任务定义两路共享，success_criterion 不依赖 agent 实现。
- 关键观察：相同的任务定义确保两路对比的公平性。
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from shared.utils.sandbox import SANDBOX_DIR
from tasks.task_base import Task


def success(final_answer: str) -> bool:
    """(a) sandbox/hello.py 存在；(b) 运行后 stdout 含 'hello world'。"""
    hello_py: Path = SANDBOX_DIR / "hello.py"
    if not hello_py.exists():
        return False
    try:
        result = subprocess.run(
            [sys.executable, str(hello_py)],
            capture_output=True,
            timeout=5,
        )
    except subprocess.TimeoutExpired:
        return False
    return b"hello world" in result.stdout.lower()


TASK = Task(
    id="task_01_simple_script",
    prompt=(
        "请在当前工作目录下创建一个名为 hello.py 的 Python 文件，"
        "内容为：打印字符串 'hello world'。"
        "创建完成后，运行该文件验证输出正确。"
    ),
    success_criterion=success,
)
