"""The web server: the page, /ask, input limits and the rate limit (LLM off, as in all tests)."""
import gzip

import pytest
from fastapi.testclient import TestClient

from saathi import web


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(web, "_recent", web.defaultdict(web.deque))     # fresh rate-limit memory per test
    with TestClient(web.app) as c:
        yield c


def test_page_is_small_self_contained_and_locked_down(client):
    r = client.get("/", headers={"Accept-Encoding": "gzip"})
    assert r.status_code == 200 and "<title>Shiksha Saathi</title>" in r.text
    assert "http://" not in r.text and "https://" not in r.text                 # no external files at all
    assert len(gzip.compress(r.content)) < 13_000     # what travels over patchy 4G: smaller than one photo
    assert "default-src 'self'" in r.headers["content-security-policy"]
    assert r.headers["content-encoding"] == "gzip"


def test_health(client):
    h = client.get("/health").json()
    assert (h["ok"], h["schools"], h["latest_month"], h["llm"]) == (True, 20, "2026-10", False)


def test_ask(client):
    r = client.post("/ask", json={"question": "Which 3 schools need my visit this week?"}).json()
    assert r["intent"] == "top_priority_schools" and "78/100" in r["text"]
    assert r["check"] == {"ai_used": False, "ai_tried": False, "rejected": False, "unsupported": [],
                          "number_words": [], "problem": None, "error": None, "ai_paused": False,
                          "test_checker": None}
    assert [o["label"] for o in r["options"]] == ["Haripar", "Chandrapur", "Manekpur"]
    assert "facts" not in r                                                    # only what the page shows


def test_ask_in_gujarati_and_with_a_pinned_school(client):
    r = client.post("/ask", json={"question": "Tell me about Shimpura", "lang": "gu", "school_id": "GJ-C07-020"}).json()
    assert (r["intent"], r["lang"]) == ("school_summary", "gu") and r["text"].startswith("શિવપુરા")


@pytest.mark.parametrize("body", [
    {"question": ""}, {"question": "x" * 501}, {"question": "hi", "lang": "fr"},
    {"question": "hi", "school_id": "../../etc/passwd"}, {},
])
def test_bad_input_is_refused(client, body):
    assert client.post("/ask", json=body).status_code == 422


def test_rate_limit(client, monkeypatch):
    monkeypatch.setattr(web, "RATE_LIMIT", 3)
    codes = [client.post("/ask", json={"question": "hi"}).status_code for _ in range(4)]
    assert codes == [200, 200, 200, 429]
    other = client.post("/ask", json={"question": "hi"}, headers={"X-Forwarded-For": "10.0.0.9"})
    assert other.status_code == 200                                            # a different person is not blocked


def test_checker_test_needs_the_llm(client):
    r = client.post("/ask", json={"question": "Which 3 schools need my visit this week?", "test_checker": True}).json()
    assert r["check"]["test_checker"] is False                                 # LLM off: nothing to tamper with


def test_ai_budget_for_the_whole_server(client, monkeypatch):
    """A made-up X-Forwarded-For dodges the per-person limit, but not the server's Gemini budget."""
    monkeypatch.setattr(web, "_ai_calls", web.deque())
    monkeypatch.setattr(web, "AI_PER_MINUTE", 2)
    monkeypatch.setattr(web.llm, "enabled", lambda: True)
    monkeypatch.setattr(web, "ask", lambda *a, **k: {"text": "ok", "lang": "en", "intent": "help", "options": [],
                                                      "mode": "rules", "trace": {}})
    paused = [client.post("/ask", json={"question": "hi"}, headers={"X-Forwarded-For": f"10.0.0.{i}"})
              .json()["check"]["ai_paused"] for i in range(3)]
    assert paused == [False, False, True]


def test_forgotten_clients_are_swept(client, monkeypatch):
    monkeypatch.setattr(web, "_recent", web.defaultdict(web.deque, {"1.2.3.4": web.deque([0.0])}))
    web._sweep(now=1000.0)
    assert "1.2.3.4" not in web._recent


def _page_words():
    """The questions and labels the page shows (the JSON block in web/index.html)."""
    import json
    import re
    page = (web.PAGE).read_text(encoding="utf-8")
    return json.loads(re.search(r'<script type="application/json" id="starters">(.*?)</script>', page, re.S).group(1))


def test_every_suggested_question_on_the_page_is_understood():
    """The visit button and the "Try asking" examples are the first things a CRC taps; each must lead to
    the intended answer, in every language."""
    from saathi.assistant import ask
    words = _page_words()
    for lang in ("en", "gu", "hi"):
        assert ask(words["visit"][lang])["intent"] == "top_priority_schools", lang
        assert [ask(q)["intent"] for q in words["examples"][lang]] == [
            "subject_analysis", "attendance_trend", "school_summary"], lang
    # Auto (the reviewer's first view) shows the demo's questions, one of them in Gujarati (D-033)
    assert [ask(q)["intent"] for q in words["examples"]["auto"]] == [
        "subject_analysis", "attendance_trend", "subject_analysis"]


