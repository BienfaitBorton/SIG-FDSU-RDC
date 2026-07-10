"""API Executive Data Visualization System / Salle de Pilotage DG."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from api.services import executive_cockpit_service

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
        ],
        "modules_path": "dashboard/modules/shared/executive-dashboard/",
    }
