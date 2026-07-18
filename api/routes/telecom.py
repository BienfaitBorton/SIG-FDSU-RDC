"""Endpoints REST du référentiel télécom national."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query

from api.config import DATA_MODE
from api.services import telecom_service
from api.services.telecom_layer_catalog import catalog_payload, known_layer_keys

router = APIRouter()


def _ensure_db_mode() -> None:
    if DATA_MODE != "db":
        raise HTTPException(
            status_code=503,
            detail="Endpoint disponible uniquement en mode DB (DATA_MODE=db).",
        )


@router.get("/operators", summary="Lister les opérateurs télécom")
def list_operators() -> list[dict[str, Any]]:
    _ensure_db_mode()
    return telecom_service.list_operators()


@router.get("/statistics", summary="Statistiques du référentiel télécom")
def telecom_statistics() -> dict[str, Any]:
    _ensure_db_mode()
    return telecom_service.get_statistics()


@router.get("/panel", summary="Synthèse Centre de Décision")
def telecom_panel() -> dict[str, Any]:
    _ensure_db_mode()
    return telecom_service.get_panel_payload()


@router.get("/infrastructure", summary="Infrastructures ponctuelles")
def list_infrastructure(
    operator_code: str | None = Query(None),
    format: str = Query("json", pattern="^(json|geojson)$"),
    skip: int = Query(0, ge=0),
    limit: int = Query(10000, gt=0, le=100000),
) -> Any:
    _ensure_db_mode()
    rows = telecom_service.list_infrastructure(operator_code=operator_code, skip=skip, limit=limit)
    if format == "geojson":
        features = []
        for index, row in enumerate(rows, start=1):
            features.append(
                {
                    "type": "Feature",
                    "id": index,
                    "geometry": row.get("geometry"),
                    "properties": {
                        key: value
                        for key, value in row.items()
                        if key not in {"geometry"} and value not in (None, "")
                    },
                }
            )
        return {"type": "FeatureCollection", "features": features}
    return rows


@router.get("/network-lines", summary="Lignes réseau")
def list_network_lines(
    operator_code: str | None = Query(None),
    format: str = Query("json", pattern="^(json|geojson)$"),
    skip: int = Query(0, ge=0),
    limit: int = Query(10000, gt=0, le=100000),
) -> Any:
    _ensure_db_mode()
    rows = telecom_service.list_network_lines(operator_code=operator_code, skip=skip, limit=limit)
    if format == "geojson":
        features = []
        for index, row in enumerate(rows, start=1):
            features.append(
                {
                    "type": "Feature",
                    "id": index,
                    "geometry": row.get("geometry"),
                    "properties": {
                        key: value
                        for key, value in row.items()
                        if key not in {"geometry"} and value not in (None, "")
                    },
                }
            )
        return {"type": "FeatureCollection", "features": features}
    return rows


@router.get("/coverage-polygons", summary="Polygones de couverture")
def list_coverage_polygons(
    operator_code: str | None = Query(None),
    format: str = Query("json", pattern="^(json|geojson)$"),
    skip: int = Query(0, ge=0),
    limit: int = Query(10000, gt=0, le=100000),
) -> Any:
    _ensure_db_mode()
    rows = telecom_service.list_coverage_polygons(operator_code=operator_code, skip=skip, limit=limit)
    if format == "geojson":
        features = []
        for index, row in enumerate(rows, start=1):
            features.append(
                {
                    "type": "Feature",
                    "id": index,
                    "geometry": row.get("geometry"),
                    "properties": {
                        key: value
                        for key, value in row.items()
                        if key not in {"geometry"} and value not in (None, "")
                    },
                }
            )
        return {"type": "FeatureCollection", "features": features}
    return rows


@router.get("/layer-catalog", summary="Catalogue extensible des couches télécom")
def telecom_layer_catalog() -> dict[str, Any]:
    """Catalogue déclaratif — Smart Map et futurs opérateurs."""
    _ensure_db_mode()
    try:
        telecom_service.ensure_fdsu_mobile_operators()
    except Exception:
        pass
    return catalog_payload()


@router.get("/layers/{layer_key}", summary="Couche cartographique télécom")
def telecom_layer(
    layer_key: str,
    limit: int = Query(5000, gt=0, le=100000),
) -> dict[str, Any]:
    _ensure_db_mode()
    if layer_key not in known_layer_keys() and layer_key not in telecom_service.LAYER_OPERATOR_MAP:
        raise HTTPException(status_code=404, detail="Couche telecom introuvable.")
    try:
        telecom_service.ensure_fdsu_mobile_operators()
    except Exception:
        pass
    return telecom_service.resolve_layer_geojson(layer_key, limit=limit)


@router.get("/spatial-context", summary="Relations spatiales télécom autour d'un point")
def telecom_spatial_context(
    latitude: float = Query(...),
    longitude: float = Query(...),
    radius_m: float = Query(25000, gt=0, le=100000),
) -> dict[str, Any]:
    """Nearest MNO / fibre / MW / multi-opérateur — PostGIS + staging FDSU."""
    _ensure_db_mode()
    return telecom_service.spatial_context_around(latitude, longitude, radius_m=radius_m)


@router.post("/fdsu-mno-staging/sync", summary="Synchroniser staging FDSU MNO (hors KPI)")
def sync_fdsu_mno_staging(max_rows: int = Query(20000, gt=0, le=50000)) -> dict[str, Any]:
    """Copie dérivée contrôlée vers telecom.fdsu_mno_sites — n'écrit pas dans infrastructure."""
    _ensure_db_mode()
    return telecom_service.sync_fdsu_mno_staging_from_audit(max_rows=max_rows)


@router.get(
    "/operator-sites-consolidation",
    summary="Référentiel consolidé sites opérateurs FDSU (lecture seule)",
)
def operator_sites_consolidation_report() -> dict[str, Any]:
    """Consolidation opérateur-par-opérateur — hors Fibre/MW ; n'écrit pas les sources."""
    _ensure_db_mode()
    from api.services.telecom_operator_sites_consolidation import (
        consolidate_mobile_operator_sites,
        result_as_dict,
    )

    return result_as_dict(consolidate_mobile_operator_sites())


@router.get("/nearby-sites", summary="Sites FDSU proches d'une infrastructure")
def nearby_sites(
    latitude: float | None = Query(None),
    longitude: float | None = Query(None),
    radius_meters: float | None = Query(None, gt=0),
    limit: int = Query(100, gt=0, le=1000),
) -> dict[str, Any]:
    _ensure_db_mode()
    return telecom_service.get_nearby_sites(
        latitude=latitude,
        longitude=longitude,
        radius_meters=radius_meters,
        limit=limit,
    )
