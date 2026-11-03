"""Facts for each kind of question. Every number the assistant may say comes from here.

Each function returns a plain dict that can be turned into JSON. Missing values
are None (never 0), and "not applicable" (a grade the school does not have,
a vacation month) is reported separately from "missing".
"""
import pandas as pd

from .actions import TEACHER_LOW
from .data import AS_OF, ASSESSED_GRADES, grades_mentioned, num, subjects_for
from .scoring import score_all, score_school, visit_plan

SUBJECT_WORDS = {"Gujarati": ["gujarati", "read"], "Maths": ["math"],
                 "EVS": ["evs"], "Science": ["science", "experiment"]}
CLASS_CONCERN = 50   # a class average below this gets a remedial action in subject analysis


def school_profile(data, school_id):
    s = data.school(school_id)
    return {"school_id": school_id, "name": s["name"], "name_gu": s["name_gu"],
            "village": s["village"], "village_gu": s["village_gu"], "type": s["type"],
            "grades": data.grades(school_id), "enrolment": int(s["enrolment"])}


def priority_list(data, limit=3, month=None):
    """'Which schools need my visit this week?'"""
    return visit_plan(data, limit, month)


def school_summary(data, school_id, month=None):
    """'Tell me about school X': score with reasons, attendance by month, facilities, last visit."""
    return {"school": school_profile(data, school_id),
            "priority": score_school(data, school_id, month),
            "attendance_by_month": attendance_months(data, school_id)}


def subject_analysis(data, school_id, grade, subject):
    """'Why is Grade 5 Maths low in school X?'"""
    school = school_profile(data, school_id)
    base = {"school": school, "grade": grade, "subject": subject}
    if grade not in ASSESSED_GRADES:
        return {**base, "status": "not_applicable", "reason": "grade_not_assessed",
                "assessed_grades": ASSESSED_GRADES}
    if grade not in school["grades"]:
        return {**base, "status": "not_applicable", "reason": "grade_not_offered"}
    if subject not in subjects_for(grade):
        return {**base, "status": "not_applicable", "reason": "subject_not_taught",
                "taught_instead": subjects_for(grade)[2]}

    a = data.assessments
    rows = a[(a.school_id == school_id) & (a.grade == grade) & (a.subject == subject)].set_index("month")
    trend = [{"month": m,
              "avg_score_pct": num(rows.at[m, "avg_score_pct"]) if m in rows.index else None,
              "pct_below_basic": num(rows.at[m, "pct_below_basic"]) if m in rows.index else None}
             for m in data.open_months]
    available = [t for t in trend if t["avg_score_pct"] is not None]
    if not available:
        return {**base, "status": "no_data", "months": data.open_months}

    first, latest = available[0], available[-1]
    same_grade = a[(a.school_id == school_id) & (a.grade == grade) & (a.month == latest["month"])
                   & (a.subject != subject)]
    cluster = a[(a.grade == grade) & (a.subject == subject) & (a.month == latest["month"])]
    cluster_avg = num(cluster.avg_score_pct.mean())
    concern = latest["avg_score_pct"] < CLASS_CONCERN
    return {
        **base,
        "status": "ok",
        "latest": latest,
        "latest_is_current_month": latest["month"] == data.latest_month,
        "first": first,
        "change_since_first": num(latest["avg_score_pct"] - first["avg_score_pct"]),
        "trend": trend,
        "missing_months": [t["month"] for t in trend if t["avg_score_pct"] is None],
        "other_subjects_same_grade": [{"subject": r.subject, "avg_score_pct": num(r.avg_score_pct)}
                                      for r in same_grade.itertuples()],
        "cluster_average": {"avg_score_pct": cluster_avg, "schools": len(cluster),
                            "difference": num(latest["avg_score_pct"] - cluster_avg)},
        "context": data.facilities_for(school_id),
        "related_visit_notes": related_notes(data, school_id, grade, subject),
        "action": ({"code": "class_remedial", "grade": grade, "subject": subject} if concern
                   else {"code": "routine"}),
    }


def related_notes(data, school_id, grade, subject):
    """Visit notes that mention this grade or this subject."""
    return [v for v in data.visits_for(school_id)
            if grade in grades_mentioned(v["notes"])
            or any(word in v["notes"].lower() for word in SUBJECT_WORDS[subject])]


def attendance_months(data, school_id):
    """One row per calendar month: closed (vacation), missing, or the recorded figures."""
    att = data.attendance[data.attendance.school_id == school_id].set_index("month")
    rows = []
    for month, school_open, note in data.calendar[["month", "school_open", "note"]].itertuples(index=False):
        if school_open != "yes":
            rows.append({"month": month, "status": "school_closed", "note": note})
        elif month not in att.index:
            rows.append({"month": month, "status": "missing"})
        else:
            rows.append({"month": month, "status": "recorded",
                         "student_attendance_pct": num(att.at[month, "student_attendance_pct"]),
                         "teacher_attendance_pct": num(att.at[month, "teacher_attendance_pct"])})
    return rows


