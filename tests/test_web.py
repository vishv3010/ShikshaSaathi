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
    assert len(gzip.compress(r.content)) < 12_000     # what travels over patchy 4G: smaller than one photo
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
    # Auto (the reviewer's first view) shows the demo's questions, one of them in Hindi
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
