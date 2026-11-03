"""Check the dataset before any analysis runs on it.

Errors (broken IDs, duplicates, out-of-range values, rows in vacation months)
stop the run with exit code 1. Missing values are expected and only reported,
never filled in.

Run:  .venv/Scripts/python scripts/validate_data.py [data_dir]
"""
import re
import sys
from pathlib import Path

import pandas as pd

DATA = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent / "data"
ENCODING = "utf-8-sig"

REQUIRED = {
    "schools": ["school_id", "name", "village", "type", "enrolment", "head_teacher"],
    "calendar": ["month", "school_open"],
    "attendance": ["school_id", "month", "student_attendance_pct", "teacher_attendance_pct"],
    "assessments": ["school_id", "month", "grade", "subject", "avg_score_pct", "pct_below_basic"],
    "visits": ["school_id", "visit_date", "focus_area", "notes", "notes_gu"],
    "facilities": ["school_id", "teacher_posts_sanctioned", "teachers_in_position", "multigrade_classes",
                   "drinking_water", "girls_toilet", "electricity"],
}
KEYS = {
    "schools": ["school_id"],
    "calendar": ["month"],
    "attendance": ["school_id", "month"],
    "assessments": ["school_id", "month", "grade", "subject"],
    "facilities": ["school_id"],
}
GRADES = {"primary": {3, 4, 5}, "upper_primary": {3, 4, 5, 6, 7, 8}}

errors, notes = [], []


def check(ok, message):
    if not ok:
        errors.append(message)


def main():
    tables = {}
    for name, cols in REQUIRED.items():
        path = DATA / f"{name}.csv"
        if not path.exists():
            errors.append(f"{name}.csv is missing")
            continue
        df = pd.read_csv(path, encoding=ENCODING)
        missing_cols = set(cols) - set(df.columns)
        check(not missing_cols, f"{name}.csv lacks columns {sorted(missing_cols)}")
        tables[name] = df
    if errors:
        return report(tables)

    schools, cal = tables["schools"], tables["calendar"]
    att, ass, vis = tables["attendance"], tables["assessments"], tables["visits"]

    # Keys and references
    for name, key in KEYS.items():
        dupes = tables[name].duplicated(subset=key).sum()
        check(dupes == 0, f"{name}: {dupes} duplicate rows on {key}")
    ids = set(schools.school_id)
    check(schools.school_id.str.fullmatch(r"GJ-C07-\d{3}").all(), "schools: badly formed school_id")
    for name in ["attendance", "assessments", "visits", "facilities"]:
        unknown = set(tables[name].school_id) - ids
        check(not unknown, f"{name}: unknown school_id {sorted(unknown)}")
    check(set(schools.type) <= set(GRADES), f"schools: unknown type {set(schools.type) - set(GRADES)}")
    check((schools.enrolment > 0).all(), "schools: enrolment must be positive")

    # Ranges
    for name, cols in [("attendance", ["student_attendance_pct", "teacher_attendance_pct"]),
                       ("assessments", ["avg_score_pct", "pct_below_basic"])]:
        for col in cols:
            values = tables[name][col].dropna()
            check(values.between(0, 100).all(), f"{name}.{col}: values outside 0-100")

    # Calendar: no school data in closed months, no months outside the calendar
    open_months = set(cal.loc[cal.school_open == "yes", "month"])
    for name in ["attendance", "assessments"]:
        bad = set(tables[name].month) - open_months
        check(not bad, f"{name}: rows in closed or unknown months {sorted(bad)}")
    dates = pd.to_datetime(vis.visit_date, errors="coerce")
    check(dates.notna().all(), "visits: invalid visit_date")
    check(dates.dt.strftime("%Y-%m").isin(open_months).all(), "visits: visit in a closed or unknown month")

    # Grades and subjects must match the school type and grade
    merged = ass.merge(schools[["school_id", "type"]], on="school_id")
    wrong_grade = merged[[g not in GRADES[t] for g, t in zip(merged.grade, merged.type)]]
    check(wrong_grade.empty, f"assessments: {len(wrong_grade)} rows for grades the school does not have")
    expected_subject = merged.grade.map(lambda g: {"Gujarati", "Maths", "EVS" if g <= 5 else "Science"})
    wrong_subject = [s not in e for s, e in zip(merged.subject, expected_subject)]
    check(not any(wrong_subject), f"assessments: {sum(wrong_subject)} rows with a subject not taught in that grade")
    vis_types = vis.merge(schools[["school_id", "type"]], on="school_id")
    bad_notes = [s for s, t, note in zip(vis_types.school_id, vis_types.type, vis_types.notes)
                 if any(int(g) not in GRADES[t]
                        for pair in re.findall(r"Grades? (\d)(?: (?:to|and) (\d))?", str(note)) for g in pair if g)]
    check(not bad_notes, f"visits: notes mention grades the school does not have {sorted(set(bad_notes))}")

    # Gujarati notes: present, in Gujarati script, and carrying exactly the numbers of the English note
    # (the number checker treats both as evidence, so they must agree).
    gujarati = vis.notes_gu.fillna("").map(lambda s: bool(re.search("[\u0a80-\u0aff]", s)))
    check(gujarati.all(), f"visits: {int((~gujarati).sum())} notes_gu missing or not in Gujarati")
    numbers_differ = [i for i, (en, gu) in enumerate(zip(vis.notes, vis.notes_gu.fillna("")))
                      if sorted(re.findall(r"\d+", str(en))) != sorted(re.findall(r"\d+", gu))]
    check(not numbers_differ, f"visits: notes_gu numbers differ from notes in rows {numbers_differ}")

    # Coverage: expected rows vs actual (gaps are reported, not errors)
    n_open = len(open_months)
    expected_att = len(schools) * n_open
    expected_ass = sum(len(GRADES[t]) * 3 for t in schools.type) * n_open
    notes.append(f"attendance rows: {len(att)} of {expected_att} expected")
    notes.append(f"assessment rows: {len(ass)} of {expected_ass} expected")
    notes.append(f"visits: {len(vis)}, covering {vis.school_id.nunique()} of {len(schools)} schools")
    for name in ["attendance", "assessments", "facilities"]:
        gaps = tables[name].isna().sum()
        gaps = gaps[gaps > 0]
        for col, count in gaps.items():
            notes.append(f"missing {name}.{col}: {count}")
    att_full = att.drop_duplicates(["school_id", "month"]).set_index(["school_id", "month"]).reindex(
        pd.MultiIndex.from_product([sorted(ids), sorted(open_months)]))
    absent = att_full[att_full.isna().all(axis=1)].index.tolist()
    for school, month in absent:
        notes.append(f"no attendance row: {school} {month}")
    return report(tables)


def report(tables):
    print("Tables: " + ", ".join(f"{n} ({len(df)})" for n, df in tables.items()))
    for line in notes:
        print("  " + line)
    if errors:
        print(f"\n{len(errors)} ERROR(S):")
        for e in errors:
            print("  " + e)
        return 1
    print("\nOK: no errors. Missing values above are expected and are kept as missing.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
