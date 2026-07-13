"""Tests Integrity Gate — Decision Case site/29 + resolver."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from api.main import app
from api.services import explainable_decision_service as eds
from api.services import site_entity_resolver

CLIENT = TestClient(app)
ROOT = Path(__file__).resolve().parents[1]
HISTORY = ROOT / "data" / "decision" / "case_history.json"


def test_case_history_is_valid_json():
    raw = HISTORY.read_text(encoding="utf-8")
    import json

    payload = json.loads(raw)
    assert isinstance(payload.get("history"), list)


def test_append_history_never_breaks_case_on_corrupt_file(tmp_path, monkeypatch):
    bad = tmp_path / "case_history.json"
    bad.write_text('{"history":[]}\n{"extra":true}', encoding="utf-8")
    monkeypatch.setattr(eds, "HISTORY_PATH", bad)
    case = eds.get_decision_case("29", asset_type="site", program_code="sites_40")
    assert case is not None
    assert case["asset"]["site_name"] or case["asset"]["name"]


def test_resolver_site_29_sites_40():
    resolved = site_entity_resolver.resolve_site(29, program_code="sites_40")
    assert resolved["resolved"] is True
    assert resolved["site_id"] == 29
    assert resolved["site_name"]
    assert "29" not in str(resolved["site_name"]) or resolved["site_name"] != "29"
    assert resolved["program_code"] == "sites_40"


def test_api_case_site_29_ok():
    res = CLIENT.get("/api/decision/case/29?asset_type=site&program_code=sites_40")
    assert res.status_code == 200, res.text
    body = res.json()
    name = body["asset"].get("site_name") or body["asset"].get("name")
    assert name
    assert str(name) != "29"
    assert body["score"]["global"] is not None
    assert body["score"].get("priority_label") or body["score"].get("priority_level")


def test_api_case_sites_7_30_and_missing():
    for sid in (7, 30):
        res = CLIENT.get(f"/api/decision/case/{sid}?asset_type=site&program_code=sites_40")
        assert res.status_code == 200, (sid, res.text)
        body = res.json()
        assert body["asset"].get("site_name") or body["asset"].get("name")

    # programme 300 — au moins un site résolvable ou 404 métier propre
    res300 = CLIENT.get("/api/decision/case/7?asset_type=site&program_code=sites_300")
    assert res300.status_code in {200, 404}

    missing = CLIENT.get("/api/decision/case/99999999?asset_type=site&program_code=sites_40")
    assert missing.status_code == 404
