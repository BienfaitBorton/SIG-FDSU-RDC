"""Endpoints REST du Spatial Intelligence Engine."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query

from pydantic import BaseModel

from api.config import DATA_MODE
from api.services import spatial_analysis_service

router = APIRouter()

DEFAULT_PROGRAMS = ("PROG_SITES_40", "PROG_SITES_300")


class RunProgramsPayload(BaseModel):
    program_codes: list[str] | None = None


def _ensure_db_mode() -> None:
    if DATA_MODE != "db":
        raise HTTPException(
            status_code=503,
            detail="Endpoint disponible uniquement en mode DB (DATA_MODE=db).",
        )


@router.get("/statistics", summary="Statistiques du moteur d'analyse spatiale")
def analysis_statistics() -> dict[str, Any]:
    _ensure_db_mode()
    return spatial_analysis_service.get_statistics()


@router.get("/panel", summary="Synthèse Centre de Décision")
def analysis_panel() -> dict[str, Any]:
    _ensure_db_mode()
    return spatial_analysis_service.get_panel_payload()


@router.get("/layers/spatial-relations", summary="Couche cartographique relations spatiales")
def spatial_relations_layer(limit: int = Query(5000, gt=0, le=50000)) -> dict[str, Any]:
    _ensure_db_mode()
    return spatial_analysis_service.spatial_relations_geojson(limit=limit)


@router.post("/run/programs", summary="Analyser les programmes FDSU")
def run_programs_analysis(payload: RunProgramsPayload | None = None) -> dict[str, Any]:
    _ensure_db_mode()
    codes = (payload.program_codes if payload else None) or list(DEFAULT_PROGRAMS)
    return spatial_analysis_service.analyze_programs(codes, persist=True)


@router.get("/site/{site_id}", summary="Analyse spatiale d'un site FDSU")
def analyze_site(site_id: int, refresh: bool = Query(False)) -> dict[str, Any]:
    _ensure_db_mode()
    if refresh:
        return spatial_analysis_service.analyze_site(site_id, persist=True)
    stats = spatial_analysis_service.get_statistics()
    if stats.get("sites_analyzed", 0) == 0:
        return spatial_analysis_service.analyze_site(site_id, persist=True)
    result = spatial_analysis_service.analyze_site(site_id, persist=False)
    if result.get("analysis_status") == "not_found":
        raise HTTPException(status_code=404, detail="Site introuvable.")
    return result


@router.get("/program/{program_code}", summary="Analyse spatiale d'un programme FDSU")
def analyze_program(
    program_code: str,
    refresh: bool = Query(True, description="Recalculer les analyses"),
) -> dict[str, Any]:
    _ensure_db_mode()
    return spatial_analysis_service.analyze_program(program_code, persist=refresh)


@router.get("/nearby", summary="Proximité depuis un point")
def nearby_analysis(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    radius_m: float = Query(10000, gt=0, le=100000),
    limit: int = Query(100, gt=0, le=1000),
) -> dict[str, Any]:
    _ensure_db_mode()
    return spatial_analysis_service.get_nearby_analysis(
        latitude=latitude,
        longitude=longitude,
        radius_m=radius_m,
        limit=limit,
    )


@router.get("/health/site/{site_id}", summary="Proximité santé d'un site FDSU (extension)")
def site_health_proximity(site_id: int) -> dict[str, Any]:
    _ensure_db_mode()
    return spatial_analysis_service.get_site_health_proximity(site_id)
