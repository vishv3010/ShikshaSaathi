"""The question-answering pipeline (PLAN.md section 1):

    understand -> validate -> compute facts -> phrase

`ask()` is the one entry point: the chat page calls it, and a WhatsApp or
SwiftChat webhook would call the same function.

    1. rules read the question (understand.py)
    2. only if the rules cannot place it, Gemini reads it; the code validates its JSON
    3. Python computes the facts (analytics.py); every number comes from here
    4. a template writes a draft from the facts (reply.py)
    5. Gemini adds a one- or two-sentence direct answer above the draft (English,
       Gujarati), or translates the whole draft (Hindi)
    6. the number checker compares every number with the facts (checker.py), and for
       a translation also that no number was dropped; if not, the draft is sent

Without a key, or when Gemini fails, steps 2, 5 and 6 are skipped and every
answer is still correct (D-009).
"""
from dataclasses import asdict
from difflib import get_close_matches

from . import analytics, llm, llm_steps, reply, understand
from .actions import render_action
from .data import AS_OF, ASSESSED_GRADES, load, subjects_for
from .lang import LANGS
from .scoring import LONG_UNVISITED_DAYS, MIN_PREVIOUS_MONTHS, RECENT_VISIT_DAYS

SUGGESTION_CUTOFF = 0.6   # how close an unknown name must be to suggest a school ("Rampur school" -> Rampura)
SCORE_SCALE = 100         # priority scores are out of 100
SCORED_KINDS = {"top_priority_schools", "school_summary", "officer_summary"}
EXAMPLE_KINDS = {"help", "out_of_scope", "people_judgement", "personal_info", "not_allowed"}
# Answers built from school data get Gemini's wording; boundaries and "which one?" questions keep
# the fixed wording, except in Hindi, which has no templates.
DATA_KINDS = {"top_priority_schools", "school_summary", "subject_analysis", "class_overview", "attendance_trend",
              "missing_data", "recent_visits", "officer_summary"}


def month_note(data, month, scored=False):
    """None when the asked month can be answered; otherwise why it cannot (closed, not yet, before the
    data, or, for a score, too early: a score needs MIN_PREVIOUS_MONTHS earlier school months)."""
    if month is None:
        return None
    calendar = {r.month: r for r in data.calendar.itertuples()}
    latest = data.latest_month
    if month in calendar and calendar[month].school_open != "yes":
        return {"month": month, "status": "school_closed", "note": calendar[month].note, "latest": latest}
    if month in data.open_months and month <= latest:
        if scored and len(data.previous_months(month)) < MIN_PREVIOUS_MONTHS:
            first = next(m for m in data.open_months if len(data.previous_months(m)) >= MIN_PREVIOUS_MONTHS)
            return {"month": month, "status": "too_early", "first": first, "latest": latest}
        return None
    if month > latest:
        return {"month": month, "status": "not_yet", "latest": latest}
    return {"month": month, "status": "before_data", "first": min(calendar), "latest": latest}


def _school_brief(data, school_id):
    s = data.school(school_id)
    return {"school_id": school_id, "name": s["name"], "name_gu": s["name_gu"]}


def compute(q, data):
    """(kind of answer, facts). Facts hold every number the reply may use, and nothing more:
    the number checker treats them as the only source of truth."""
    kind, facts = _compute(q, data)
    return kind, complete(kind, facts)


def complete(kind, facts):
    """Add what the reply shows besides data: the score scale, each action's wording
    (it contains numbers such as "30-minute"), and example questions."""
    if kind in SCORED_KINDS:
        facts["score_scale"] = SCORE_SCALE
    if kind in EXAMPLE_KINDS:
        facts["examples"] = reply.EXAMPLES
    _add_action_text(facts)
    return facts


def _add_action_text(value):
    if isinstance(value, dict):
        action = value.get("action")
        if isinstance(action, dict) and "code" in action:
            value["action_text"] = {lang: render_action(action, lang) for lang in LANGS}
        for v in list(value.values()):
            _add_action_text(v)
    elif isinstance(value, list):
        for v in value:
            _add_action_text(v)


def _compute(q, data):
    intent = q.intent
    sid = q.school_ids[0] if len(q.school_ids) == 1 else None
    note = month_note(data, q.month, scored=intent in ("top_priority_schools", "school_summary"))
    usable_month = q.month if q.month and not note else None

    if intent == "top_priority_schools":
        facts = analytics.priority_list(data, q.limit, usable_month)
        facts["rules"] = {"long_unvisited_days": LONG_UNVISITED_DAYS, "recent_visit_days": RECENT_VISIT_DAYS}
        return intent, {**facts, "latest_month": data.latest_month, "month_note": note}

    if intent == "school_summary":
        return intent, {**analytics.school_summary(data, sid, usable_month), "month_note": note}

    if intent == "subject_analysis":
        return _subject(q, data, sid)

    if intent == "class_overview":
        return intent, analytics.class_overview(data, q.grade, q.subject, q.limit)

    if intent == "attendance_trend":
        facts = analytics.attendance_trend(data, sid)
        facts.update(latest_month=data.latest_month, month_note=note if note and note["status"] != "school_closed"
                     else None)
        if sid and q.month and (not note or note["status"] == "school_closed"):
            facts["asked_month"] = q.month           # the reply leads with that month (closed months show as such)
        elif not sid:
            facts["month_note"] = note
        return intent, facts

    if intent == "missing_data":
        if sid:
            entry = analytics.score_school(data, sid)
            return intent, {"school": analytics.school_profile(data, sid), "gaps": analytics.school_gaps(data, sid),
                            "score_status": entry["status"], "action": entry["action"]}
        closed = list(data.calendar.loc[data.calendar.school_open != "yes", "month"])
        return intent, {**analytics.missing_data_report(data), "as_of": AS_OF.isoformat(), "closed_months": closed}

    if intent == "recent_visits":
        return intent, analytics.recent_visits(data, sid)

    if intent == "officer_summary":
        return intent, analytics.officer_summary(data)

    if intent == "school_not_found":
        return intent, _not_found(q, data)

    if intent == "clarify_school":
        named = not q.unknown_school and len(q.school_ids) > 1
        return intent, {"question": q.text, "candidates": [_school_brief(data, s) for s in q.school_ids],
                        "reason": "several_named" if named else "unclear_name"}

    return intent, {}   # help and the polite boundaries need no data


