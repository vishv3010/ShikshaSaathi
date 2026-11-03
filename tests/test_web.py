"""The web server: the page, /ask, input limits and the rate limit (LLM off, as in all tests)."""
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
    assert len(r.content) < 20_000                                              # one small file for patchy 4G
    assert "default-src 'self'" in r.headers["content-security-policy"]
    assert r.headers["content-encoding"] == "gzip"


def test_health(client):
    h = client.get("/health").json()
    assert (h["ok"], h["schools"], h["latest_month"], h["llm"]) == (True, 20, "2026-10", False)


def test_ask(client):
    r = client.post("/ask", json={"question": "Which 3 schools need my visit this week?"}).json()
    assert r["intent"] == "top_priority_schools" and "78/100" in r["text"]
    assert r["check"] == {"ai_used": False, "ai_tried": False, "rejected": False, "unsupported": [],
                          "number_words": [], "problem": None, "error": None, "test_checker": None}
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
