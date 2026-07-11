"""API REST — Tableau de Synthèse Territoriale (TST)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query

from api.config import DATA_MODE
from api.services import territorial_summary_service

router = APIRouter()


def _ensure_db_mode() -> None:
    if DATA_MODE != "db":
        raise HTTPException(status_code=503, detail="TST disponible en mode DB (DATA_MODE=db).")


@router.get("/metrics", summary="Catalogue des métriques TST (sources réelles)")
def tst_metrics() -> dict[str, Any]:
    _ensure_db_mode()
    return territorial_summary_service.list_metrics()


@router.get("/layer", summary="Couche choroplèthe TST (properties sans géométrie)")
def tst_layer(
    level: str = Query("province", description="province | territoire"),
    metric: str = Query("priority"),
    parent_id: str | None = Query(None, description="Province parente pour niveau territoire"),
) -> dict[str, Any]:
    _ensure_db_mode()
    if level == "province":
        return territorial_summary_service.build_province_layer(metric)
    if level == "territoire":
        if not parent_id:
            raise HTTPException(status_code=400, detail="parent_id (province) requis pour les territoires.")
        return territorial_summary_service.build_territory_layer(parent_id, metric)
    raise HTTPException(status_code=400, detail="Niveau non supporté pour cette version (province|territoire).")


@router.get("/entity", summary="Panneau de synthèse d’une entité territoriale")
def tst_entity(
    level: str = Query(...),
    id: str = Query(..., alias="id"),
    name: str | None = Query(None),
) -> dict[str, Any]:
    _ensure_db_mode()
    return territorial_summary_service.build_entity_summary(level, id, name)
