"""Generate the synthetic dataset for one cluster (GJ-C07): 20 schools, May-Oct 2026.

Each school has a designed profile (base attendance, base learning level) plus
seeded random noise, so the data looks real but is reproducible. A few schools
carry a specific "story" (see docs/DATASET.md) so the assistant has genuine
patterns to find, and some values are deliberately missing.

Run:  .venv/Scripts/python scripts/generate_data.py
"""
import re
from pathlib import Path

import numpy as np
import pandas as pd

SEED = 7
OUT = Path(__file__).resolve().parent.parent / "data"
ENCODING = "utf-8-sig"  # BOM so Excel shows Gujarati correctly

# Gujarat calendar: summer vacation 4 May - 7 June 2026, so May has no school data.
CALENDAR = [
    ("2026-05", "no", "Summer vacation (4 May - 7 June)"),
    ("2026-06", "yes", "Schools reopen 8 June; enrolment drive"),
    ("2026-07", "yes", "Monsoon"),
    ("2026-08", "yes", "Monsoon; festival season"),
    ("2026-09", "yes", ""),
    ("2026-10", "yes", "Navratri; first-term exams"),
]
OPEN_MONTHS = [m for m, is_open, _ in CALENDAR if is_open == "yes"]

# Month effects shared by every school.
STUDENT_SEASON = {"2026-06": -5, "2026-07": -3, "2026-08": -6, "2026-09": -1, "2026-10": -3}
TEACHER_SEASON = {"2026-06": -1, "2026-07": 0, "2026-08": 0, "2026-09": 0, "2026-10": 0}
SCORE_SEASON = {"2026-06": -4, "2026-07": -2, "2026-08": 0, "2026-09": 1, "2026-10": 1}  # June = post-vacation loss
SUBJECT_OFFSET = {"Gujarati": 3, "Maths": -5, "EVS": 0, "Science": -2}

# id, village (en), village (gu), type, enrolment, head teacher,
# base student attendance, base teacher attendance, base learning score
SCHOOLS = [
    (1, "Amrapur", "અમરાપુર", "upper_primary", 420, "Jignesh Patel", 92, 96, 68),
    (2, "Bhimpura", "ભીમપુરા", "upper_primary", 310, "Kokila Desai", 86, 93, 57),
    (3, "Chandrapur", "ચંદ્રપુર", "upper_primary", 280, "Bharat Solanki", 87, 92, 55),
    (4, "Dhamnod", "ધામણોદ", "primary", 140, "Meena Chaudhari", 88, 94, 60),
    (5, "Ganeshpura", "ગણેશપુરા", "upper_primary", 350, "Rajesh Vasava", 91, 95, 66),
    (6, "Haripar", "હરિપર", "primary", 120, "Nayna Joshi", 74, 90, 38),
    (7, "Jamla", "જામલા", "primary", 95, "Dilip Rathod", 85, 93, 54),
    (8, "Kesarpura", "કેસરપુરા", "primary", 110, "Hetal Shah", 84, 92, 42),
    (9, "Khodiyarnagar", "ખોડિયારનગર", "upper_primary", 330, "Pravin Makwana", 89, 95, 67),
    (10, "Lakhapadar", "લાખાપાદર", "primary", 160, "Sonal Trivedi", 87, 93, 58),
    (11, "Manekpur", "માણેકપુર", "upper_primary", 260, "Rekha Parmar", 88, 93, 58),
    (12, "Navli", "નાવલી", "upper_primary", 380, "Mahesh Gamit", 90, 96, 64),
    (13, "Pipaliya", "પીપળીયા", "primary", 85, "Kiran Bariya", 83, 91, 52),
    (14, "Rampura", "રામપુરા", "primary", 130, "Alpa Mehta", 86, 93, 57),
    (15, "Sonpura", "સોનપુરા", "upper_primary", 300, "Suresh Damor", 90, 94, 62),
    (16, "Talavdi", "તલાવડી", "primary", 150, "Jyoti Vaghela", 85, 92, 55),
    (17, "Umarvada", "ઉમરવાડા", "primary", 100, "Nilesh Chauhan", 84, 91, 53),
    (18, "Vasantpur", "વસંતપુર", "upper_primary", 240, "Pinal Bhatt", 86, 92, 56),
    (19, "Ambaliya", "આંબલિયા", "upper_primary", 270, "Arvind Rana", 76, 89, 41),
    (20, "Shivpura", "શિવપુરા", "primary", 70, "Daxa Prajapati", 82, 90, 50),
]


def sid(n):
    return f"GJ-C07-{n:03d}"


