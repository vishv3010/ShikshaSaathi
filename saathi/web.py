"""Web server: one chat page and one /ask endpoint (D-010).

The page is a single small HTML file with no external libraries, fonts or
images, for a basic Android phone on patchy 4G. POST /ask is the same call a
WhatsApp or SwiftChat webhook would make in production.

Run:  .venv/bin/uvicorn saathi.web:app --port 8000      then open http://localhost:8000
"""
import time
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel, Field

from . import llm
from .assistant import ask
from .data import load

PAGE = Path(__file__).resolve().parent.parent / "web" / "index.html"
MAX_QUESTION_CHARS = 500
RATE_LIMIT = 20       # questions per person per minute: enough for a real conversation,
RATE_WINDOW = 60      # too few to burn the free Gemini quota from one public link
PAGE_HEADERS = {
    "Cache-Control": "no-cache",
    # Only this page's own inline code runs; nothing is loaded from anywhere else.
    "Content-Security-Policy": "default-src 'self'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; "
                               "connect-src 'self'; img-src 'self' data:; base-uri 'none'; form-action 'none'",
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
}


@asynccontextmanager
async def lifespan(_app):
    load()   # read the CSVs once at start, so the first question is fast
    yield


app = FastAPI(title="Shiksha Saathi", docs_url=None, redoc_url=None, openapi_url=None, lifespan=lifespan)
app.add_middleware(GZipMiddleware, minimum_size=500)
_recent = defaultdict(deque)


class Question(BaseModel):
    question: str = Field(min_length=1, max_length=MAX_QUESTION_CHARS)
    lang: Literal["en", "gu", "hi"] | None = None
    school_id: str | None = Field(default=None, pattern=r"^GJ-C07-\d{3}$")
    test_checker: bool = False


def _client(request):
    """The person's address; behind a hosting proxy it is the first X-Forwarded-For entry."""
    forwarded = request.headers.get("x-forwarded-for", "")
    return forwarded.split(",")[0].strip() or (request.client.host if request.client else "unknown")


def _too_many(client):
    now, recent = time.time(), _recent[client]
    while recent and now - recent[0] > RATE_WINDOW:
        recent.popleft()
    if len(recent) >= RATE_LIMIT:
        return True
    recent.append(now)
    return False


@app.get("/")
def page():
    return FileResponse(PAGE, media_type="text/html; charset=utf-8", headers=PAGE_HEADERS)


@app.get("/favicon.ico")
def favicon():
    return Response(status_code=204)


@app.get("/health")
def health():
    data = load()
    return {"ok": True, "schools": len(data.schools), "latest_month": data.latest_month,
            "llm": llm.enabled(), "model": llm.model_name() if llm.enabled() else None}


@app.post("/ask")
def answer(body: Question, request: Request):
    if _too_many(_client(request)):
        raise HTTPException(status_code=429, detail="Too many questions in a minute; please wait a little.")
    r = ask(body.question, lang=body.lang, school_id=body.school_id, test_checker=body.test_checker)
    phrase = r["trace"].get("phrase") or {}
    checked = phrase.get("check") or {}
    return {
        "text": r["text"], "lang": r["lang"], "intent": r["intent"], "options": r["options"], "mode": r["mode"],
        # What the page shows under each answer: was AI wording used, and did the checker reject any?
        "check": {"ai_used": r["mode"] == "llm", "ai_tried": bool(phrase),
                  "rejected": bool(checked) and not phrase.get("ok"),
                  "unsupported": checked.get("unsupported", []), "number_words": checked.get("number_words", []),
                  "problem": phrase.get("problem"), "error": phrase.get("error"),
                  "test_checker": r["trace"].get("test_checker")},
    }
