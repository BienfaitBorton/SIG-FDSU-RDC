"""API REST — Transport & Accessibility Intelligence."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query

from api.config import DATA_MODE
from api.services import transport_service

router = APIRouter()


def _ensure_db_mode() -> None:
    if DATA_MODE != "db":
        raise HTTPException(status_code=503, detail="Transport disponible en mode DB (DATA_MODE=db).")


@router.get("/manifest", summary="Manifeste référentiel Transport")
def manifest() -> dict[str, Any]:
    return transport_service.get_manifest()


@router.get("/statistics", summary="Statistiques routes principales")
def statistics() -> dict[str, Any]:
    _ensure_db_mode()
    return transport_service.get_statistics()


@router.get("/quality", summary="Rapport qualité transport")
def quality() -> dict[str, Any]:
    return transport_service.get_quality_report()


@router.get("/formula", summary="Formule documentée du score d'accessibilité")
def formula() -> dict[str, Any]:
    return {
        "_meta": {"version": transport_service.ENGINE_VERSION},
        "formula": transport_service.ACCESSIBILITY_FORMULA,
    }


@router.get("/routes", summary="Liste des routes (JSON ou GeoJSON)")
def list_routes(
    format: str = Query("json", pattern="^(json|geojson)$"),
    skip: int = Query(0, ge=0),
    limit: int = Query(5000, gt=0, le=20000),
    type_route: str | None = Query(None),
) -> Any:
    _ensure_db_mode()
    rows = transport_service.list_routes(skip=skip, limit=limit, type_route=type_route)
    if format == "geojson":
        return {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "id": row.get("id"),
                    "geometry": row.get("geometry"),
                    "properties": {k: v for k, v in row.items() if k != "geometry"},
                }
                for row in rows
                if row.get("geometry")
            ],
        }
    return rows


@router.get("/layers/routes_principales", summary="Couche cartographique Routes principales")
def layer_routes(limit: int = Query(8000, gt=0, le=20000)) -> dict[str, Any]:
    _ensure_db_mode()
    return transport_service.routes_layer(limit=limit)


@router.get("/nearest-road", summary="Route principale la plus proche d'un point")
def nearest_road(
    lon: float = Query(...),
    lat: float = Query(...),
    max_distance_m: float = Query(50000, gt=0),
) -> dict[str, Any]:
    _ensure_db_mode()
    road = transport_service.nearest_road(lon, lat, max_distance_m=max_distance_m)
    if not road:
        return {
            "status": "insufficient",
            "display": "Données insuffisantes",
            "nearest_road": None,
            "message": "Aucune route dans le rayon demandé.",
        }
    return {"status": "ok", "nearest_road": road}


@router.get("/accessibility", summary="Score d'accessibilité d'un site ou d'un point")
def accessibility(
    site_id: int | None = Query(None),
    lon: float | None = Query(None),
    lat: float | None = Query(None),
) -> dict[str, Any]:
    _ensure_db_mode()
    if site_id is None and (lon is None or lat is None):
        raise HTTPException(status_code=400, detail="Fournir site_id ou lon+lat.")
    return transport_service.site_accessibility(site_id=site_id, lon=lon, lat=lat)


@router.get("/panel", summary="Panneau Decision Workspace / Centre de Décision")
def panel(site_id: int | None = Query(None)) -> dict[str, Any]:
    _ensure_db_mode()
    return transport_service.get_panel_payload(site_id=site_id)
