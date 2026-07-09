"""Endpoints REST du Moteur de Décision FDSU v1.0."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from api.config import DATA_MODE
from api.services import decision_engine_service

router = APIRouter()


class RecomputePayload(BaseModel):
    program_codes: list[str] | None = None


def _ensure_db_mode() -> None:
    if DATA_MODE != "db":
        raise HTTPException(
            status_code=503,
            detail="Endpoint disponible uniquement en mode DB (DATA_MODE=db).",
        )


@router.get("/site-scores", summary="Liste des scores de priorité FDSU")
def list_site_scores(
    priority_level: str | None = Query(None, description="Filtrer par niveau: critical, high, medium, low"),
    program_code: str | None = Query(None, description="Filtrer par code programme"),
    limit: int = Query(500, gt=0, le=2000),
    offset: int = Query(0, ge=0),
) -> dict[str, Any]:
    _ensure_db_mode()
    return decision_engine_service.list_site_scores(
        priority_level=priority_level,
        program_code=program_code,
        limit=limit,
        offset=offset,
    )


@router.get("/site-scores/{site_id}", summary="Score de priorité d'un site FDSU")
def get_site_score(site_id: int) -> dict[str, Any]:
    _ensure_db_mode()
    result = decision_engine_service.get_site_score(site_id)
    if not result:
        raise HTTPException(status_code=404, detail="Score introuvable pour ce site.")
    return result


@router.post("/recompute-site-scores", summary="Recalculer tous les scores de priorité")
def recompute_site_scores(_payload: RecomputePayload | None = None) -> dict[str, Any]:
    _ensure_db_mode()
    return decision_engine_service.recompute_all_site_scores()


@router.get("/panel", summary="Synthèse Centre de Décision — moteur de décision")
def decision_panel() -> dict[str, Any]:
    _ensure_db_mode()
    return decision_engine_service.get_panel_payload()


@router.get("/national-panel", summary="Panneau national du Centre de Décision — KPI réels")
def national_panel() -> dict[str, Any]:
    _ensure_db_mode()
    return decision_engine_service.get_national_panel_payload()
