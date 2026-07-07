import os
from shared.utils.config import LLMConfig, load_env

def test_load_env_reads_three_keys(monkeypatch):
    monkeypatch.setenv("LLM_BASE_URL", "https://example.com/v1")
    monkeypatch.setenv("LLM_API_KEY", "sk-test")
    monkeypatch.setenv("LLM_MODEL", "gpt-test")
    cfg = load_env()
    assert cfg.LLM_BASE_URL == "https://example.com/v1"
    assert cfg.LLM_API_KEY == "sk-test"
    assert cfg.LLM_MODEL == "gpt-test"

def test_load_env_missing_key_raises(monkeypatch):
    # 隔离 .env 文件影响：把 load_dotenv 替换成 no-op，只测 os.environ 路径
    monkeypatch.setattr("shared.utils.config.load_dotenv", lambda *a, **kw: None)
    for k in ("LLM_BASE_URL", "LLM_API_KEY", "LLM_MODEL"):
        monkeypatch.delenv(k, raising=False)
    try:
        load_env()
    except RuntimeError:
        return
    raise AssertionError("expected RuntimeError on missing env")
