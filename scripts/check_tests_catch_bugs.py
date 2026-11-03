"""Plant known bugs, one at a time, in a throwaway copy of the code and check the tests catch each one.

A test suite that never fails proves nothing. Exit code 1 if any bug slips through.

Run:  .venv/Scripts/python scripts/check_tests_catch_bugs.py
"""
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# (the bug, file, correct code, buggy code); a bug that needs several edits gives lists of both
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
    # Python's \d already reads Gujarati digits, so the digit conversion is a second layer; the real bug
    # (as in a JavaScript port, where \d is ASCII-only) removes both.
    ("number checker blind to Gujarati and Devanagari digits", "saathi/checker.py",
     ["    text = text.translate(DIGITS)\n    if list_markers:", 'NUMBER = re.compile(r"\\d+(?:\\.\\d+)?")'],
     ["    if list_markers:", 'NUMBER = re.compile(r"[0-9]+(?:\\.[0-9]+)?")']),
    ("Hindi translation allowed to drop lines", "saathi/llm_steps.py",
     'f"dropped numbers {dropped}" if dropped else None', "None"),
]


def main():
    missed = 0
    for label, path, correct, buggy in BUGS:
        with tempfile.TemporaryDirectory() as tmp:
            copy = Path(tmp) / "repo"
            shutil.copytree(ROOT, copy, ignore=shutil.ignore_patterns(".venv", ".git", "__pycache__", ".pytest_cache",
                                                                  ".env", "logs"))   # never copy the key
            target = copy / path
            code = target.read_text(encoding="utf-8")
            edits = zip(correct, buggy) if isinstance(correct, list) else [(correct, buggy)]
            for old, new in edits:
                if old not in code:
                    sys.exit(f"cannot plant '{label}': {path} has changed, update this script")
                code = code.replace(old, new)
            target.write_text(code, encoding="utf-8")
            # UTF-8 both ways: test output holds Gujarati and Hindi, which Windows' default code page cannot.
            result = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider"],
                                    cwd=copy, capture_output=True, encoding="utf-8", errors="replace",
                                    env={**os.environ, "PYTHONUTF8": "1"})
        caught = result.returncode != 0
        missed += not caught
        summary = (result.stdout.strip().splitlines() or ["no output"])[-1]
        print(f"{'caught' if caught else 'MISSED'}  {label}  ({summary})")
    sys.exit(1 if missed else 0)


if __name__ == "__main__":
    main()
