from __future__ import annotations
from dataclasses import dataclass
from unittest.mock import patch, MagicMock

from handroll.loop.loop import run_loop, parse_response
from shared.tracker.run_logger import RunLog


@dataclass
class _StubTask:
    """Mirror of tasks.task_base.Task shape; lets loop tests run before Task exists."""
    id: str
    prompt: str
    success_criterion: object


def _fake_resp(text="", tool_calls=None, in_tok=10, out_tok=5):
    msg = MagicMock()
    msg.content = text
    msg.tool_calls = tool_calls or []
    resp = MagicMock()
    resp.choices = [MagicMock(message=msg)]
    resp.usage = MagicMock(prompt_tokens=in_tok, completion_tokens=out_tok)
    return resp, in_tok, out_tok


def _task():
    return _StubTask(id="t1", prompt="do it", success_criterion=lambda x: True)


def test_parse_response_extracts_text_and_tool_calls():
    msg = MagicMock()
    msg.content = "thinking"
    func_mock = MagicMock()
    func_mock.name = "bash_exec"
    func_mock.arguments = '{"command": "ls"}'
    msg.tool_calls = [
        MagicMock(id="1", type="function", function=func_mock)
    ]
    resp = MagicMock()
    resp.choices = [MagicMock(message=msg)]
    text_parts, tool_calls = parse_response(resp)
    assert text_parts == ["thinking"]
    assert tool_calls[0]["name"] == "bash_exec"
    assert tool_calls[0]["input"] == {"command": "ls"}


def test_run_loop_completes_when_no_tool_calls():
    log = RunLog(task_id="t", agent_type="handroll")
    seq = [_fake_resp(text="all done", tool_calls=[])]
    with patch("handroll.loop.loop.chat", side_effect=seq) as mc, \
         patch("handroll.loop.loop.Evaluator"):
        result_log = run_loop(_task(), "sys", log, max_turns=5)
    assert result_log.success is True
    assert result_log.stop_reason == "task_complete"
    assert result_log.final_answer == "all done"
    assert mc.call_count == 1


def test_run_loop_executes_then_completes():
    log = RunLog(task_id="t", agent_type="handroll")
    func_mock = MagicMock()
    func_mock.name = "bash_exec"
    func_mock.arguments = '{"command": "echo hi"}'
    tool_call_mock = MagicMock(
        id="1", type="function", function=func_mock
    )
    seq = [
        _fake_resp(text="thinking", tool_calls=[tool_call_mock]),
        _fake_resp(text="done", tool_calls=[]),
    ]
    with patch("handroll.loop.loop.chat", side_effect=seq), \
         patch("handroll.loop.loop.Evaluator") as MockEv:
        MockEv.return_value.should_stop.return_value = (False, "")
        result_log = run_loop(_task(), "sys", log, max_turns=5)
    assert result_log.success is True
    assert len(result_log.tool_calls) == 1
    assert result_log.tool_calls[0]["name"] == "bash_exec"


def test_run_loop_respects_max_turns():
    log = RunLog(task_id="t", agent_type="handroll")
    func_mock = MagicMock()
    func_mock.name = "bash_exec"
    func_mock.arguments = '{"command": "true"}'
    tool_call_mock = MagicMock(
        id="1", type="function", function=func_mock
    )
    # Always returns a tool call — never completes
    seq = [_fake_resp(tool_calls=[tool_call_mock]) for _ in range(20)]
    with patch("handroll.loop.loop.chat", side_effect=seq), \
         patch("handroll.loop.loop.Evaluator") as MockEv:
        # Make Evaluator trigger max_turns at turn 3
        MockEv.return_value.should_stop.side_effect = [
            (False, ""),
            (False, ""),
            (True, "max_turns"),
        ]
        result_log = run_loop(_task(), "sys", log, max_turns=3)
    assert result_log.success is False
    assert result_log.stop_reason == "max_turns"
