"""How well is a question understood? Scores the reader on question sets it was not built from.

Each row of eval/*.csv gives a question, the acceptable question types (separated by |),
and, where it matters, the school, grade and subject. A row passes only if all of them
are right. Reports rules alone, and rules with Gemini for the questions the rules cannot
place (what the app does). Gemini mode needs GEMINI_API_KEY and uses a little quota.

Run:  .venv/bin/python scripts/eval_understanding.py eval/round1.csv [--llm]
"""
import argparse
import csv
import sys
import time
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from saathi import data as data_module, llm, llm_steps  # noqa: E402
from saathi.understand import parse  # noqa: E402


def read(path):
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def understood(question, data, use_llm):
    q = parse(question, data)
    by = "rules"
    if use_llm and q.intent == "out_of_scope":
        better, _usage = llm_steps.understand_question(question, data)
        if better:
            q, by = better, "gemini"
    return q, by


def problems(row, q):
    wrong = []
    if q.intent not in row["intents"].split("|"):
        wrong.append(f"type {q.intent} (want {row['intents']})")
    if row["school_id"] and q.school_ids != [row["school_id"]]:
        wrong.append(f"school {q.school_ids} (want {row['school_id']})")
    if row["grade"] and q.grade != int(row["grade"]):
        wrong.append(f"grade {q.grade} (want {row['grade']})")
    if row["subject"] and q.subject != row["subject"]:
        wrong.append(f"subject {q.subject} (want {row['subject']})")
    return wrong


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("csv", nargs="+")
    parser.add_argument("--llm", action="store_true", help="let Gemini read what the rules cannot place")
    parser.add_argument("--pause", type=float, default=6.0, help="seconds after each Gemini call (free tier)")
    args = parser.parse_args()
    if args.llm and not llm.enabled():
        sys.exit("--llm needs GEMINI_API_KEY (and SAATHI_LLM not off)")

    data = data_module.load()
    rows = [row for path in args.csv for row in read(path)]
    passed, groups, failures, gemini_calls = 0, defaultdict(lambda: [0, 0]), [], 0
    for row in rows:
        q, by = understood(row["question"], data, args.llm)
        if by == "gemini" or (args.llm and parse(row["question"], data).intent == "out_of_scope"):
            gemini_calls += 1
            time.sleep(args.pause)
        wrong = problems(row, q)
        groups[row["group"]][1] += 1
        if wrong:
            failures.append(f"  [{row['group']}] {row['question']}  ->  {'; '.join(wrong)}  (read by {by})")
        else:
            passed += 1
            groups[row["group"]][0] += 1

    mode = "rules + Gemini for unplaced questions" if args.llm else "rules only"
    print(f"{mode}: {passed}/{len(rows)} understood correctly ({100 * passed / len(rows):.0f}%)"
          + (f"; Gemini asked {gemini_calls} times" if args.llm else ""))
    print("  " + " · ".join(f"{g} {ok}/{n}" for g, (ok, n) in groups.items()))
    if failures:
        print("missed:")
        print("\n".join(failures))


if __name__ == "__main__":
    main()
