from unittest.mock import patch, MagicMock
from shared.utils.llm_client import chat


def _fake_response(text="ok", tool_calls=None, in_tok=10, out_tok=5):
    msg = MagicMock()
    msg.content = text
    msg.tool_calls = tool_calls or []
    resp = MagicMock()
    resp.choices = [MagicMock(message=msg)]
    resp.usage = MagicMock(prompt_tokens=in_tok, completion_tokens=out_tok)
    return resp


def test_chat_returns_response_and_tokens(monkeypatch):
    monkeypatch.setenv("LLM_BASE_URL", "https://x/v1")
    monkeypatch.setenv("LLM_API_KEY", "sk-x")
    monkeypatch.setenv("LLM_MODEL", "gpt-x")
    fake = _fake_response(in_tok=20, out_tok=7)
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = fake
    with patch("shared.utils.llm_client._get_client", return_value=mock_client):
        resp, in_tok, out_tok = chat(
            messages=[{"role": "user", "content": "hi"}],
            system="you are helpful",
            tools=[],
        )
    assert in_tok == 20
    assert out_tok == 7


def test_chat_passes_tools_through(monkeypatch):
    monkeypatch.setenv("LLM_BASE_URL", "https://x/v1")
    monkeypatch.setenv("LLM_API_KEY", "sk-x")
    monkeypatch.setenv("LLM_MODEL", "gpt-x")
    fake = _fake_response()
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = fake
    with patch("shared.utils.llm_client._get_client", return_value=mock_client):
        chat(
            messages=[{"role": "user", "content": "hi"}],
            system="s",
            tools=[{"name": "bash_exec", "description": "x", "input_schema": {}}],
        )
    call_kwargs = mock_client.chat.completions.create.call_args.kwargs
    assert "tools" in call_kwargs
