"""Tests never call Gemini: the LLM is switched off unless a test plugs in a fake one."""
import pytest

from saathi import llm


@pytest.fixture(autouse=True)
def llm_off(monkeypatch, tmp_path):
    monkeypatch.setenv("SAATHI_LLM", "off")
    monkeypatch.setattr(llm, "LOG_FILE", tmp_path / "llm_calls.jsonl")   # keep test calls out of real logs
    monkeypatch.setattr(llm, "_cooldown_until", 0.0)
