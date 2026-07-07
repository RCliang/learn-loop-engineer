"""LLM 配置加载 —— OpenAI 兼容端点的统一入口。

【和 DeepAgent 的对比】（Task 18 补全）
"""
from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class LLMConfig:
    LLM_BASE_URL: str
    LLM_API_KEY: str
    LLM_MODEL: str


_REQUIRED = ("LLM_BASE_URL", "LLM_API_KEY", "LLM_MODEL")


def load_env() -> LLMConfig:
    """从环境变量读取 LLM 配置。缺失则抛 RuntimeError。"""
    missing = [k for k in _REQUIRED if not os.getenv(k)]
    if missing:
        raise RuntimeError(f"missing env vars: {missing}")
    return LLMConfig(
        LLM_BASE_URL=os.environ["LLM_BASE_URL"],
        LLM_API_KEY=os.environ["LLM_API_KEY"],
        LLM_MODEL=os.environ["LLM_MODEL"],
    )