def cluster_attendance(data):
    """Average attendance across the schools that reported, month by month."""
    rows = []
    for month, school_open, note in data.calendar[["month", "school_open", "note"]].itertuples(index=False):
        if school_open != "yes":
            rows.append({"month": month, "status": "school_closed", "note": note})
            continue
        m = data.attendance[data.attendance.month == month]
        rows.append({"month": month, "status": "recorded",
                     "student_attendance_pct": num(m.student_attendance_pct.mean()),
                     "teacher_attendance_pct": num(m.teacher_attendance_pct.mean()),
                     "schools_reporting": int(m.student_attendance_pct.notna().sum()),
                     "schools_total": len(data.schools)})
    return rows


def attendance_trend(data, school_id=None):
    """'Show attendance trend', for one school or the whole cluster."""
    if school_id:
        entry = score_school(data, school_id)
        return {"school": school_profile(data, school_id),
                "months": attendance_months(data, school_id),
                "change": entry["indicators"]["attendance_drop"] if entry["status"] == "scored" else None,
                "cluster_months": cluster_attendance(data)}
    scored = [e for e in score_all(data) if e["status"] == "scored"]
    drops = sorted((e for e in scored if e["indicators"]["attendance_drop"]["value"] >= 2),
                   key=lambda e: -e["indicators"]["attendance_drop"]["value"])
    latest = data.attendance[data.attendance.month == data.latest_month]
    reported = set(latest.dropna(subset=["student_attendance_pct"]).school_id)
    names = data.schools.set_index("school_id")
    teacher_low = latest[latest.teacher_attendance_pct < TEACHER_LOW].sort_values("teacher_attendance_pct")
    return {"month": data.latest_month,
            "months": cluster_attendance(data),
            "biggest_drops": [{"school_id": e["school_id"], "name": e["name"], "name_gu": e["name_gu"],
                               "student_attendance_pct": e["indicators"]["student_attendance"]["value"],
                               **e["indicators"]["attendance_drop"]} for e in drops[:3]],
            # A school-level pattern, never a judgement of a person: leave and official duty count as absence.
            "low_teacher_attendance": {"below_pct": TEACHER_LOW, "schools": [
                {"school_id": r.school_id, "name": names.at[r.school_id, "name"],
                 "name_gu": names.at[r.school_id, "name_gu"], "teacher_attendance_pct": num(r.teacher_attendance_pct)}
                for r in teacher_low.itertuples()]},
            "not_reported": [{"school_id": s.school_id, "name": s.name, "name_gu": s.name_gu}
                             for s in data.schools.itertuples() if s.school_id not in reported]}


def class_overview(data, grade=None, subject=None, limit=3):
    """'Why is Grade 5 Maths low?' with no school named: that class across the cluster.
    With only a subject, every grade that takes it; with only a grade, every subject in it."""
    month = data.latest_month
    base = {"grade": grade, "subject": subject, "month": month}
    if grade is not None and grade not in ASSESSED_GRADES:
        return {**base, "status": "not_applicable", "reason": "grade_not_assessed", "assessed_grades": ASSESSED_GRADES}
    if grade is not None and subject and subject not in subjects_for(grade):
        return {**base, "status": "not_applicable", "reason": "subject_not_taught",
                "taught_instead": subjects_for(grade)[2]}

    grades = [grade] if grade is not None else [g for g in ASSESSED_GRADES if not subject or subject in subjects_for(g)]
    a = data.assessments
    rows = a[(a.month == month) & a.grade.isin(grades) & ((a.subject == subject) if subject else True)]
    rows = rows.dropna(subset=["avg_score_pct"]).sort_values(
        ["avg_score_pct", "pct_below_basic", "school_id"], ascending=[True, False, True], na_position="last")
    names = data.schools.set_index("school_id")
    results = [{"school_id": r.school_id, "name": names.at[r.school_id, "name"], "name_gu": names.at[r.school_id, "name_gu"],
                "grade": int(r.grade), "subject": r.subject, "avg_score_pct": num(r.avg_score_pct),
                "pct_below_basic": num(r.pct_below_basic)} for r in rows.itertuples()]
    expected = [s for s in data.schools.school_id if set(data.grades(s)) & set(grades)]
    reported = set(rows.school_id)
    return {**base, "status": "ok", "grades": grades,
            "average_pct": num(rows.avg_score_pct.mean()), "results": len(results),
            "below_concern": {"pct": CLASS_CONCERN, "count": sum(r["avg_score_pct"] < CLASS_CONCERN for r in results)},
            "lowest": results[:limit],
            "no_result": [{"school_id": s, "name": names.at[s, "name"], "name_gu": names.at[s, "name_gu"]}
                          for s in expected if s not in reported]}