# Schools with a designed story. Everything else is "normal" plus noise.
MIGRATION = sid(3)        # attendance collapses in October (sugarcane migration)
LOW_UNVISITED = sid(6)    # low on everything, poor facilities, last visit in early July
IMPROVING = sid(8)        # weak in June, improving after a remedial programme
SAMPLE_009 = sid(9)       # matches the brief's sample row
DECLINING = sid(11)       # slow decline; two teachers on election (BLO) duty
WEAK_G5_MATHS = sid(14)   # fine overall, but Grade 5 Maths is weak (brief's sample row)
DATA_GAPS = sid(17)       # data uploads stopped in September (weak network)
RECENT_VISIT = sid(19)    # high need, but visited a few days ago
STORY_SCHOOLS = {MIGRATION, LOW_UNVISITED, IMPROVING, DECLINING, WEAK_G5_MATHS, DATA_GAPS, RECENT_VISIT}

# Extra student-attendance change on top of the season, by month.
ATTENDANCE_STORY = {
    MIGRATION: {"2026-09": -3, "2026-10": -19},
    DECLINING: {"2026-07": -2, "2026-08": -4, "2026-09": -7, "2026-10": -10},
}
# Teacher attendance overrides (official duty, not absence by choice).
TEACHER_OVERRIDE = {DECLINING: {"2026-09": 80, "2026-10": 77}}
# Extra learning-score change, by month.
SCORE_STORY = {
    IMPROVING: {"2026-06": -2, "2026-07": 0, "2026-08": 5, "2026-09": 10, "2026-10": 14},
    DECLINING: {"2026-07": -1, "2026-08": -3, "2026-09": -5, "2026-10": -7},
    MIGRATION: {"2026-10": -3},
}
# Exact cells: (school, month, grade, subject) -> (avg_score_pct, pct_below_basic or None).
# The 2026-08 values reproduce the sample rows printed in the assignment brief.
FIXED_SCORES = {
    (WEAK_G5_MATHS, "2026-06", 5, "Maths"): (45, None),
    (WEAK_G5_MATHS, "2026-07", 5, "Maths"): (43, None),
    (WEAK_G5_MATHS, "2026-08", 5, "Maths"): (41, 38),
    (WEAK_G5_MATHS, "2026-09", 5, "Maths"): (39, None),
    (WEAK_G5_MATHS, "2026-10", 5, "Maths"): (36, None),
    (WEAK_G5_MATHS, "2026-08", 5, "Gujarati"): (58, 19),
    (SAMPLE_009, "2026-08", 5, "Maths"): (63, 12),
}


def grades_for(school_type):
    return [3, 4, 5] if school_type == "primary" else [3, 4, 5, 6, 7, 8]


def subjects_for(grade):
    return ["Gujarati", "Maths", "EVS" if grade <= 5 else "Science"]


def below_basic_from(avg, rng):
    # Lower average -> more children below basic. Fitted to the brief's sample rows
    # (41 -> 38, 58 -> 19, 63 -> 12).
    return int(round(np.clip(85 - 1.15 * avg + rng.normal(0, 2.5), 2, 85)))


def build_schools():
    rows = []
    for n, village, village_gu, stype, enrol, head, *_ in SCHOOLS:
        if n == 1:
            name, name_gu = f"{village} Pay Center School", f"{village_gu} પે સેન્ટર શાળા"
        else:
            name, name_gu = f"{village} Primary School", f"{village_gu} પ્રાથમિક શાળા"
        rows.append({
            "school_id": sid(n), "name": name, "name_gu": name_gu,
            "village": village, "village_gu": village_gu, "type": stype,
            "enrolment": enrol, "head_teacher": head,
        })
    return pd.DataFrame(rows)


def build_calendar():
    return pd.DataFrame(CALENDAR, columns=["month", "school_open", "note"])


def build_attendance(rng):
    rows = []
    for n, *_, base_att, base_teacher, _score in SCHOOLS:
        school = sid(n)
        for month in OPEN_MONTHS:
            student = base_att + STUDENT_SEASON[month] + ATTENDANCE_STORY.get(school, {}).get(month, 0)
            student = round(float(np.clip(student + rng.normal(0, 1.5), 40, 99)), 1)
            teacher = TEACHER_OVERRIDE.get(school, {}).get(month)
            if teacher is None:
                teacher = round(float(np.clip(base_teacher + TEACHER_SEASON[month] + rng.normal(0, 1.5), 60, 100)), 1)
            rows.append({"school_id": school, "month": month,
                         "student_attendance_pct": student, "teacher_attendance_pct": float(teacher)})
    df = pd.DataFrame(rows)

    # Data gaps school: September student figure never synced, October not uploaded at all.
    df.loc[(df.school_id == DATA_GAPS) & (df.month == "2026-09"), "student_attendance_pct"] = np.nan
    df = df[~((df.school_id == DATA_GAPS) & (df.month == "2026-10"))]

    # Two random teacher-attendance gaps in "normal" schools.
    normal = df[~df.school_id.isin(STORY_SCHOOLS)].index
    df.loc[rng.choice(normal, size=2, replace=False), "teacher_attendance_pct"] = np.nan
    return df.reset_index(drop=True)


