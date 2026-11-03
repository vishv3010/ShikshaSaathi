"""Build docs/Solution_Note.pdf from docs/SOLUTION_NOTE.md (the brief allows 2 pages at most).

Markdown -> HTML with print styles -> PDF with headless Chrome, in a throw-away
browser profile. Fails if the PDF is longer than two pages.

Run:  .venv/bin/python scripts/build_note.py        (needs requirements-dev.txt and Chrome or Chromium)
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "docs" / "SOLUTION_NOTE.md"
TARGET = ROOT / "docs" / "Solution_Note.pdf"
MAX_PAGES = 2

STYLE = """
@page { size: A4; margin: 11mm 13mm 11mm 13mm; }
body { font: 8.9pt/1.36 "Noto Sans", "Segoe UI", Roboto, Arial, "Noto Sans Gujarati", sans-serif; color: #111; }
h1 { font-size: 15pt; margin: 0 0 3pt; color: #075e54; }
h2 { font-size: 10.6pt; margin: 8pt 0 3pt; color: #075e54; border-bottom: 1px solid #cfe3df; padding-bottom: 1pt; }
p { margin: 0 0 4pt; }
ul, ol { margin: 0 0 4pt; padding-left: 15pt; }
li { margin: 0 0 1.5pt; }
table { border-collapse: collapse; width: 100%; margin: 2pt 0 5pt; font-size: 8.3pt; }
th, td { border: 1px solid #cfd8dc; padding: 2pt 4pt; vertical-align: top; text-align: left; }
th { background: #eef5f3; }
code { font-size: 8.2pt; }
strong { color: #000; }
"""


def chrome():
    for name in (os.environ.get("CHROME"), "google-chrome", "google-chrome-stable", "chromium", "chromium-browser"):
        if name and shutil.which(name):
            return shutil.which(name)
    sys.exit("Chrome or Chromium not found (set CHROME=/path/to/chrome)")


def pages(pdf):
    if shutil.which("pdfinfo"):
        out = subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True).stdout
        return int(re.search(r"Pages:\s+(\d+)", out).group(1))
    return len(re.findall(rb"/Type\s*/Page[^s]", pdf.read_bytes()))


def main():
    body = markdown.markdown(SOURCE.read_text(encoding="utf-8"), extensions=["tables"])
    html = (f'<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Shiksha Saathi: solution note</title>'
            f"<style>{STYLE}</style></head><body>{body}</body></html>")
    with tempfile.TemporaryDirectory() as tmp:
        page = Path(tmp) / "note.html"
        page.write_text(html, encoding="utf-8")
        subprocess.run([chrome(), "--headless=new", "--disable-gpu", "--no-first-run", f"--user-data-dir={tmp}/profile",
                        "--no-pdf-header-footer", f"--print-to-pdf={TARGET}", page.as_uri()],
                       check=True, capture_output=True)
    count = pages(TARGET)
    print(f"{TARGET.relative_to(ROOT)}: {count} page(s), {TARGET.stat().st_size // 1024} KB")
    if count > MAX_PAGES:
        sys.exit(f"Too long: {count} pages, the brief allows {MAX_PAGES}. Shorten docs/SOLUTION_NOTE.md.")


if __name__ == "__main__":
    main()