def _brief(entry):
    """The parts of a score entry a one-line mention needs."""
    return {"school_id": entry["school_id"], "name": entry["name"], "name_gu": entry["name_gu"],
            "score": entry["score"], "priority": entry["priority"], "reasons": entry["reasons"],
            "indicators": {n: entry["indicators"][n] for n in entry["reasons"]} if entry["indicators"] else None,
            "weakest_class": entry["weakest_class"], "action": entry["action"],
            "days_since_visit": entry["last_visit"]["days_ago"] if entry["last_visit"] else None}


def officer_summary(data):
    """'Give me a summary for my block officer': a short message she can forward."""
    plan = visit_plan(data, limit=3)
    month = data.latest_month
    need = [e for e in score_all(data) if e["priority"] in ("High", "Medium")]
    return {"month": month, "as_of": AS_OF.isoformat(), "schools_total": len(data.schools),
            "counts": plan["counts"],
            "need_support": [_brief(e) for e in need],
            "visit_plan": [_brief(e) for e in plan["schools"]],
            "phone_follow_up": [_brief(e) for e in plan["moved_down"]],
            "watch": [_brief(e) for e in plan["watch"]],
            "not_enough_data": [_brief(e) for e in plan["not_enough_data"]],
            "cluster_attendance": next(r for r in cluster_attendance(data) if r["month"] == month)}


def school_gaps(data, school_id):
    """Every missing value for one school. Vacation months and grades the school
    does not have are not gaps, so they are never listed."""
    gaps = []
    att = data.attendance[data.attendance.school_id == school_id].set_index("month")
    for month in data.open_months:
        if month not in att.index:
            gaps.append({"what": "attendance_row", "month": month})
            continue
        for col, what in [("student_attendance_pct", "student_attendance"),
                          ("teacher_attendance_pct", "teacher_attendance")]:
            if pd.isna(att.at[month, col]):
                gaps.append({"what": what, "month": month})

    grades = data.grades(school_id)
    expected = {(g, s) for g in grades for s in subjects_for(g)}
    results = data.assessments[data.assessments.school_id == school_id]
    for month in data.open_months:
        m = results[results.month == month]
        missing = sorted(expected - set(zip(m.grade, m.subject)))
        if missing:
            gaps.append({"what": "assessment_results", "month": month, "available": len(m),
                         "expected": len(expected), "classes": [[int(g), s] for g, s in missing]})
        blank = m[m.pct_below_basic.isna()]
        for r in blank.itertuples():
            gaps.append({"what": "below_basic", "month": month, "class": [int(r.grade), r.subject]})

    for field, value in data.facilities_for(school_id).items():
        if value is None:
            gaps.append({"what": "facilities", "field": field})
    return gaps


def missing_data_report(data):
    """'Which schools have missing data?'"""
    schools = []
    for s in data.schools.itertuples():
        gaps = school_gaps(data, s.school_id)
        if gaps:
            schools.append({"school_id": s.school_id, "name": s.name, "name_gu": s.name_gu, "gaps": gaps})
    not_enough = [e for e in score_all(data) if e["status"] == "not_enough_data"]
    return {"month": data.latest_month,
            "schools_with_gaps": len(schools),
            "schools_total": len(data.schools),
            "not_enough_data_this_month": [{"school_id": e["school_id"], "name": e["name"],
                                            "name_gu": e["name_gu"], "gaps": e["gaps"]} for e in not_enough],
            "schools": schools}


def recent_visits(data, school_id=None):
    """'When did I last visit school X?' or, for the cluster, schools not visited for longest."""
    if school_id:
        return {"as_of": AS_OF.isoformat(), "school": school_profile(data, school_id),
                "visits": data.visits_for(school_id)}
    rows, last_30_days = [], 0
    for s in data.schools.itertuples():
        visits = data.visits_for(s.school_id)
        last_30_days += sum(v["days_ago"] <= 30 for v in visits)
        rows.append({"school_id": s.school_id, "name": s.name, "name_gu": s.name_gu,
                     "visits": len(visits), "last_visit": visits[0] if visits else None})
    rows.sort(key=lambda r: -(r["last_visit"]["days_ago"] if r["last_visit"] else float("inf")))
    return {"as_of": AS_OF.isoformat(), "visits_last_30_days": last_30_days, "schools": rows}