def _subject(q, data, sid):
    if q.grade is None and q.subject is None:      # e.g. Gemini read "how is Rampura doing in studies?"
        return "school_summary", analytics.school_summary(data, sid)
    profile = analytics.school_profile(data, sid)
    if q.grade is None:
        grades = [g for g in profile["grades"] if q.subject in subjects_for(g)]
        if not grades:   # e.g. Science at a primary school: none of its grades takes it
            instead = next(s for s in subjects_for(profile["grades"][0]) if s not in ("Gujarati", "Maths"))
            return "subject_analysis", {"school": profile, "grade": None, "subject": q.subject,
                                        "status": "not_applicable", "reason": "subject_not_at_school",
                                        "taught_instead": instead}
        return "clarify_grade", {"school": profile, "subject": q.subject, "grades": grades, "question": q.text}
    if q.subject is None:
        if q.grade not in ASSESSED_GRADES or q.grade not in profile["grades"]:
            return "subject_analysis", analytics.subject_analysis(data, sid, q.grade, subjects_for(q.grade)[1])
        return "clarify_subject", {"school": profile, "grade": q.grade, "subjects": subjects_for(q.grade),
                                   "question": q.text}
    return "subject_analysis", analytics.subject_analysis(data, sid, q.grade, q.subject)


def _not_found(q, data):
    name = q.unknown_school
    native = not name.isascii()
    pool = {(s.village_gu if native else s.village.lower()): s.school_id for s in data.schools.itertuples()}
    close = get_close_matches(understand.to_gujarati_script(name) if native else name.lower(), list(pool),
                              n=3, cutoff=SUGGESTION_CUTOFF)
    return {"name": name, "question": q.text,
            "suggestions": [_school_brief(data, pool[c]) for c in close],
            "schools": [_school_brief(data, s) for s in data.schools.school_id]}


def needs_opening(kind, facts):
    """Is an LLM opening line worth a call? Not when the template already starts with the
    direct answer (one month's attendance, one school's gaps or visits), and not for the
    officer summary, which is meant to be forwarded as it is."""
    if kind == "attendance_trend":
        return not facts.get("asked_month")
    if kind in ("missing_data", "recent_visits"):
        return "school" not in facts
    return kind in DATA_KINDS and kind != "officer_summary"


def reply_language(q, lang=None, llm_on=False):
    """Explicit choice (UI toggle) first, then a request in the question, then the question's own language.
    Hindi needs the LLM; without it Hindi is answered in English (A-20)."""
    chosen = lang or q.reply_lang or q.lang
    if chosen in LANGS or (chosen == "hi" and llm_on):
        return chosen
    return "en"


def ask(text, lang=None, school_id=None, data=None, use_llm=None, test_checker=False):
    """Answer one question. `lang` forces 'en', 'gu' or 'hi'; `school_id` pins the school
    (sent back by the chat page when she taps an option); `use_llm` overrides the
    GEMINI_API_KEY / SAATHI_LLM setting; `test_checker` (demo only) adds a made-up figure
    to Gemini's text to show the number checker rejecting it."""
    data = data or load()
    use_llm = llm.enabled() if use_llm is None else use_llm
    text = text or ""
    trace = {"understood_by": "rules"}

    q = understand.parse(text, data, school_id=school_id)
    if use_llm and q.intent == "out_of_scope" and text.strip():
        better, usage = llm_steps.understand_question(text, data)
        if usage:
            trace["understand"] = usage
        if better:
            q, trace["understood_by"] = better, "llm"

    kind, facts = compute(q, data)
    out_lang = reply_language(q, lang, llm_on=use_llm)
    draft_lang = out_lang if out_lang in LANGS else "en"
    draft, options = reply.render(kind, facts, draft_lang)

    answer, mode = draft, "rules"
    if test_checker:
        trace["test_checker"] = use_llm and (out_lang not in LANGS or kind in DATA_KINDS)
    if use_llm and out_lang not in LANGS:                  # Hindi: Gemini translates the whole draft
        worded = llm_steps.translate(text, kind, facts, draft, out_lang, tamper=test_checker)
        trace["phrase"] = {k: v for k, v in worded.items() if k != "text"}
        if worded["ok"]:
            answer, mode = worded["text"], "llm"
    elif use_llm and (needs_opening(kind, facts) or (test_checker and kind in DATA_KINDS)):
        worded = llm_steps.lead(text, kind, facts, draft, out_lang, tamper=test_checker)   # English, Gujarati
        trace["phrase"] = {k: v for k, v in worded.items() if k != "text"}
        if worded["ok"] and worded["text"]:
            answer, mode = f"{worded['text']}\n\n{draft}", "llm"
    if mode == "rules":
        out_lang = draft_lang          # e.g. Hindi asked, Gemini unavailable: the English draft is sent
    return {"intent": kind, "lang": out_lang, "text": answer, "options": options, "facts": facts,
            "question": asdict(q), "mode": mode, "draft": draft, "trace": trace}
