"""The question-answering pipeline (PLAN.md section 1):

    understand -> validate -> compute facts -> phrase

`ask()` is the one entry point: the chat page calls it today, and a WhatsApp or
SwiftChat webhook would call the same function. In this version both the
"understand" and "phrase" steps are rule-based, so every answer is correct with
no LLM at all (D-009). The Gemini layer will plug into the same two steps and
be checked against the same facts.
"""
from dataclasses import asdict
from difflib import get_close_matches

from . import analytics, reply, understand
from .data import AS_OF, ASSESSED_GRADES, load, subjects_for
from .lang import LANGS
from .scoring import LONG_UNVISITED_DAYS, RECENT_VISIT_DAYS

SUGGESTION_CUTOFF = 0.6   # how close an unknown name must be to suggest a school ("Rampur school" -> Rampura)


def month_note(data, month):
    """None when the asked month can be answered; otherwise why it cannot (closed, not yet, before the data)."""
    if month is None:
        return None
    calendar = {r.month: r for r in data.calendar.itertuples()}
    latest = data.latest_month
    if month in calendar and calendar[month].school_open != "yes":
        return {"month": month, "status": "school_closed", "note": calendar[month].note, "latest": latest}
    if month in data.open_months and month <= latest:
        return None
    if month > latest:
        return {"month": month, "status": "not_yet", "latest": latest}
    return {"month": month, "status": "before_data", "first": min(calendar), "latest": latest}


def _school_brief(data, school_id):
    s = data.school(school_id)
    return {"school_id": school_id, "name": s["name"], "name_gu": s["name_gu"]}


def compute(q, data):
    """(kind of answer, facts). Facts hold every number the reply may use, and nothing more."""
    intent = q.intent
    sid = q.school_ids[0] if len(q.school_ids) == 1 else None
    note = month_note(data, q.month)
    usable_month = q.month if q.month and not note else None

    if intent == "top_priority_schools":
        facts = analytics.priority_list(data, q.limit, usable_month)
        facts["rules"] = {"long_unvisited_days": LONG_UNVISITED_DAYS, "recent_visit_days": RECENT_VISIT_DAYS}
        return intent, {**facts, "month_note": note}

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


def reply_language(q, lang=None):
    """Explicit choice (UI toggle) first, then a request in the question, then the question's own language.
    Hindi has no templates yet, so without the LLM it is answered in English (A-20)."""
    chosen = lang or q.reply_lang or q.lang
    return chosen if chosen in LANGS else "en"


def ask(text, lang=None, school_id=None, data=None):
    """Answer one question. `lang` forces 'en' or 'gu'; `school_id` pins the school
    (sent back by the chat page when she taps an option)."""
    data = data or load()
    q = understand.parse(text or "", data, school_id=school_id)
    kind, facts = compute(q, data)
    out_lang = reply_language(q, lang)
    answer, options = reply.render(kind, facts, out_lang)
    return {"intent": kind, "lang": out_lang, "text": answer, "options": options, "facts": facts,
            "question": asdict(q), "mode": "rules"}
