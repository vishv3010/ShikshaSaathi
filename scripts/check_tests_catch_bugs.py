"""Plant known bugs, one at a time, in a throwaway copy of the code and check the tests catch each one.

A test suite that never fails proves nothing. Exit code 1 if any bug slips through.

Run:  .venv/Scripts/python scripts/check_tests_catch_bugs.py
"""
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# (the bug, file, correct code, buggy code)
BUGS = [
    ("attendance band moved from 70 to 75", "saathi/scoring.py",
     "(None, 70, 25), (70, 80, 18)", "(None, 75, 25), (75, 80, 18)"),
    ("missing values turned into 0", "saathi/data.py",
     "        return None\n    value = round", "        return 0\n    value = round"),
    ("recent-visit rule switched off", "saathi/scoring.py",
     "RECENT_VISIT_DAYS = 14", "RECENT_VISIT_DAYS = -1"),
    ("teacher-availability rule skipped", "saathi/actions.py",
     "if teacher is not None and teacher < TEACHER_LOW:", "if False:"),
    ("requests to change rules or data no longer refused", "saathi/understand.py",
     "if _any(norm, NOT_ALLOWED):", "if False:"),
    ("questions blaming teachers no longer declined", "saathi/understand.py",
     "if about_people and (_any(norm, JUDGEMENT)", "if False and (_any(norm, JUDGEMENT)"),
    ("a month with no attendance record not reported", "saathi/reply.py",
     '        if row["status"] == "missing":', '        if False:'),
    ("above / below the cluster average swapped", "saathi/reply.py",
     '"cmp_below" if d < 0 else "cmp_above" if d > 0', '"cmp_below" if d > 0 else "cmp_above" if d < 0'),
]


def main():
    missed = 0
    for label, path, correct, buggy in BUGS:
        with tempfile.TemporaryDirectory() as tmp:
            copy = Path(tmp) / "repo"
            shutil.copytree(ROOT, copy, ignore=shutil.ignore_patterns(".venv", ".git", "__pycache__", ".pytest_cache"))
            target = copy / path
            code = target.read_text(encoding="utf-8")
            if correct not in code:
                sys.exit(f"cannot plant '{label}': {path} has changed, update this script")
            target.write_text(code.replace(correct, buggy), encoding="utf-8")
            result = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider"],
                                    cwd=copy, capture_output=True, text=True)
        caught = result.returncode != 0
        missed += not caught
        print(f"{'caught' if caught else 'MISSED'}  {label}  ({result.stdout.strip().splitlines()[-1]})")
    sys.exit(1 if missed else 0)


if __name__ == "__main__":
    main()
