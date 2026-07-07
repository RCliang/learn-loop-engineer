from tasks import TASKS
from tasks.benchmark.task_01_simple_script import TASK, success
from shared.utils.sandbox import SANDBOX_DIR, reset_sandbox


def test_task_registered():
    assert "task_01_simple_script" in TASKS
    assert TASKS["task_01_simple_script"] is TASK


def test_success_false_when_no_file():
    reset_sandbox()
    assert success("any answer") is False


def test_success_true_when_hello_py_runs_hello_world():
    (SANDBOX_DIR / "hello.py").write_text("print('hello world')\n", encoding="utf-8")
    assert success("any answer") is True


def test_success_false_when_output_wrong():
    (SANDBOX_DIR / "hello.py").write_text("print('goodbye')\n", encoding="utf-8")
    assert success("any answer") is False
