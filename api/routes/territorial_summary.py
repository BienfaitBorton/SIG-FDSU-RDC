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


@router.get("/layer", summary="Couche choroplèthe TST (parent + enfants + statut géométrique)")
def tst_layer(
    level: str = Query(
        "province",
        description="province | territoire | collectivite | groupement | localite",
    ),
    metric: str = Query("priority"),
    parent_id: str | None = Query(None, description="Entité parente (province, territoire, …)"),
    province: str | None = Query(None, description="Province contextuelle (niveaux inférieurs)"),
    territory: str | None = Query(None, description="Territoire contextuel (groupement/localité)"),
) -> dict[str, Any]:
    _ensure_db_mode()
    level_norm = (level or "province").strip().lower()
    if level_norm in {"province", "provinces"}:
        return territorial_summary_service.build_province_layer(metric)
    if level_norm in {"territoire", "territory", "territoires"}:
        if not parent_id:
            raise HTTPException(status_code=400, detail="parent_id (province) requis pour les territoires.")
        return territorial_summary_service.build_territory_layer(parent_id, metric)
    if level_norm in {"collectivite", "collectivites", "subdivision", "secteur", "chefferie"}:
        if not parent_id:
            raise HTTPException(status_code=400, detail="parent_id (territoire) requis pour les collectivités.")
        return territorial_summary_service.build_subdivision_layer(parent_id, metric, province_name=province)
    if level_norm in {"groupement", "groupements"}:
        if not parent_id:
            raise HTTPException(status_code=400, detail="parent_id (collectivité) requis pour les groupements.")
        return territorial_summary_service.build_points_layer(
            "groupement",
            parent_id,
            metric,
            province_name=province,
            territory_name=territory,
        )
    if level_norm in {"localite", "localites", "localité"}:
        if not parent_id:
            raise HTTPException(status_code=400, detail="parent_id (groupement) requis pour les localités.")
        return territorial_summary_service.build_points_layer(
            "localite",
            parent_id,
            metric,
            province_name=province,
            territory_name=territory,
        )
    raise HTTPException(
        status_code=400,
        detail="Niveau non supporté (province|territoire|collectivite|groupement|localite).",
    )


@router.get("/entity", summary="Panneau de synthèse d’une entité territoriale")
def tst_entity(
    level: str = Query(...),
    id: str = Query(..., alias="id"),
    name: str | None = Query(None),
) -> dict[str, Any]:
    _ensure_db_mode()
    return territorial_summary_service.build_entity_summary(level, id, name)
