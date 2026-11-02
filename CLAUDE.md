# Shiksha Saathi

AI assistant for a Cluster Resource Coordinator (CRC) in Gujarat: answers "which schools need attention this month, and what will you do about it?" from school data, in Gujarati, English (and Hindi), in under two minutes of her time.

This is the ConveGenius "CG AI Build" assignment. Brief: `../Assignment - Vishv Patel.pdf`. Due Wed 4 Nov 2026, 11:59 PM. Time budget 12–15 hours total.

The plan of record is `docs/PLAN.md`.

## Non-negotiable rules

- **Free tools only.** LLM is the Gemini API free tier; hosting, libraries and video tools must be free too.
- **The app must answer correctly with the LLM switched off** (keyword intent + templates), so a quota error never breaks a demo.

- **Numbers come from code, never from the LLM.** The LLM picks a tool and phrases the reply; Python computes every figure. Every number in a reply must be traceable to a tool result.
- **Missing data is said out loud.** Never fill a gap with a guess. "Not applicable" (e.g. a primary school has no Grade 6–8) is different from "missing".
- **Never state a cause the data cannot show.** Suggest what to check on the visit; cite visit notes when they exist.
- **Flag patterns, not people.** No blame on schools, teachers or head teachers. Low teacher attendance may be official duty.
- **Synthetic data only.** No real student, teacher or school names.
- **Short replies.** She reads on a basic Android phone over patchy 4G.

## Commands

- Python 3.10 in `.venv` (`.venv/Scripts/python` on Windows).
- `scripts/generate_data.py` rebuilds `data/` (seed 7, byte-identical output); `scripts/validate_data.py [data_dir]` must pass after any data change.
- CSVs are UTF-8 with BOM; read them with `encoding="utf-8-sig"`.

## How we work

- Every non-obvious choice goes in `docs/DECISIONS.md`; every assumption in `docs/ASSUMPTIONS.md` (the reviewer explicitly asked for assumptions).
- Log AI use in `docs/AI_USAGE_LOG.md` as we go, including where AI output was wrong and how it was caught.
- Small commits with clear messages, so history shows the process.
- Vishv makes the final call on design decisions and must be able to explain each one.

## Applied Learning
