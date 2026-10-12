from fastapi.testclient import TestClient

from app.main import app
from app.review import make_diff

client = TestClient(app)


def test_health():
    assert client.get("/api/health").json()["status"] == "ok"


def test_review_static_only():
    r = client.post("/api/review", json={"code": "x = eval(input())\n", "language": "python", "use_ai": False})
    assert r.status_code == 200
    body = r.json()
    assert body["ai_used"] is False
    assert any(f["rule_id"] == "B307" for f in body["findings"])
    assert body["summary"]["score"] < 100


def test_empty_code_rejected():
    assert client.post("/api/review", json={"code": "  ", "use_ai": False}).status_code == 400


def test_ai_failure_falls_back(monkeypatch):
    import app.review as rv

    async def boom(*a, **k):
        raise RuntimeError("no model")
    monkeypatch.setattr(rv, "review_with_gemma", boom)
    r = client.post("/api/review", json={"code": "x = eval(input())\n", "use_ai": True}).json()
    assert r["ai_used"] is False and r["ai_error"] and r["findings"]


def test_ai_merge_and_patch(monkeypatch):
    import app.review as rv

    async def fake(code, lang, static):
        return {"findings": [{"title": "Eval", "severity": "high", "line_start": 1, "explanation": "Friendly text",
                              "why_it_matters": "bad", "suggested_fix": "use literal_eval"},
                             {"title": "Odd", "severity": "low", "line_start": 2, "explanation": "hmm", "confidence": 0.99}],
                "fixed_code": "import ast\nx = ast.literal_eval(input())\n"}
    monkeypatch.setattr(rv, "review_with_gemma", fake)
    r = client.post("/api/review", json={"code": "x = eval(input())\ny = 1\n", "use_ai": True}).json()
    ev = next(f for f in r["findings"] if f["rule_id"] == "B307")
    assert ev["explanation"] == "Friendly text" and ev["verified_by_static"]
    ai_only = next(f for f in r["findings"] if f["source"] == "gemma")
    assert ai_only["confidence"] <= 0.7 and not ai_only["verified_by_static"]
    assert r["fixed_code"] and r["diff_rows"]


def test_invalid_patch_discarded(monkeypatch):
    import app.review as rv

    async def fake(*a, **k):
        return {"findings": [], "fixed_code": "def broken(:"}
    monkeypatch.setattr(rv, "review_with_gemma", fake)
    r = client.post("/api/review", json={"code": "x = 1\n", "use_ai": True}).json()
    assert r["fixed_code"] is None


def test_diff_rows():
    rows = make_diff("a\nb\n", "a\nc\nd\n")
    assert [r.tag for r in rows] == ["equal", "replace", "insert"]
