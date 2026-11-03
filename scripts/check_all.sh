#!/usr/bin/env bash
# Every check, in one go, before a deploy or a submission. Stops at the first failure.
#   bash scripts/check_all.sh            (add --no-llm to skip the live Gemini run)
set -euo pipefail
cd "$(dirname "$0")/.."
PY=.venv/bin/python
step() { printf '\n== %s\n' "$1"; }

step "1/6 Data: validator"
$PY scripts/validate_data.py | tail -1

step "2/6 Tests (never call Gemini)"
$PY -m pytest -q | tail -1

step "3/6 Understanding: question sets, rules only"
for f in eval/round1.csv eval/round2.csv; do SAATHI_LLM=off $PY scripts/eval_understanding.py "$f" | head -1; done

step "4/6 Planted bugs: the tests must catch every one"
$PY scripts/check_tests_catch_bugs.py | sed 's/  (.*//'

step "5/6 Fresh copy, started the way the README says (no key: rules only)"
TMP=$(mktemp -d)
PORT=8765
git clone -q . "$TMP/repo"
python3 -m venv "$TMP/repo/.venv"
"$TMP/repo/.venv/bin/pip" install -q -r "$TMP/repo/requirements.txt"
cd "$TMP/repo"
SAATHI_LLM=off .venv/bin/uvicorn saathi.web:app --port $PORT > "$TMP/server.log" 2>&1 &
SERVER=$!
cd - > /dev/null
timeout 40 bash -c "until curl -sf http://127.0.0.1:$PORT/health >/dev/null; do sleep 0.5; done"
curl -s "http://127.0.0.1:$PORT/health"; echo
for q in "Which 3 schools need my visit this week?" "What was Umarvada's attendance in October?" "Which teacher is lazy?"; do
  curl -s -X POST "http://127.0.0.1:$PORT/ask" -H 'Content-Type: application/json' -d "{\"question\": \"$q\"}" \
    | $PY -c "import json,sys; r=json.load(sys.stdin); print('  ok |', r['intent'], '|', r['text'].splitlines()[0][:70])"
done
curl -s -o /dev/null -w "  page: HTTP %{http_code}, %{size_download} bytes\n" -H 'Accept-Encoding: gzip' "http://127.0.0.1:$PORT/"
kill "$SERVER" && wait "$SERVER" 2>/dev/null || true     # stop the temporary server quietly
rm -rf "$TMP"

if [ "${1:-}" != "--no-llm" ]; then
  step "6/6 Live Gemini on the demo questions"
  $PY scripts/try_llm.py --quiet | grep -E "^\[|^answers|^Gemini"
fi
printf '\nALL CHECKS PASSED\n'
