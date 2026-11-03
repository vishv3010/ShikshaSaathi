"""Priority score: which schools need support first, and why.

Each indicator falls into a band and the band's points are added up (0-100).
This follows the banded, weighted style of the Government of India's
data-driven grading of ITIs (docs/RESEARCH.md), but it measures *need for
support*: a higher score means the school should get help sooner. It is never
a judgement of the school or its staff.
"""
from .actions import choose_action
from .data import AS_OF, num

# Bands are [low, high) -> points; None means open-ended. The whole rule is this table.
INDICATORS = {
    # Student attendance in the month (%). Lower is worse.
    "student_attendance": [(None, 70, 25), (70, 80, 18), (80, 90, 9), (90, None, 0)],
    # Fall in student attendance vs the average of the previous 3 school months (points).
    "attendance_drop": [(10, None, 15), (5, 10, 10), (2, 5, 5), (None, 2, 0)],
    # Average score across all grades and subjects in the month (%). Lower is worse.
    "learning_level": [(None, 40, 35), (40, 50, 25), (50, 60, 15), (60, 70, 5), (70, None, 0)],
    # Average share of children below basic across all grades and subjects (%). Higher is worse.
    "below_basic": [(40, None, 25), (30, 40, 18), (20, 30, 10), (None, 20, 0)],
}
MAX_POINTS = {name: max(points for *_, points in bands) for name, bands in INDICATORS.items()}
PRIORITY = [(70, "High"), (40, "Medium"), (0, "Low")]

MIN_PREVIOUS_MONTHS = 2   # attendance history needed to measure a drop
MIN_COVERAGE = 0.5        # share of expected assessment results needed for a fair score
RECENT_VISIT_DAYS = 14    # visit-plan rule (A-10)
LONG_UNVISITED_DAYS = 90  # any school not visited for longer is mentioned, whatever its score


def points_for(indicator, value):
    for low, high, points in INDICATORS[indicator]:
        if (low is None or value >= low) and (high is None or value < high):
            return points
    raise ValueError(f"{indicator}: no band for {value}")


def priority_for(score):
    return next(label for floor, label in PRIORITY if score >= floor)


def score_school(data, school_id, month=None):
    """Score one school for one month, or say exactly which data is missing."""
    month = month or data.latest_month
    school = data.school(school_id)
    att = data.attendance[data.attendance.school_id == school_id].set_index("month")
    results = data.assessments[(data.assessments.school_id == school_id) & (data.assessments.month == month)]

    def attendance(m, col="student_attendance_pct"):
        return num(att.at[m, col]) if m in att.index else None

    student = attendance(month)
    history = [m for m in data.previous_months(month) if attendance(m) is not None]
    expected = len(data.grades(school_id)) * 3
    scores, below = results.avg_score_pct.dropna(), results.pct_below_basic.dropna()

    visits = data.visits_for(school_id)
    entry = {
        "school_id": school_id,
        "name": school["name"],
        "name_gu": school["name_gu"],
        "month": month,
        "teacher_attendance_pct": attendance(month, "teacher_attendance_pct"),
        "weakest_class": weakest_class(results),
        "last_visit": visits[0] if visits else None,
        "context": data.facilities_for(school_id),
    }

    gaps = []
    if student is None:
        gaps.append({"what": "student_attendance", "month": month})
    if len(history) < MIN_PREVIOUS_MONTHS:
        gaps.append({"what": "attendance_history", "months": data.previous_months(month),
                     "available": len(history)})
    if len(scores) < MIN_COVERAGE * expected:
        gaps.append({"what": "assessment_results", "month": month, "available": len(scores), "expected": expected})
    elif len(below) < MIN_COVERAGE * expected:
        gaps.append({"what": "below_basic", "month": month, "available": len(below), "expected": expected})

    if gaps:
        entry.update(status="not_enough_data", gaps=gaps, score=None, priority=None, indicators=None, reasons=[])
    else:
        previous_avg = num(sum(attendance(m) for m in history) / len(history))
        change = num(student - previous_avg)
        indicators = {
            "student_attendance": {"value": student},
            "attendance_drop": {"value": num(-change), "change": change, "previous_avg": previous_avg,
                                "previous_months": history, "months_compared": len(history)},
            "learning_level": {"value": num(scores.mean()), "results": len(scores), "expected": expected},
            "below_basic": {"value": num(below.mean())},
        }
        for name, indicator in indicators.items():
            indicator["points"] = points_for(name, indicator["value"])
            indicator["max_points"] = MAX_POINTS[name]
        score = sum(i["points"] for i in indicators.values())
        reasons = sorted((n for n, i in indicators.items() if i["points"]), key=lambda n: -indicators[n]["points"])
        entry.update(status="scored", gaps=[], score=score, priority=priority_for(score),
                     indicators=indicators, reasons=reasons)

    entry["action"] = choose_action(entry)
    return entry


def weakest_class(results):
    """The grade-subject with the lowest average score in these results."""
    rows = results.dropna(subset=["avg_score_pct"])
    if rows.empty:
        return None
    row = rows.sort_values(["avg_score_pct", "pct_below_basic", "grade"], ascending=[True, False, True]).iloc[0]
    return {"grade": int(row.grade), "subject": row.subject,
            "avg_score_pct": num(row.avg_score_pct), "pct_below_basic": num(row.pct_below_basic)}


def score_all(data, month=None):
    """Every school, highest need first; ties go to the lower learning level (D-016)."""
    entries = [score_school(data, school_id, month) for school_id in data.schools.school_id]
    scored = sorted((e for e in entries if e["status"] == "scored"),
                    key=lambda e: (-e["score"], e["indicators"]["learning_level"]["value"],
                                   -e["indicators"]["below_basic"]["value"], e["school_id"]))
    return scored + [e for e in entries if e["status"] != "scored"]


def visit_plan(data, limit=3, month=None):
    """Schools to visit next: highest need first, but a school visited in the
    last RECENT_VISIT_DAYS days moves down the list (it is reported, not hidden)."""
    month = month or data.latest_month
    entries = score_all(data, month)
    need = [e for e in entries if e["priority"] in ("High", "Medium")]
    recent = {e["school_id"] for e in need
              if e["last_visit"] and e["last_visit"]["days_ago"] <= RECENT_VISIT_DAYS}
    picks = [e for e in need if e["school_id"] not in recent][:limit]
    picks += [e for e in need if e["school_id"] in recent][:limit - len(picks)]
    picked = {e["school_id"] for e in picks}

    counts = {label: sum(e["priority"] == label for e in entries) for _, label in PRIORITY}
    counts["not_enough_data"] = sum(e["status"] == "not_enough_data" for e in entries)
    return {
        "month": month,
        "as_of": AS_OF.isoformat(),
        "limit": limit,
        "counts": counts,
        "schools": picks,
        "moved_down": [e for e in need[:limit] if e["school_id"] in recent and e["school_id"] not in picked],
        # Low priority overall, but one rule still fired (e.g. a single weak class).
        "watch": [e for e in entries if e["priority"] == "Low" and e["action"]["code"] != "routine"],
        "not_enough_data": [e for e in entries if e["status"] == "not_enough_data"],
        "long_unvisited": [e for e in entries if e["school_id"] not in picked
                           and (e["last_visit"] is None or e["last_visit"]["days_ago"] > LONG_UNVISITED_DAYS)],
    }
