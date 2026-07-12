"""API Executive Situation Room / Salle de Pilotage DG."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from api.services import executive_cockpit_service, executive_situation_room_service as esr

router = APIRouter()


@router.get("/cockpit", summary="Salle de Pilotage DG — payload EDVS")
def executive_cockpit() -> dict[str, Any]:
    return executive_cockpit_service.build_cockpit_payload()


@router.get("/chart-catalog", summary="Catalogue des visualisations EDVS")
def chart_catalog() -> dict[str, Any]:
    return {
        "_meta": {
            "title": "Catalogue EDVS",
            "framework": "EDVS v1",
            "colors_policy": "Charte officielle uniquement (vert/orange/rouge/bleu/gris/jaune)",
        },
        "components": [
            "Executive KPI Card",
            "Horizontal Ranking",
            "Stacked Bar",
            "Radar",
            "Gauge",
            "Waterfall",
            "Treemap",
            "Timeline",
            "Heatmap",
            "Mini Sparkline",
            "Executive Briefing",
            "National Situation",
            "National Alerts",
            "Smart Questions",
            "Strategic Scenarios",
            "ESR Presentation Mode",
        ],
        "modules_path": "dashboard/modules/shared/executive-dashboard/",
        "esr_path": "dashboard/modules/shared/executive-situation-room/",
    }


@router.get("/situation-room", summary="Executive Situation Room — payload agrégé")
def situation_room() -> dict[str, Any]:
    return esr.build_situation_room()


@router.get("/situation-room/briefing", summary="Executive Briefing dynamique")
def situation_briefing() -> dict[str, Any]:
    return esr.build_briefing()


@router.get("/situation-room/national", summary="Situation nationale KPI")
def situation_national() -> dict[str, Any]:
    return esr.build_national_situation()


@router.get("/situation-room/alerts", summary="Alertes nationales")
def situation_alerts() -> dict[str, Any]:
    return esr.build_alerts()


@router.get("/situation-room/questions", summary="Questions intelligentes prédéfinies")
def situation_questions() -> dict[str, Any]:
    return esr.build_questions()


@router.get("/situation-room/scenarios", summary="Simulations stratégiques")
def situation_scenarios() -> dict[str, Any]:
    return esr.build_scenarios_panel()


@router.get("/situation-room/actions", summary="Actions exécutives réelles")
def situation_actions() -> dict[str, Any]:
    return esr.build_executive_actions()
