"""Web server: one chat page and one /ask endpoint (D-010).

The page is a single small HTML file with no external libraries, fonts or
images, for a basic Android phone on patchy 4G. POST /ask is the same call a
WhatsApp or SwiftChat webhook would make in production.

Run:  .venv/bin/uvicorn saathi.web:app --port 8000      then open http://localhost:8000
"""
import os
import time
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel, Field

from . import analytics, llm, reply
from .assistant import ask
from .data import load

PAGE = Path(__file__).resolve().parent.parent / "web" / "index.html"
MAX_QUESTION_CHARS = 500
RATE_LIMIT = 20       # questions per person per minute: enough for a real conversation
RATE_WINDOW = 60
# The per-person limit can be dodged by sending a made-up X-Forwarded-For, so the Gemini quota is
# protected by a budget for the whole server: past it, answers carry on without AI wording.
AI_PER_MINUTE = int(os.environ.get("SAATHI_AI_PER_MINUTE", "15"))
AI_PER_DAY = int(os.environ.get("SAATHI_AI_PER_DAY", "800"))
SWEEP_EVERY = 200     # requests between clean-ups of the per-person memory
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
_ai_calls = deque()
_requests_seen = 0


class Question(BaseModel):
    question: str = Field(min_length=1, max_length=MAX_QUESTION_CHARS)
    lang: Literal["en", "gu", "hi"] | None = None
    school_id: str | None = Field(default=None, pattern=r"^GJ-C07-\d{3}$")
    test_checker: bool = False


def _client(request):
    """The person's address; behind a hosting proxy it is the first X-Forwarded-For entry."""
    forwarded = request.headers.get("x-forwarded-for", "")
    return forwarded.split(",")[0].strip() or (request.client.host if request.client else "unknown")


def _sweep(now):
    """Forget people with no question in the last window, so the memory cannot grow without end."""
    for client in [c for c, times in _recent.items() if not times or now - times[-1] > RATE_WINDOW]:
        del _recent[client]


def _too_many(client):
    global _requests_seen
    _requests_seen += 1
    now = time.time()
    if _requests_seen % SWEEP_EVERY == 0:
        _sweep(now)
    recent = _recent[client]
    while recent and now - recent[0] > RATE_WINDOW:
        recent.popleft()
    if len(recent) >= RATE_LIMIT:
        return True
    recent.append(now)
    return False


def _ai_budget_left():
    """True (and counted) if the server may still use Gemini this minute and this day."""
    now = time.time()
    while _ai_calls and now - _ai_calls[0] > 86_400:
        _ai_calls.popleft()
    last_minute = 0
    for t in reversed(_ai_calls):
        if now - t > 60:
            break
        last_minute += 1
    if len(_ai_calls) >= AI_PER_DAY or last_minute >= AI_PER_MINUTE:
        return False
    _ai_calls.append(now)
    return True


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


@app.get("/overview")
def overview():
    """The first screen's "this month at a glance": computed by the same code as every answer."""
    o = analytics.officer_summary(load())
    names = lambda items: [{"school_id": b["school_id"], "en": reply.short(b, "en"), "gu": reply.short(b, "gu")}
                           for b in items]
    a = o["cluster_attendance"]
    return {"month": o["month"], "schools_total": o["schools_total"], "counts": o["counts"],
            "visit_first": names(o["visit_plan"]), "not_enough_data": names(o["not_enough_data"]),
            "attendance_pct": a["student_attendance_pct"], "schools_reporting": a["schools_reporting"]}


@app.post("/ask")
def answer(body: Question, request: Request):
    if _too_many(_client(request)):
        raise HTTPException(status_code=429, detail="Too many questions in a minute; please wait a little.")
    ai_on = llm.enabled()
    use_ai = ai_on and _ai_budget_left()
    r = ask(body.question, lang=body.lang, school_id=body.school_id, use_llm=use_ai, test_checker=body.test_checker)
    phrase = r["trace"].get("phrase") or {}
    checked = phrase.get("check") or {}
    return {
        "text": r["text"], "lang": r["lang"], "intent": r["intent"], "options": r["options"], "mode": r["mode"],
        "lead": r.get("lead"), "cards": r.get("cards"),
        # What the page shows under each answer: was AI wording used, and did the checker reject any?
        "check": {"ai_used": r["mode"] == "llm", "ai_tried": bool(phrase),
                  "rejected": bool(checked) and not phrase.get("ok"),
                  "unsupported": checked.get("unsupported", []), "number_words": checked.get("number_words", []),
                  "problem": phrase.get("problem"), "error": phrase.get("error"),
                  "ai_paused": ai_on and not use_ai, "test_checker": r["trace"].get("test_checker")},
    }
