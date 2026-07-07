"""OpenAI 兼容 chat 客户端 —— handroll 路直接使用。

deepagent 路不直接用此客户端，而是构造一个配置了相同 base_url/api_key/model
的 langchain_openai.ChatOpenAI 实例。

设计：
- 模块级 _client 单例（首次 chat() 时 lazy init）
- tools 参数透传给 OpenAI tools API
- 返回 (response, input_tokens, output_tokens)，token 从 response.usage 提取

【和 DeepAgent 的对比】（Task 18 补全）
"""
from __future__ import annotations

from typing import Any

from openai import OpenAI

from shared.utils.config import load_env

_client: OpenAI | None = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        cfg = load_env()
        _client = OpenAI(base_url=cfg.LLM_BASE_URL, api_key=cfg.LLM_API_KEY)
    return _client


def _to_openai_tools(schemas: list[dict]) -> list[dict]:
    return [
        {
            "type": "function",
            "function": {
                "name": s["name"],
                "description": s["description"],
                "parameters": s["input_schema"],
            },
        }
        for s in schemas
    ]


def chat(
    messages: list[dict],
    system: str,
    tools: list[dict],
    max_tokens: int = 1024,
) -> tuple[Any, int, int]:
    """OpenAI 兼容 chat 调用。返回 (response, input_tokens, output_tokens)。"""
    client = _get_client()
    cfg = load_env()
    full_messages = [{"role": "system", "content": system}] + messages
    kwargs: dict[str, Any] = {
        "model": cfg.LLM_MODEL,
        "messages": full_messages,
        "max_tokens": max_tokens,
    }
    if tools:
        kwargs["tools"] = _to_openai_tools(tools)
    resp = client.chat.completions.create(**kwargs)
    in_tok = getattr(resp.usage, "prompt_tokens", 0) if resp.usage else 0
    out_tok = getattr(resp.usage, "completion_tokens", 0) if resp.usage else 0
    return resp, in_tok, out_tok
