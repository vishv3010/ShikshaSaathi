"""Analysis facts: correct numbers, honest gaps, and nothing that cannot be sent as JSON."""
import json

import pytest

from saathi import analytics, data
from saathi.actions import TEXT, render_action
from saathi.lang import LANGS

D = data.load()


def test_brief_sample_rows_are_in_the_data():
    a = D.assessments.set_index(["school_id", "month", "grade", "subject"])
    assert tuple(a.loc[("GJ-C07-014", "2026-08", 5, "Maths")]) == (41, 38)
    assert tuple(a.loc[("GJ-C07-014", "2026-08", 5, "Gujarati")]) == (58, 19)
    assert tuple(a.loc[("GJ-C07-009", "2026-08", 5, "Maths")]) == (63, 12)


def test_rampura_grade5_maths():
    r = analytics.subject_analysis(D, "GJ-C07-014", 5, "Maths")
    assert [t["avg_score_pct"] for t in r["trend"]] == [45, 43, 41, 39, 36]
    assert r["latest"] == {"month": "2026-10", "avg_score_pct": 36, "pct_below_basic": 47}
    assert r["change_since_first"] == -9
    assert {o["subject"]: o["avg_score_pct"] for o in r["other_subjects_same_grade"]} == {"Gujarati": 63, "EVS": 57}
    assert r["cluster_average"]["schools"] == 19          # Umarvada has no October result
    assert r["context"]["multigrade_classes"] == "yes"
    assert (r["context"]["teacher_posts_sanctioned"], r["context"]["teachers_in_position"]) == (3, 2)
    assert len(r["related_visit_notes"]) == 2
    assert r["action"] == {"code": "class_remedial", "grade": 5, "subject": "Maths"}


def test_latest_result_older_than_this_month_is_flagged():
    # Umarvada Grade 3 Maths: June 43, July 45, August 47; nothing for September or October.
    r = analytics.subject_analysis(D, "GJ-C07-017", 3, "Maths")
    assert r["latest"]["month"] == "2026-08" and not r["latest_is_current_month"]
    assert r["missing_months"] == ["2026-09", "2026-10"]
    assert r["change_since_first"] == 4


@pytest.mark.parametrize("school_id, grade, subject, reason", [
    ("GJ-C07-014", 7, "Maths", "grade_not_offered"),    # Rampura is primary (Std 1-5)
    ("GJ-C07-001", 7, "EVS", "subject_not_taught"),     # Grades 6-8 take Science
])
def test_not_applicable_is_not_missing(school_id, grade, subject, reason):
    r = analytics.subject_analysis(D, school_id, grade, subject)
    assert (r["status"], r["reason"]) == ("not_applicable", reason)


def test_attendance_months_keep_vacation_and_gaps_apart():
    months = {m["month"]: m for m in analytics.attendance_months(D, "GJ-C07-017")}
    assert months["2026-05"]["status"] == "school_closed"
    assert months["2026-09"]["student_attendance_pct"] is None
    assert months["2026-10"]["status"] == "missing"
    assert analytics.attendance_months(D, "GJ-C07-009")[3]["teacher_attendance_pct"] is None  # August blank


def test_missing_data_report():
    report = analytics.missing_data_report(D)
    assert [s["name"] for s in report["not_enough_data_this_month"]] == ["Umarvada Primary School"]
    umarvada = next(s for s in report["schools"] if s["school_id"] == "GJ-C07-017")
    found = {(g["what"], g.get("month", g.get("field"))) for g in umarvada["gaps"]}
    assert {("student_attendance", "2026-09"), ("attendance_row", "2026-10"),
            ("assessment_results", "2026-10"), ("facilities", "electricity")} <= found
    # Vacation months and grades a primary school does not have are never reported as gaps.
    assert all(g.get("month") != "2026-05" for s in report["schools"] for g in s["gaps"])


def test_cluster_attendance_trend():
    t = analytics.attendance_trend(D)
    assert t["biggest_drops"][0]["name"].startswith("Chandrapur")
    assert [s["school_id"] for s in t["not_reported"]] == ["GJ-C07-017"]
    october = t["months"][-1]
    assert (october["schools_reporting"], october["schools_total"]) == (19, 20)


def test_every_fact_is_json_safe():
    """No NaN or numpy types anywhere: missing values must be None."""
    facts = [analytics.priority_list(D), analytics.missing_data_report(D),
             analytics.attendance_trend(D), analytics.recent_visits(D)]
    for school_id in D.schools.school_id:
        facts += [analytics.school_summary(D, school_id), analytics.attendance_trend(D, school_id),
                  analytics.recent_visits(D, school_id)]
        facts += [analytics.subject_analysis(D, school_id, g, s)
                  for g in range(3, 9) for s in ["Gujarati", "Maths", "EVS", "Science"]]
    for f in facts:
        json.dumps(f, allow_nan=False, ensure_ascii=False)


@pytest.mark.parametrize("lang", LANGS)
def test_every_action_renders_in_every_language(lang):
    for code in TEXT:
        action = {"code": code, "month": "2026-10"}
        if code in ("class_remedial", "teacher_availability"):
            action.update(grade=5, subject="Maths")
        text = render_action(action, lang)
        assert "{" not in text and text.strip()
        if lang == "gu":
            assert any("\u0a80" <= ch <= "\u0aff" for ch in text)  # Gujarati script
