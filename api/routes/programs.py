"""Endpoints REST des programmes FDSU (source PostgreSQL/PostGIS)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query

from api.config import DATA_MODE
from api.services import program_service

router = APIRouter()


def _ensure_db_mode() -> None:
    if DATA_MODE != "db":
        raise HTTPException(
            status_code=503,
            detail="Endpoint disponible uniquement en mode DB (DATA_MODE=db).",
        )


@router.get("", summary="Lister les programmes FDSU")
def list_programs() -> list[dict[str, Any]]:
    _ensure_db_mode()
    return program_service.list_programs()


@router.get("/statistics", summary="Statistiques agrégées des programmes FDSU")
def program_statistics() -> dict[str, Any]:
    _ensure_db_mode()
    return program_service.get_program_statistics()


@router.get("/status-summary", summary="Synthèse des statuts programmes FDSU")
def program_status_summary() -> dict[str, Any]:
    _ensure_db_mode()
    return program_service.get_status_summary()


@router.get("/sites-followup", summary="Suivi opérationnel Sites 40 / Sites 300 / CCN")
def program_sites_followup() -> dict[str, Any]:
    _ensure_db_mode()
    return program_service.get_sites_followup()


@router.get("/sites", summary="Lister les sites FDSU")
def list_sites(
    program_code: str | None = Query(None, description="Filtrer par code programme (ex. PROG_SITES_40)"),
    skip: int = Query(0, ge=0),
    limit: int = Query(5000, gt=0, le=10000),
) -> list[dict[str, Any]]:
    _ensure_db_mode()
    return program_service.list_sites(program_code=program_code, skip=skip, limit=limit)


@router.get("/sites40", summary="Sites du programme Sites 40")
def sites40(
    format: str = Query("geojson", pattern="^(geojson|panel|json)$"),
) -> dict[str, Any]:
    _ensure_db_mode()
    if format in {"panel", "json"}:
        return program_service.get_program_sites_panel("PROG_SITES_40")
    return program_service.get_program_sites_geojson("PROG_SITES_40")


@router.get("/sites300", summary="Sites du programme Sites 300")
def sites300(
    format: str = Query("geojson", pattern="^(geojson|panel|json)$"),
) -> dict[str, Any]:
    _ensure_db_mode()
    if format in {"panel", "json"}:
        return program_service.get_program_sites_panel("PROG_SITES_300")
    return program_service.get_program_sites_geojson("PROG_SITES_300")


@router.get("/{program_ref}", summary="Détail d'un programme FDSU")
def get_program(program_ref: str) -> dict[str, Any]:
    _ensure_db_mode()
    program = program_service.get_program(program_ref)
    if not program:
        raise HTTPException(status_code=404, detail="Programme introuvable.")
    return program
