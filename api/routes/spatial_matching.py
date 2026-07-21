"""API REST — National Spatial Matching Engine (NSME)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from api.config import DATA_MODE
from api.services import spatial_matching_service as nsme

router = APIRouter()


class RefreshPayload(BaseModel):
    program_code: str | None = None
    province: str | None = None
    territoire: str | None = None
    asset_id: int | None = None
    include_ccn: bool = True
    persist: bool = True
    limit_assets: int | None = Field(default=None, ge=1, le=5000)


def _filters(
    *,
    asset_type: str | None = None,
    program_code: str | None = None,
    province: str | None = None,
    territoire: str | None = None,
    relation_type: str | None = None,
    max_distance_km: float | None = None,
    priority_level: str | None = None,
    category: str | None = None,
    limit: int = 200,
    offset: int = 0,
) -> dict[str, Any]:
    return {
        "asset_type": asset_type,
        "program_code": program_code,
        "province": province,
        "territoire": territoire,
        "relation_type": relation_type,
        "max_distance_km": max_distance_km,
        "priority_level": priority_level,
        "category": category,
        "limit": limit,
        "offset": offset,
    }


@router.get("/statistics", summary="Statistiques nationales NSME")
def statistics() -> dict[str, Any]:
    return nsme.get_statistics()


@router.get("/rules", summary="Règles spatiales configurables")
def rules() -> dict[str, Any]:
    return nsme.get_rules()


@router.get("/quality", summary="Rapport qualité des correspondances")
def quality() -> dict[str, Any]:
    return nsme.quality_report()


@router.get("/demo-cases", summary="Cas de démonstration réels")
def demo_cases() -> dict[str, Any]:
    return nsme.demo_cases()


@router.get("/edvs", summary="Indicateurs EDVS NSME")
def edvs() -> dict[str, Any]:
    return nsme.edvs_charts()


@router.get("/map", summary="Couche cartographique Correspondance Actifs ↔ Besoins")
def map_layer(
    asset_id: str | None = Query(None),
    territoire: str | None = Query(None),
    limit: int = Query(500, gt=0, le=5000),
) -> dict[str, Any]:
    return nsme.map_payload(asset_id=asset_id, territoire=territoire, limit=limit)


@router.get("/assets/{asset_id}/needs", summary="Besoins liés à un actif")
def asset_needs(
    asset_id: str,
    asset_type: str | None = Query("fdsu_site"),
    program_code: str | None = None,
    province: str | None = None,
    territoire: str | None = None,
    relation_type: str | None = None,
    max_distance_km: float | None = Query(None, ge=0),
    priority_level: str | None = None,
    category: str | None = None,
    limit: int = Query(200, gt=0, le=2000),
    offset: int = Query(0, ge=0),
) -> dict[str, Any]:
    return nsme.get_asset_needs(
        asset_id,
        **_filters(
            asset_type=asset_type,
            program_code=program_code,
            province=province,
            territoire=territoire,
            relation_type=relation_type,
            max_distance_km=max_distance_km,
            priority_level=priority_level,
            category=category,
            limit=limit,
            offset=offset,
        ),
    )


@router.get("/needs/{need_id}/assets", summary="Actifs liés à un besoin")
def need_assets(
    need_id: str,
    asset_type: str | None = None,
    program_code: str | None = None,
    province: str | None = None,
    territoire: str | None = None,
    relation_type: str | None = None,
    priority_level: str | None = None,
    limit: int = Query(200, gt=0, le=2000),
    offset: int = Query(0, ge=0),
) -> dict[str, Any]:
    return nsme.get_need_assets(
        need_id,
        asset_type=asset_type,
        program_code=program_code,
        province=province,
        territoire=territoire,
        relation_type=relation_type,
        priority_level=priority_level,
        limit=limit,
        offset=offset,
    )


@router.get("/assets/{asset_id}/impact", summary="Impact populationnel d'un actif")
def asset_impact(
    asset_id: str,
    asset_type: str | None = Query("fdsu_site"),
    program_code: str | None = None,
    max_distance_km: float | None = Query(None, ge=0),
) -> dict[str, Any]:
    return nsme.get_asset_impact(
        asset_id,
        asset_type=asset_type,
        program_code=program_code,
        max_distance_km=max_distance_km,
    )


@router.get("/assets/{asset_id}/explain", summary="Explicabilité d'une correspondance")
def asset_explain(
    asset_id: str,
    need_id: str | None = Query(None),
    program_code: str | None = None,
) -> dict[str, Any]:
    return nsme.explain_match(asset_id=asset_id, need_id=need_id, program_code=program_code)


@router.get("/territories/{territory_id}/matches", summary="Correspondances d'un territoire")
def territory_matches(
    territory_id: str,
    limit: int = Query(500, gt=0, le=5000),
    offset: int = Query(0, ge=0),
) -> dict[str, Any]:
    return nsme.get_territory_matches(territory_id, limit=limit, offset=offset)


@router.post("/refresh", summary="Recalcul ciblé des correspondances")
def refresh(payload: RefreshPayload | None = None) -> dict[str, Any]:
    if DATA_MODE != "db":
        raise HTTPException(status_code=503, detail="Refresh NSME disponible en DATA_MODE=db.")
    body = payload or RefreshPayload()
    return nsme.refresh_matches(
        program_code=body.program_code,
        province=body.province,
        territoire=body.territoire,
        asset_id=body.asset_id,
        include_ccn=body.include_ccn,
        persist=body.persist,
        limit_assets=body.limit_assets,
    )
