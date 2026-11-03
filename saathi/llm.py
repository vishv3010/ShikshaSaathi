"""Gemini, called over plain HTTPS (no extra dependency).

The LLM has two jobs only (PLAN.md section 1): read a question the rules could
not place, and word a reply from a draft the code wrote from computed facts.
Every failure (no key, switched off, timeout, quota, cut-off or empty output)
raises LLMError, and the caller falls back to the rule-based answer (D-009).

Settings (environment or a local .env file, which git ignores):
    GEMINI_API_KEY   the key; without it the app runs on rules only
    GEMINI_MODEL     default gemini-3.5-flash-lite
    SAATHI_LLM       "off" switches the LLM off (tests do this)
"""
import json
import os
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
API = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
DEFAULT_MODEL = "gemini-3.5-flash-lite"
COOLDOWN_SECONDS = 60      # after a quota error, use rules for a minute instead of retrying
LOG_FILE = ROOT / "logs" / "llm_calls.jsonl"

_env_loaded = False
_cooldown_until = 0.0


class LLMError(Exception):
    """Any reason the LLM could not give a usable answer; the caller falls back to rules."""


def load_env(path=ROOT / ".env"):
    """Read KEY=value lines from .env once. Real environment variables win."""
    global _env_loaded
    if _env_loaded:
        return
    _env_loaded = True
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ.setdefault(key.strip(), value.strip().strip("'\""))


def model_name():
    load_env()
    return os.environ.get("GEMINI_MODEL", DEFAULT_MODEL)


def enabled():
    load_env()
    return bool(os.environ.get("GEMINI_API_KEY")) and os.environ.get("SAATHI_LLM", "on").lower() != "off"


def generate(prompt, system, *, schema=None, max_tokens=1500, timeout=20):
    """One Gemini call. Returns {text, model, seconds, tokens_in, tokens_out}; raises LLMError."""
    global _cooldown_until
    if not enabled():
        raise LLMError("switched_off" if os.environ.get("GEMINI_API_KEY") else "no_key")
    if time.time() < _cooldown_until:
        raise LLMError("cooling_down")

    model = model_name()
    config = {"maxOutputTokens": max_tokens, "temperature": 0.2}
    if schema:
        config.update(responseMimeType="application/json", responseSchema=schema)
    body = {"systemInstruction": {"parts": [{"text": system}]},
            "contents": [{"role": "user", "parts": [{"text": prompt}]}],
            "generationConfig": config}
    request = urllib.request.Request(
        API.format(model=model), data=json.dumps(body).encode("utf-8"), method="POST",
        headers={"x-goog-api-key": os.environ["GEMINI_API_KEY"], "Content-Type": "application/json"})

    start = time.time()
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            data = json.load(response)
    except urllib.error.HTTPError as error:
        if error.code == 429:
            _cooldown_until = time.time() + COOLDOWN_SECONDS
        raise LLMError(f"http_{error.code}") from error
    except (urllib.error.URLError, OSError, ValueError) as error:   # network, timeout, bad JSON
        raise LLMError(f"network: {type(error).__name__}") from error

    try:
        candidate = data["candidates"][0]
        text = "".join(part.get("text", "") for part in candidate["content"]["parts"]).strip()
    except (KeyError, IndexError, TypeError) as error:
        raise LLMError("empty_response") from error
    if candidate.get("finishReason", "STOP") != "STOP":
        raise LLMError(f"finish_{candidate.get('finishReason')}")   # e.g. cut off at MAX_TOKENS
    if not text:
        raise LLMError("empty_text")
    usage = data.get("usageMetadata", {})
    return {"text": text, "model": model, "seconds": round(time.time() - start, 2),
            "tokens_in": usage.get("promptTokenCount", 0),
            "tokens_out": usage.get("candidatesTokenCount", 0) + (usage.get("thoughtsTokenCount") or 0)}


def log_call(record):
    """Append one LLM call to logs/llm_calls.jsonl (question, outcome, tokens; never the key)."""
    try:
        LOG_FILE.parent.mkdir(exist_ok=True)
        record = {"at": datetime.now(timezone.utc).isoformat(timespec="seconds"), **record}
        with LOG_FILE.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except OSError:
        pass   # logging must never break an answer
