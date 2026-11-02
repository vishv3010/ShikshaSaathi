"""Priority score tests. Expected values were worked out by hand from the CSVs in data/."""
import pytest

from saathi import data, scoring
from saathi.actions import choose_action

D = data.load()


def by_id(school_id, month=None):
    return scoring.score_school(D, school_id, month)


@pytest.mark.parametrize("indicator, value, points", [
    ("student_attendance", 69.9, 25), ("student_attendance", 70, 18), ("student_attendance", 79.9, 18),
    ("student_attendance", 80, 9), ("student_attendance", 89.9, 9), ("student_attendance", 90, 0),
    ("attendance_drop", 10, 15), ("attendance_drop", 9.9, 10), ("attendance_drop", 5, 10),
    ("attendance_drop", 2, 5), ("attendance_drop", 1.9, 0), ("attendance_drop", -5, 0),
    ("learning_level", 39.9, 35), ("learning_level", 40, 25), ("learning_level", 50, 15),
    ("learning_level", 69.9, 5), ("learning_level", 70, 0),
    ("below_basic", 40, 25), ("below_basic", 39.9, 18), ("below_basic", 20, 10), ("below_basic", 19.9, 0),
])
def test_band_edges(indicator, value, points):
    assert scoring.points_for(indicator, value) == points


def test_points_add_up_to_100():
    assert sum(scoring.MAX_POINTS.values()) == 100


@pytest.mark.parametrize("score, label", [(100, "High"), (70, "High"), (69, "Medium"), (40, "Medium"),
                                          (39, "Low"), (0, "Low")])
def test_priority_edges(score, label):
    assert scoring.priority_for(score) == label


def test_haripar_by_hand():
    # October attendance 73.2; July-September 71.1, 67.7, 72.9 -> 211.7 / 3 = 70.6, so it rose 2.6.
    # October scores 41+35+42+41+33+36+42+30+42 = 342 / 9 = 38.0.
    # Below basic 38+44+31+36+48+42+38+56+33 = 366 / 9 = 40.7.
    e = by_id("GJ-C07-006")
    i = e["indicators"]
    assert (i["student_attendance"]["value"], i["student_attendance"]["points"]) == (73.2, 18)
    assert (i["attendance_drop"]["previous_avg"], i["attendance_drop"]["change"]) == (70.6, 2.6)
    assert i["attendance_drop"]["points"] == 0
    assert (i["learning_level"]["value"], i["learning_level"]["points"]) == (38, 35)
    assert (i["below_basic"]["value"], i["below_basic"]["points"]) == (40.7, 25)
    assert (e["score"], e["priority"]) == (78, "High")
    assert e["weakest_class"] == {"grade": 5, "subject": "Maths", "avg_score_pct": 30, "pct_below_basic": 56}
    assert e["reasons"] == ["learning_level", "below_basic", "student_attendance"]


def test_chandrapur_by_hand():
    # October attendance 64.9; July-September 82.1, 81.2, 79.2 -> 242.5 / 3 = 80.8, a fall of 15.9.
    # 18 October results sum to 872 -> 48.4; below basic sums to 527 -> 29.3.
    e = by_id("GJ-C07-003")
    i = e["indicators"]
    assert (i["student_attendance"]["value"], i["student_attendance"]["points"]) == (64.9, 25)
    assert (i["attendance_drop"]["previous_avg"], i["attendance_drop"]["value"]) == (80.8, 15.9)
    assert i["attendance_drop"]["points"] == 15
    assert (i["learning_level"]["value"], i["learning_level"]["points"]) == (48.4, 25)
    assert (i["below_basic"]["value"], i["below_basic"]["points"]) == (29.3, 10)
    assert (e["score"], e["priority"]) == (75, "High")
    assert e["action"]["code"] == "attendance_drop"


def test_missing_data_is_never_scored_as_zero():
    # Umarvada: no October attendance row and no October results at all.
    e = by_id("GJ-C07-017")
    assert e["status"] == "not_enough_data"
    assert (e["score"], e["priority"]) == (None, None)
    assert {g["what"] for g in e["gaps"]} == {"student_attendance", "assessment_results"}
    assert e["action"] == {"code": "check_data", "month": "2026-10"}
    assert scoring.score_all(D)[-1]["school_id"] == "GJ-C07-017"


def test_partial_month_is_not_enough_data():
    # Umarvada in September: student attendance blank and only 3 of 9 results (Gujarati only).
    e = by_id("GJ-C07-017", "2026-09")
    assert e["status"] == "not_enough_data"
    assert {"what": "assessment_results", "month": "2026-09", "available": 3, "expected": 9} in e["gaps"]


def test_ties_go_to_lower_learning_level():
    tied = [e["name"].split()[0] for e in scoring.score_all(D) if e["score"] == 34]
    assert tied == ["Jamla", "Vasantpur", "Rampura", "Kesarpura"]  # 52.4 < 52.9 < 53.7 < 54.9


def test_visit_plan():
    plan = scoring.visit_plan(D, limit=3)
    assert [e["name"].split()[0] for e in plan["schools"]] == ["Haripar", "Chandrapur", "Manekpur"]
    # Ambaliya is third by need but was visited on 28 October, 5 days before 2 November.
    assert [(e["name"].split()[0], e["last_visit"]["days_ago"]) for e in plan["moved_down"]] == [("Ambaliya", 5)]
    assert [e["name"].split()[0] for e in plan["watch"]] == ["Rampura"]
    assert [e["name"].split()[0] for e in plan["not_enough_data"]] == ["Umarvada"]
    assert plan["counts"] == {"High": 3, "Medium": 4, "Low": 12, "not_enough_data": 1}


def test_visit_plan_fills_with_recent_schools_when_needed():
    plan = scoring.visit_plan(D, limit=7)  # exactly 7 schools are High or Medium
    # Ambaliya (visited 28 Oct) and Talavdi (20 Oct) were both seen in the last 14 days,
    # so they come last, still in order of need.
    assert [e["name"].split()[0] for e in plan["schools"][-2:]] == ["Ambaliya", "Talavdi"]
    assert len(plan["schools"]) == 7 and plan["moved_down"] == []


def entry(**changes):
    """A made-up scored entry where no rule fires, for testing rule order."""
    base = {"status": "scored", "month": "2026-10", "priority": "Medium", "teacher_attendance_pct": 95,
            "weakest_class": {"grade": 5, "subject": "Maths", "avg_score_pct": 55, "pct_below_basic": 15},
            "indicators": {"attendance_drop": {"value": 0}, "learning_level": {"value": 60},
                           "student_attendance": {"value": 90}}}
    for key, value in changes.items():
        if key in base["indicators"]:
            base["indicators"][key] = {"value": value}
        else:
            base[key] = value
    return base


@pytest.mark.parametrize("changes, code", [
    ({"attendance_drop": 12, "teacher_attendance_pct": 70, "learning_level": 30}, "attendance_drop"),
    ({"teacher_attendance_pct": 70, "learning_level": 30}, "teacher_availability"),
    ({"learning_level": 44}, "school_remedial"),
    ({"weakest_class": {"grade": 7, "subject": "Science", "avg_score_pct": 35, "pct_below_basic": 40},
      "student_attendance": 70}, "class_remedial"),
    ({"student_attendance": 75}, "attendance_follow_up"),
    ({}, "class_remedial"),                    # Medium priority: support the weakest class
    ({"priority": "Low"}, "routine"),
])
def test_action_rules_first_match_wins(changes, code):
    assert choose_action(entry(**changes))["code"] == code
