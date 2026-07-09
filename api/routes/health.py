"""Endpoints REST du référentiel Santé v1.0."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query

from api.config import DATA_MODE
from api.services import health_service

router = APIRouter()


def _ensure_db_mode() -> None:
    if DATA_MODE != "db":
        raise HTTPException(
            status_code=503,
            detail="Endpoint disponible uniquement en mode DB (DATA_MODE=db).",
        )


@router.get("/facilities", summary="Lister les structures sanitaires")
def list_facilities(
    facility_type_code: str | None = Query(None),
    province_name: str | None = Query(None),
    territory_name: str | None = Query(None),
    q: str | None = Query(None, description="Recherche textuelle"),
    skip: int = Query(0, ge=0),
    limit: int = Query(500, gt=0, le=5000),
) -> dict[str, Any]:
    _ensure_db_mode()
    if q:
        facilities = health_service.search_facilities(
            q=q,
            facility_type_code=facility_type_code,
            province_name=province_name,
            limit=limit,
        )
    else:
        facilities = health_service.list_facilities(
            facility_type_code=facility_type_code,
            province_name=province_name,
            territory_name=territory_name,
            skip=skip,
            limit=limit,
        )
    stats = health_service.get_statistics()
    return {
        "_meta": {
            "count": len(facilities),
            "data_available": stats.get("data_available", False),
        },
        "facilities": facilities,
        "statistics": stats,
    }


@router.get("/facilities/{facility_id}", summary="Détail d'une structure sanitaire")
def get_facility(facility_id: int) -> dict[str, Any]:
    _ensure_db_mode()
    facility = health_service.get_facility(facility_id)
    if not facility:
        raise HTTPException(status_code=404, detail="Structure sanitaire introuvable.")
    return facility


@router.get("/statistics", summary="Statistiques du référentiel santé")
def health_statistics(refresh: bool = Query(False)) -> dict[str, Any]:
    _ensure_db_mode()
    if refresh:
        return health_service.compute_statistics()
    return health_service.get_statistics()


@router.get("/nearest", summary="Structures sanitaires les plus proches")
def nearest_facility(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    facility_type_code: str | None = Query(None),
    radius_m: float = Query(50000, gt=0, le=200000),
    limit: int = Query(10, gt=0, le=100),
) -> dict[str, Any]:
    _ensure_db_mode()
    return health_service.nearest_facility(
        latitude=latitude,
        longitude=longitude,
        facility_type_code=facility_type_code,
        radius_m=radius_m,
        limit=limit,
    )


@router.get("/panel", summary="Synthèse Centre de Décision — Santé")
def health_panel() -> dict[str, Any]:
    _ensure_db_mode()
    return health_service.get_panel_payload()


@router.get("/layers/facilities", summary="Couche cartographique structures sanitaires")
def health_facilities_layer(limit: int = Query(5000, gt=0, le=50000)) -> dict[str, Any]:
    _ensure_db_mode()
    return health_service.facilities_geojson(limit=limit)