def test_home_screen_labels_match_the_visit_plan_cards():
    """The priority labels on the home screen are the same words as on the cards the server sends."""
    from saathi import reply
    tags = _page_words()["tags"]
    for lang in ("en", "gu"):
        assert tags[lang] == {p: reply.t("lbl_" + p, lang) for p in ("High", "Medium", "Low")}, lang
    assert set(tags["hi"]) == {"High", "Medium", "Low"}


def test_reviewer_tools_are_folded_away(client):
    import re
    page = client.get("/").text
    tag = re.search(r'<details class="review" id="review"[^>]*>', page).group(0)
    assert " open" not in tag and "For reviewers" in page                     # closed until a reviewer opens it


def test_overview_gives_the_months_numbers(client):
    o = client.get("/overview").json()
    assert (o["month"], o["counts"]) == ("2026-10", {"High": 3, "Medium": 4, "Low": 12, "not_enough_data": 1})
    assert [s["en"] for s in o["visit_first"]] == ["Haripar", "Chandrapur", "Manekpur"]
    assert [s["gu"] for s in o["not_enough_data"]] == ["ઉમરવાડા"]
    assert (o["attendance_pct"], o["schools_reporting"], o["schools_total"]) == (81, 19, 20)


@pytest.mark.parametrize("lang", ["en", "gu"])
def test_visit_plan_cards_carry_only_numbers_from_the_facts(lang):
    """Cards never pass through the LLM, and every number on them is in the computed facts."""
    import json
    from saathi.assistant import ask
    from saathi.checker import check
    r = ask("Which 3 schools need my visit this week?", lang=lang)
    cards = r["cards"]
    assert [s["name"] for s in cards["schools"]] == (["Haripar", "Chandrapur", "Manekpur"] if lang == "en"
                                                     else ["હરિપર", "ચંદ્રપુર", "માણેકપુર"])
    assert [(s["priority"], s["score"]) for s in cards["schools"]] == [("High", 78), ("High", 75), ("Medium", 66)]
    assert check(json.dumps(cards, ensure_ascii=False), r["facts"]).ok
    assert ask("Why is Grade 5 maths low in Rampura?")["cards"] is None      # other answers stay text


def test_home_screen_tiles_are_understood_in_every_language():
    from saathi.assistant import ask
    tiles = _page_words()["tiles"]
    for lang in ("en", "gu", "hi"):
        assert [ask(q)["intent"] for q in tiles[lang]] == [
            "attendance_trend", "class_overview", "missing_data", "officer_summary"], lang


def _bar_pattern():
    """The page's attendance-bar pattern in Python (re.ASCII: JavaScript's \\d reads ASCII digits only)."""
    import re
    js = re.search(r"const pct = line\.match\(/(.+?)/\);", web.PAGE.read_text(encoding="utf-8")).group(1)
    return re.compile(js, re.ASCII)


@pytest.mark.parametrize("lang", ["en", "gu"])
def test_attendance_bars_go_on_every_month_with_a_figure_and_nowhere_else(lang):
    """The page draws a bar under a reply line only when the line matches its pattern, as wide as the line's
    first figure. Checked on real replies: every month with a children's figure gets a bar of exactly that
    figure (each school, and the cluster); a month with no figure, and every other kind of answer, gets none."""
    from saathi import analytics
    from saathi.assistant import ask
    from saathi.data import load
    bar, data = _bar_pattern(), load()

    def bars(question):
        return [float(m.group(1)) for m in map(bar.match, ask(question, lang=lang)["text"].splitlines()) if m]

    for school_id, village in zip(data.schools.school_id, data.schools.village):
        want = [r["student_attendance_pct"] for r in analytics.attendance_months(data, school_id)
                if r["status"] == "recorded" and r["student_attendance_pct"] is not None]
        assert bars(f"Show attendance trend for {village}") == want, village
    # Umarvada: June-August recorded, September's children figure blank, October missing.
    assert bars("What was Umarvada's attendance in October?") == [81.5, 79.4, 80.1]
    assert bars("Show attendance trend") == [r["student_attendance_pct"] for r in analytics.cluster_attendance(data)
                                             if r["status"] == "recorded"]
    for question in ["Which 3 schools need my visit this week?", "Why is Grade 5 Maths low in Rampura?",
                     "Tell me about Chandrapur", "Which schools have missing data?", "Summary for my block officer",
                     "When did I last visit Sonpura?"]:
        assert bars(question) == [], question


def _page_pattern(js):
    """A regular expression lifted from the page's own code (re.ASCII: JavaScript's \\d reads ASCII digits only)."""
    import re
    return re.compile(re.search(js, web.PAGE.read_text(encoding="utf-8")).group(1), re.ASCII)


