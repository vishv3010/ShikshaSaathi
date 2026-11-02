"""The validator must catch broken data, not only pass good data."""
import shutil
import subprocess
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
ENCODING = "utf-8-sig"


def test_validator_passes_the_real_data():
    result = subprocess.run([sys.executable, str(ROOT / "scripts" / "validate_data.py")],
                            capture_output=True, text=True)
    assert result.returncode == 0, result.stdout


def test_validator_catches_planted_errors(tmp_path):
    bad = tmp_path / "data"
    shutil.copytree(ROOT / "data", bad)
    primary = set(pd.read_csv(bad / "schools.csv", encoding=ENCODING).query("type == 'primary'").school_id)

    a = pd.read_csv(bad / "attendance.csv", encoding=ENCODING)
    a = pd.concat([a, a.iloc[[0]], a.iloc[[2]].assign(month="2026-05")], ignore_index=True)
    a.loc[1, "student_attendance_pct"] = 120                     # out of range
    a.to_csv(bad / "attendance.csv", index=False, encoding=ENCODING)

    x = pd.read_csv(bad / "assessments.csv", encoding=ENCODING)
    x.loc[0, "school_id"] = "GJ-C07-099"                         # unknown school
    x.loc[x[x.school_id.isin(primary)].index[0], "grade"] = 7    # Grade 7 at a primary school
    x.to_csv(bad / "assessments.csv", index=False, encoding=ENCODING)

    v = pd.read_csv(bad / "visits.csv", encoding=ENCODING)
    v.loc[v[v.school_id.isin(primary)].index[0], "notes"] = "Observed a Grade 8 science class."
    v.to_csv(bad / "visits.csv", index=False, encoding=ENCODING)

    result = subprocess.run([sys.executable, str(ROOT / "scripts" / "validate_data.py"), str(bad)],
                            capture_output=True, text=True)
    assert result.returncode == 1
    for message in ["duplicate rows", "unknown school_id", "values outside 0-100", "closed or unknown months",
                    "rows for grades the school does not have", "notes mention grades"]:
        assert message in result.stdout, message