def build_assessments(rng):
    rows = []
    for n, _v, _vg, stype, *_, base_score in SCHOOLS:
        school = sid(n)
        for month in OPEN_MONTHS:
            for grade in grades_for(stype):
                for subject in subjects_for(grade):
                    fixed = FIXED_SCORES.get((school, month, grade, subject))
                    if fixed:
                        avg = fixed[0]
                        below = fixed[1] if fixed[1] is not None else below_basic_from(avg, rng)
                    else:
                        avg = (base_score + SUBJECT_OFFSET[subject] - (grade - 3) * 1.2
                               + SCORE_SEASON[month] + SCORE_STORY.get(school, {}).get(month, 0)
                               + rng.normal(0, 2.5))
                        avg = int(round(np.clip(avg, 15, 95)))
                        below = below_basic_from(avg, rng)
                    rows.append({"school_id": school, "month": month, "grade": grade, "subject": subject,
                                 "avg_score_pct": avg, "pct_below_basic": below})
    df = pd.DataFrame(rows)

    # Data gaps school: no October results, and only Gujarati uploaded for September.
    gaps = df.school_id == DATA_GAPS
    df = df[~(gaps & ((df.month == "2026-10") | ((df.month == "2026-09") & (df.subject != "Gujarati"))))]

    # About 1.5% of other rows missing at random, plus two rows with the
    # below-basic figure missing. Fixed sample cells are never touched.
    protected = {(s, m, g, sub) for s, m, g, sub in FIXED_SCORES}
    keys = list(zip(df.school_id, df.month, df.grade, df.subject))
    candidates = [i for i, k in zip(df.index, keys) if k not in protected and k[0] not in STORY_SCHOOLS]
    drop = rng.choice(candidates, size=round(0.015 * len(df)), replace=False)
    df = df.drop(index=drop)
    remaining = [i for i in candidates if i not in set(drop)]
    df["pct_below_basic"] = df["pct_below_basic"].astype("Int64")
    df.loc[rng.choice(remaining, size=2, replace=False), "pct_below_basic"] = pd.NA
    return df.reset_index(drop=True)


# Visits written by hand for story schools: (school, date, focus_area, notes).
STORY_VISITS = [
    (LOW_UNVISITED, "2026-07-03", "Classroom observation",
     "Grades 3 to 5 are taught together in one room as 1 of 3 teacher posts is vacant. "
     "Girls' toilet not working; head teacher has written to the block office."),
    (MIGRATION, "2026-07-14", "Attendance",
     "Attendance recovering after monsoon. Head teacher follows up with parents of absent children."),
    (MIGRATION, "2026-09-22", "School management",
     "Head teacher expects several families to leave for sugarcane harvesting after Navratri. "
     "Discussed keeping a list of children likely to migrate."),
    (DECLINING, "2026-06-24", "Teacher support",
     "Unit test planning with teachers. Grade 7 science kit is unused; shared simple experiment ideas."),
    (DECLINING, "2026-09-15", "Classroom observation",
     "Two teachers deputed on BLO duty for electoral roll revision; remaining teachers are covering extra classes."),
    (WEAK_G5_MATHS, "2026-08-19", "Maths",
     "Grade 5 maths: place value and division are weak. Grades 4 and 5 are taught together as one teacher post is vacant."),
    (WEAK_G5_MATHS, "2026-10-07", "Classroom observation",
     "Observed Grade 5 maths; children struggle with 3-digit numbers. Shared a bundles-and-sticks place value activity."),
    (IMPROVING, "2026-07-09", "Gujarati reading",
     "Many children in Grades 3 to 5 below grade level after the vacation. "
     "Head teacher started a daily 30-minute remedial period in small groups."),
    (IMPROVING, "2026-09-10", "Classroom observation",
     "Remedial groups running regularly; more children reading short paragraphs. Encouraged teachers to continue."),
    (DATA_GAPS, "2026-08-26", "School management",
     "Attendance app not syncing because of weak mobile network; head teacher enters data later from the register."),
    (RECENT_VISIT, "2026-08-05", "Attendance",
     "Attendance low in Grades 6 to 8; some older children help on farms during sowing."),
    (RECENT_VISIT, "2026-10-28", "Maths",
     "Worked with the Grade 6 to 8 maths teacher on fractions; agreed on weekly practice sheets. Review in 3 weeks."),
]

