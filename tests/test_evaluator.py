from unittest.mock import patch, MagicMock
from handroll.evaluator.evaluator import Evaluator


def test_max_turns_returns_stop():
    ev = Evaluator(max_turns=3)
    stop, reason = ev.should_stop(task="x", last_response="y", current_turn=3, last_action=None)
    assert stop is True
    assert reason == "max_turns"


def test_max_turns_not_reached():
    ev = Evaluator(max_turns=3)
    with patch("handroll.evaluator.evaluator.chat") as mock_chat:
        mock_chat.return_value = (MagicMock(choices=[MagicMock(message=MagicMock(content="INCOMPLETE"))]), 0, 0)
        stop, _ = ev.should_stop(task="x", last_response="y", current_turn=1, last_action=None)
    assert stop is False


def test_loop_detection_after_three_same_actions():
    ev = Evaluator(max_turns=10)
    action = {"name": "bash_exec", "input": {"command": "ls"}}
    with patch("handroll.evaluator.evaluator.chat") as mock_chat:
        mock_chat.return_value = (MagicMock(choices=[MagicMock(message=MagicMock(content="INCOMPLETE"))]), 0, 0)
        ev.should_stop("x", "y", 1, action)
        ev.should_stop("x", "y", 2, action)
        stop, reason = ev.should_stop("x", "y", 3, action)
    assert stop is True
    assert reason == "loop_detected"


def test_self_critique_complete():
    ev = Evaluator(max_turns=10)
    with patch("handroll.evaluator.evaluator.chat") as mock_chat:
        mock_chat.return_value = (MagicMock(choices=[MagicMock(message=MagicMock(content="COMPLETE: done"))]), 0, 0)
        stop, reason = ev.should_stop(task="x", last_response="done", current_turn=1, last_action=None)
    assert stop is True
    assert reason == "task_complete"
