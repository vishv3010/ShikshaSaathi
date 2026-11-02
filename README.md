# Shiksha Saathi

AI assistant that turns school assessment data into clear next steps for a Cluster Resource Coordinator (CRC) — Gujarati and English, grounded in data.

CG AI Build assignment · due 4 Nov 2026.

_Work in progress — the assistant itself and the solution note are still to come._

## Dataset

Synthetic data for 20 schools in one cluster, May–October 2026, in [`data/`](data/). How it was made: [docs/DATASET.md](docs/DATASET.md).

```
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\python scripts\generate_data.py
.venv\Scripts\python scripts\validate_data.py
```

## Docs

- [Development plan](docs/PLAN.md): architecture, data design, scoring, tests and schedule
- [Dataset notes](docs/DATASET.md): how the synthetic data was generated, the designed stories, and what is missing on purpose
- [Research notes](docs/RESEARCH.md): the local system, the government grading method we borrowed from, and why schools struggle
- [Decisions](docs/DECISIONS.md): every non-obvious design choice and why
- [Assumptions](docs/ASSUMPTIONS.md): what the brief left open and what we assumed
- [AI usage log](docs/AI_USAGE_LOG.md): which AI tools were used, for what, and what was checked by hand
