"""Vercel entry point: the same FastAPI app that `uvicorn saathi.web:app` runs locally."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))   # so `saathi` imports from the project root

from saathi.web import app  # noqa: E402,F401
