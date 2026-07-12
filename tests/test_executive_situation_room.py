"""Tests Executive Situation Room v1.0."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from api.main import app
from api.services import executive_situation_room_service as esr

CLIENT = TestClient(app)
ROOT = Path(__file__).resolve().parents[1]
ESR_DIR = ROOT / "dashboard" / "modules" / "shared" / "executive-situation-room"


def test_esr_frontend_files_exist():
    assert (ESR_DIR / "executive-situation-room.js").exists()
    assert (ESR_DIR / "executive-situation-room.css").exists()
    html = (ROOT / "dashboard/index.html").read_text(encoding="utf-8")
    assert "executive-situation-room.js" in html
    assert "executive-situation-room.css" in html


def test_briefing_is_sourced_not_invented():
    briefing = esr.build_briefing()
    assert briefing["_meta"]["principle"]
    assert "invent" in briefing["_meta"]["principle"].lower() or "inventée" in briefing["_meta"]["principle"].lower()
    assert briefing["headline"]
    assert "stats_used" in briefing


def test_national_situation_cards_explainable():
    national = esr.build_national_situation()
    assert national["cards"]
    for card in national["cards"]:
        assert card.get("explain")
        assert card.get("why_available") is True
        assert card.get("hash")


def test_alerts_have_severity_categories():
    alerts = esr.build_alerts()
    assert "categories" in alerts
    ids = {c["id"] for c in alerts["categories"]}
    assert {"critical", "attention", "info"} <= ids
    for item in alerts["items"]:
        assert item.get("why")
        assert item.get("hash")


def test_questions_predefined_conversational_ready():
    questions = esr.build_questions()
    assert questions["_meta"]["conversational_ready"] is True
    assert questions["_meta"]["mode"] == "predefined_v1"
    assert len(questions["questions"]) >= 4


def test_actions_zero_decorative():
    actions = esr.build_executive_actions()
    assert actions["_meta"]["zero_decorative"] is True
    mission = next(a for a in actions["actions"] if a["id"] == "prepare_mission")
    assert mission["available"] is False
    assert mission["hide_when_unavailable"] is True
    assert any(a["id"] == "present_dg" for a in actions["actions"])


def test_api_situation_room_endpoints():
    for path in (
        "/api/executive/situation-room/briefing",
        "/api/executive/situation-room/national",
        "/api/executive/situation-room/alerts",
        "/api/executive/situation-room/questions",
        "/api/executive/situation-room/actions",
        "/api/executive/situation-room/scenarios",
    ):
        res = CLIENT.get(path)
        assert res.status_code == 200, path

    full = CLIENT.get("/api/executive/situation-room")
    assert full.status_code == 200
    body = full.json()
    assert body["_meta"]["version"].startswith("esr-")
    assert "briefing" in body
    assert "presentation" in body
    assert len(body["presentation"]["steps"]) >= 5
