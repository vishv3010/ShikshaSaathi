"""Entry point for hosts that look for a FastAPI `app` in main.py (Vercel).
Locally the same app runs with:  uvicorn saathi.web:app"""
from saathi.web import app  # noqa: F401
