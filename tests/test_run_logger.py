import json
from shared.tracker.run_logger import RunLog


def test_default_construction():
    log = RunLog(task_id="t1", agent_type="handroll")
    assert log.success is False
    assert log.tool_calls == []
    assert log.notes == []


def test_log_tool_call_appends():
    log = RunLog(task_id="t1", agent_type="handroll")
    log.log_tool_call("bash_exec", {"command": "ls"}, {"ok": True, "exit_code": 0})
    assert len(log.tool_calls) == 1
    assert log.tool_calls[0]["name"] == "bash_exec"
    assert log.tool_calls[0]["ok"] is True


def test_log_event_appends():
    log = RunLog(task_id="t1", agent_type="handroll")
    log.log_event(turn=1, kind="llm_call", input_tokens=10, output_tokens=5)
    assert log.events[0] == {
        "turn": 1, "kind": "llm_call", "input_tokens": 10, "output_tokens": 5
    }


def test_finish_sets_status():
    log = RunLog(task_id="t1", agent_type="handroll")
    log.finish(success=True, stop_reason="task_complete", final_answer="done")
    assert log.success is True
    assert log.stop_reason == "task_complete"
    assert log.final_answer == "done"


def test_save_writes_json(tmp_path):
    log = RunLog(task_id="t1", agent_type="handroll")
    log.finish(True, "task_complete", "hi")
    path = log.save(dir=str(tmp_path))
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["task_id"] == "t1"
    assert data["agent_type"] == "handroll"
    assert data["success"] is True
    assert "tool_calls" in data