GENERIC_NOTES = {
    "Gujarati reading": [
        "Listened to Grade 3 children read aloud; most read simple words, a few need letter practice.",
        "Shared a story-card activity for Grade 4 reading.",
    ],
    "Maths": [
        "Grade 4 maths: shared number games using local objects for addition and subtraction.",
        "Reviewed the Grade 6 unit test together; fractions need more practice.",
    ],
    "EVS/Science": [
        "Helped the Grade 7 teacher plan a simple plant experiment.",
        "Grade 5 EVS: suggested a village water-source walk activity.",
    ],
    "Attendance": [
        "Checked registers; attendance steady. Head teacher calls parents after three days of absence.",
        "Discussed post-monsoon attendance with SMC members.",
    ],
    "Teacher support": [
        "Supported teachers in preparing unit test papers.",
        "Shared learning-outcome posters and how to use them in class.",
    ],
    "Classroom observation": [
        "Observed Grade 3 and 4 classes; good use of group work.",
        "Observed a Grade 8 science class; children engaged in discussion.",
    ],
    "School management": [
        "Attended SMC meeting; discussed school safety and cleanliness.",
        "Reviewed mid-day meal records and the school development plan.",
    ],
}


def random_school_day(rng):
    # A Monday-Saturday date between school reopening (8 June) and 30 October.
    days = pd.bdate_range("2026-06-08", "2026-10-30", freq="C", weekmask="Mon Tue Wed Thu Fri Sat")
    return days[rng.integers(len(days))].strftime("%Y-%m-%d")


def notes_for(focus, school_type):
    # A primary school (Std 1-5) must never get a note about Grades 6-8.
    allowed = grades_for(school_type)
    return [note for note in GENERIC_NOTES[focus] if all(g in allowed for g in grades_mentioned(note))]


def grades_mentioned(note):
    # "Grade 7", "Grades 6 to 8", "Grades 4 and 5" -> [7], [6, 8], [4, 5]
    pairs = re.findall(r"Grades? (\d)(?: (?:to|and) (\d))?", note)
    return [int(g) for pair in pairs for g in pair if g]


def build_visits(rng):
    rows = [dict(zip(["school_id", "visit_date", "focus_area", "notes"], v)) for v in STORY_VISITS]
    for n, _v, _vg, stype, *_ in SCHOOLS:
        school = sid(n)
        if school in STORY_SCHOOLS:
            continue
        for _ in range(rng.integers(1, 4)):  # 1 to 3 visits
            focus = rng.choice(list(GENERIC_NOTES))
            note = rng.choice(notes_for(focus, stype))
            rows.append({"school_id": school, "visit_date": random_school_day(rng),
                         "focus_area": focus, "notes": note})
    return pd.DataFrame(rows).sort_values(["visit_date", "school_id"]).reset_index(drop=True)


# Yearly snapshot (UDISE+ reference date 30 Sept 2025).
FACILITY_OVERRIDES = {
    LOW_UNVISITED: dict(teacher_posts_sanctioned=3, teachers_in_position=2, multigrade_classes="yes",
                        drinking_water="not functional", girls_toilet="not functional"),
    WEAK_G5_MATHS: dict(teacher_posts_sanctioned=3, teachers_in_position=2, multigrade_classes="yes"),
    RECENT_VISIT: dict(teacher_posts_sanctioned=7, teachers_in_position=6),
    sid(13): dict(teacher_posts_sanctioned=3, teachers_in_position=3, multigrade_classes="yes"),
    sid(20): dict(teacher_posts_sanctioned=2, teachers_in_position=2, multigrade_classes="yes"),
    DATA_GAPS: dict(electricity=None),  # not reported
}


def build_facilities():
    rows = []
    for n, _v, _vg, stype, enrol, *_ in SCHOOLS:
        school = sid(n)
        posts = (3 if enrol < 150 else 4) if stype == "primary" else (6 if enrol < 300 else 8)
        row = {"school_id": school, "as_of_date": "2025-09-30",
               "teacher_posts_sanctioned": posts, "teachers_in_position": posts,
               "multigrade_classes": "no", "drinking_water": "functional",
               "girls_toilet": "functional", "electricity": "yes"}
        row.update(FACILITY_OVERRIDES.get(school, {}))
        rows.append(row)
    return pd.DataFrame(rows)


def main():
    rng = np.random.default_rng(SEED)
    OUT.mkdir(exist_ok=True)
    tables = {
        "schools": build_schools(),
        "calendar": build_calendar(),
        "attendance": build_attendance(rng),
        "assessments": build_assessments(rng),
        "visits": build_visits(rng),
        "facilities": build_facilities(),
    }
    for name, df in tables.items():
        df.to_csv(OUT / f"{name}.csv", index=False, encoding=ENCODING)
        print(f"{name:12s} {len(df):5d} rows")


if __name__ == "__main__":
    main()