def _month_rows(text):
    """The page's month rows, ported: lines with a figure, and their neighbours that name a month without one."""
    bar, month = _bar_pattern(), _page_pattern(r"const MONTH = /(.+?)/;")
    lines = text.split("\n")
    rows = [bool(bar.match(line)) for line in lines]
    for _ in range(2):
        for i, line in enumerate(lines):
            if month.match(line) and ((i > 0 and rows[i - 1]) or (i + 1 < len(lines) and rows[i + 1])):
                rows[i] = True
    return [line.split(": ")[0] for line, row in zip(lines, rows) if row]


@pytest.mark.parametrize("lang, months", [("en", ["May", "June", "July", "August", "September", "October"]),
                                          ("gu", ["મે", "જૂન", "જુલાઈ", "ઑગસ્ટ", "સપ્ટેમ્બર", "ઑક્ટોબર"])])
def test_month_rows_hold_every_month_and_nothing_else(lang, months):
    """One row per month (D-034): a closed month and a month with no record keep their words in a row of their own,
    so a gap is said, never dropped; the line about the cluster under them is not taken as a month."""
    from saathi.assistant import ask
    assert _month_rows(ask("What was Umarvada's attendance in October?", lang=lang)["text"]) == months
    assert _month_rows(ask("Show attendance trend", lang=lang)["text"]) == months
    for question in ["Which 3 schools need my visit this week?", "Why is Grade 5 Maths Low in Rampura?",
                     "Tell me about Chandrapur", "Which schools have missing data?", "Summary for my block officer"]:
        assert _month_rows(ask(question, lang=lang)["text"]) == [], question


@pytest.mark.parametrize("lang", ["en", "gu"])
def test_trend_columns_carry_the_computed_trend(lang):
    """A class's trend is drawn as columns only when every month has a figure, and the columns carry exactly the
    computed figures; a month without one leaves the line in words (D-034)."""
    from saathi.assistant import ask
    from saathi.data import load
    whole = _page_pattern(r"const m = text\.match\(/(.+?)/\), pts")
    point = _page_pattern(r'pts = m && m\[2\]\.split\(" → "\)\.map\(\(p\) => p\.match\(/(.+?)/\)\);')
    drawn = 0
    for village in load().schools.village:
        r = ask(f"Why is Grade 5 Maths low in {village}?", lang=lang)
        line = next(x[2:] for x in r["text"].splitlines() if x.startswith("• ") and " → " in x)
        points = [point.match(p) for p in whole.match(line).group(2).split(" → ")]
        want = [x["avg_score_pct"] for x in r["facts"]["trend"]]
        if None in want:
            assert not all(points), village
        else:
            assert [float(p.group(2)) for p in points] == want, village
            drawn += 1
    assert drawn >= 15
    assert not all(point.match(p) for p in "June 45% → July no data → August 41%".split(" → "))


def _folded(text):
    """The sections the page folds, ported: a short line ending in ':' with bullets under it, after an earlier list."""
    import re
    lines = [line.rstrip() for line in text.split("\n")]
    folded, lists, in_list, first = [], 0, False, True
    for i, line in enumerate(lines):
        if not line.strip():
            in_list = False
            continue
        if first:
            first = False
            continue
        if line.startswith("• "):
            lists, in_list = lists + (not in_list), True
            continue
        in_list = False
        if re.match(r"^\d+\.\s", line):
            lists += 1
        elif line.endswith(":") and len(line) < 70:
            n = 0
            while i + 1 + n < len(lines) and lines[i + 1 + n].startswith("• "):
                n += 1
            if lists and n:
                folded.append(line)
                in_list = True
    return folded


@pytest.mark.parametrize("lang", ["en", "gu"])
def test_only_later_lists_fold_and_a_missing_score_never_does(lang):
    """Folds hide nothing that decides a visit (D-034): the first list of an answer and the data that blocks a score
    stay in view; later lists (visit notes, the other gaps) fold under their own title and count. The visit plan
    never folds as text, and on cards its missing-data line sits outside the fold."""
    from saathi import reply
    from saathi.assistant import ask
    assert _folded(ask("Why is Grade 5 Maths low in Rampura?", lang=lang)["text"]) == [reply.t("visit_notes", lang)]
    gaps = ask("Which schools have missing data?", lang=lang)["text"]
    assert _folded(gaps) == [reply.t("gaps_other", lang)]
    assert reply.t("gaps_not_enough", lang, month=reply.month("2026-10", lang)) in gaps     # in view, above the fold
    for question in ["Show attendance trend", "What was Umarvada's attendance in October?", "Tell me about Chandrapur",
                     "Summary for my block officer"]:
        assert _folded(ask(question, lang=lang)["text"]) == [], question
    page = web.PAGE.read_text(encoding="utf-8")
    assert "if (folds && lists && n) {" in page                  # the rule ported above, as the page runs it
    assert 'r.intent !== "top_priority_schools"' in page
    cards = ask("Which 3 schools need my visit this week?", lang=lang)["cards"]
    assert [m.split(":")[0] for m in cards["missing"]] == [reply.short({"name": "Umarvada", "name_gu": "ઉમરવાડા"}, lang)]
    assert not any(m in cards["also"] for m in cards["missing"])
