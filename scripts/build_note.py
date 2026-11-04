"""Build docs/Solution_Note.pdf from docs/SOLUTION_NOTE.md (the brief allows 2 pages at most).

Markdown -> HTML with print styles -> PDF with headless Chrome (or Edge), in a throw-away
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
@page { size: A4; margin: 12mm 14mm 11mm 14mm; }
* { box-sizing: border-box; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
body { font: 9.3pt/1.42 "Segoe UI", "Noto Sans", Roboto, Arial, "Nirmala UI", "Noto Sans Gujarati", sans-serif;
       color: #1f2a2e; margin: 0; }
a { color: #0b6e5f; text-decoration: none; }
.masthead { border-bottom: 2px solid #0b6e5f; padding-bottom: 6pt; margin-bottom: 8pt; }
.kicker { font-size: 7.8pt; letter-spacing: .08em; text-transform: uppercase; color: #5b6f73; font-weight: 600; }
h1 { font-size: 23pt; line-height: 1.1; margin: 2pt 0 3pt; color: #0b4f45; }
.byline { font-size: 8.2pt; color: #5b6f73; }
h2 { font-size: 11.2pt; margin: 10pt 0 4pt; color: #0b4f45; border-left: 3pt solid #0b6e5f; padding-left: 6pt;
     break-after: avoid; }
p { margin: 0 0 5pt; }
ul, ol { margin: 0 0 5pt; padding-left: 14pt; }
li { margin: 0 0 2.4pt; }
strong { color: #0f1a1d; }
code { font: 8.2pt Consolas, "Courier New", monospace; }
.lead { background: #eef6f4; border-left: 3pt solid #0b6e5f; border-radius: 0 4pt 4pt 0; padding: 7pt 10pt;
        margin: 0 0 8pt; font-size: 9.7pt; }
.stats { display: flex; gap: 6pt; margin: 0 0 2pt; }
.stats > div { flex: 1; border: 1px solid #d6e6e2; border-radius: 5pt; padding: 5pt 7pt; font-size: 7.8pt;
               line-height: 1.3; color: #4a5c60; }
.stats b { display: block; font-size: 15pt; line-height: 1.15; color: #0b6e5f; }
.flow { display: flex; gap: 3pt; margin: 2pt 0 7pt; break-inside: avoid; }
.step { flex: 1; border: 1px solid #d6e6e2; border-radius: 5pt; padding: 5pt 6pt; background: #f7fbfa;
        font-size: 7.9pt; line-height: 1.32; }
.step b { display: block; margin-bottom: 2pt; font-size: 8.5pt; color: #0b4f45; }
.step.ai { background: #fff7e8; border-color: #efd7a2; } .step.ai b { color: #8a5a00; }
.step.check { background: #edf7ee; border-color: #c7e2c9; } .step.check b { color: #2e6a33; }
.arrow { display: flex; align-items: center; font-weight: 700; color: #0b6e5f; }
table { border-collapse: collapse; width: 100%; margin: 3pt 0 6pt; font-size: 8.5pt; break-inside: avoid; }
th, td { border: 1px solid #d6e6e2; padding: 3pt 6pt; vertical-align: top; text-align: left; }
th { background: #eef6f4; color: #0b4f45; }
.two { display: flex; gap: 8pt; margin: 2pt 0 6pt; }
.two > div { flex: 1; border: 1px solid #d6e6e2; border-radius: 5pt; padding: 6pt 8pt; background: #f7fbfa; }
.two b { display: block; margin-bottom: 2pt; color: #0b4f45; }
.callout { background: #0b4f45; color: #fff; border-radius: 5pt; padding: 6pt 10pt; margin: 3pt 0 4pt; }
.callout b { color: #fff; }
.foot { margin-top: 9pt; padding-top: 5pt; border-top: 1px solid #d6e6e2; font-size: 7.7pt; color: #5b6f73; }
"""

WINDOWS_BROWSERS = (r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
                    r"C:\Program Files\Google\Chrome\Application\chrome.exe")


def chrome():
    for name in (os.environ.get("CHROME"), "google-chrome", "google-chrome-stable", "chromium", "chromium-browser",
                 *WINDOWS_BROWSERS):
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
