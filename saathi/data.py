"""Load the cluster dataset once and share small helpers used everywhere."""
import re
from dataclasses import dataclass, fields
from datetime import date
from functools import lru_cache
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
ENCODING = "utf-8-sig"

# Date of this data snapshot. "Days since last visit" is counted from here (A-13).
AS_OF = date(2026, 11, 2)

GRADES = {"primary": [3, 4, 5], "upper_primary": [3, 4, 5, 6, 7, 8]}
ASSESSED_GRADES = GRADES["upper_primary"]   # Grades 1-2 are not assessed in this data (brief: grades 3-8)
FACILITY_FIELDS = ["teacher_posts_sanctioned", "teachers_in_position", "multigrade_classes",
                   "drinking_water", "girls_toilet", "electricity"]


def subjects_for(grade):
    return ["Gujarati", "Maths", "EVS" if grade <= 5 else "Science"]


def num(value):
    """A plain Python number rounded to 1 decimal (whole numbers lose the .0), or None if missing."""
    if value is None or pd.isna(value):
        return None
    value = round(float(value), 1)
    return int(value) if value.is_integer() else value


def grades_mentioned(text):
    # "Grade 7", "Grades 6 to 8", "Grades 4 and 5" -> [7], [6, 8], [4, 5]
    pairs = re.findall(r"Grades? (\d)(?: (?:to|and) (\d))?", text)
    return [int(g) for pair in pairs for g in pair if g]


@dataclass(frozen=True)
class Data:
    schools: pd.DataFrame
    calendar: pd.DataFrame
    attendance: pd.DataFrame
    assessments: pd.DataFrame
    visits: pd.DataFrame
    facilities: pd.DataFrame

    @property
    def open_months(self):
        return sorted(self.calendar.loc[self.calendar.school_open == "yes", "month"])

    @property
    def latest_month(self):
        """The latest month in which school was open and any data arrived."""
        reported = set(self.attendance.month) | set(self.assessments.month)
        return [m for m in self.open_months if m in reported][-1]

    def previous_months(self, month, count=3):
        """The `count` school months before `month` (vacation months are skipped)."""
        months = self.open_months
        i = months.index(month)
        return months[max(0, i - count):i]

    def has_school(self, school_id):
        return school_id in set(self.schools.school_id)

    def school(self, school_id):
        rows = self.schools[self.schools.school_id == school_id]
        if rows.empty:
            raise KeyError(f"unknown school {school_id}")
        return rows.iloc[0]

    def grades(self, school_id):
        return GRADES[self.school(school_id)["type"]]

    def visits_for(self, school_id):
        """Visits to one school, newest first, with days since each visit."""
        rows = self.visits[self.visits.school_id == school_id].sort_values("visit_date", ascending=False)
        return [{"date": r.visit_date, "days_ago": (AS_OF - date.fromisoformat(r.visit_date)).days,
                 "focus_area": r.focus_area, "notes": r.notes, "notes_gu": r.notes_gu} for r in rows.itertuples()]

    def facilities_for(self, school_id):
        row = self.facilities[self.facilities.school_id == school_id].iloc[0]
        facts = {"as_of_date": row.as_of_date}
        for col in FACILITY_FIELDS:
            value = row[col]
            facts[col] = None if pd.isna(value) else (int(value) if col.startswith("teacher") else value)
        return facts


@lru_cache(maxsize=None)
def load(data_dir=DATA_DIR):
    def read(name):
        return pd.read_csv(Path(data_dir) / f"{name}.csv", encoding=ENCODING)
    return Data(**{f.name: read(f.name) for f in fields(Data)})
