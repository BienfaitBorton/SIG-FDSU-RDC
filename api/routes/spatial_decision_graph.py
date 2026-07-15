"""API REST — Spatial Decision Graph / Analyse d’Impact Territorial."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query

from api.services import spatial_decision_graph_service as sdg

router = APIRouter()


@router.get("/meta/categories", summary="Catégories et styles du graphe")
def get_categories() -> dict[str, Any]:
    return {
        "categories": list(sdg.CATEGORIES.values()),
        "relation_styles": sdg.RELATION_STYLES,
        "presentation_steps": sdg.PRESENTATION_STEPS,
        "ui_title": "Analyse d’Impact Territorial",
        "technical_name": "Spatial Decision Graph",
    }


@router.get("/{asset_type}/{asset_id}/presentation", summary="Scénario de présentation DG")
def get_presentation(
    asset_type: str,
    asset_id: str,
    program_code: str | None = Query(default=None),
) -> dict[str, Any]:
    payload = sdg.build_presentation(asset_type, asset_id, program_code=program_code)
    if not payload:
        raise HTTPException(status_code=404, detail="Présentation indisponible pour cet actif.")
    return payload


@router.get("/{asset_type}/{asset_id}", summary="Graphe décisionnel territorial")
def get_graph(
    asset_type: str,
    asset_id: str,
    program_code: str | None = Query(default=None),
) -> dict[str, Any]:
    graph = sdg.build_graph(asset_type, asset_id, program_code=program_code)
    if not graph:
        raise HTTPException(status_code=404, detail="Graphe d’impact territorial introuvable pour cet actif.")
    # Les graphes « impossible » (classification C) restent 200 avec fiche explicative — Data First.
    return graph
