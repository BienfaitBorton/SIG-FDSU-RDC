"""Endpoints REST du National Reference Framework."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query

from api.config import DATA_MODE
from api.services import reference_service

router = APIRouter()


def _ensure_db_mode() -> None:
    if DATA_MODE != "db":
        raise HTTPException(
            status_code=503,
            detail="Endpoint disponible uniquement en mode DB (DATA_MODE=db).",
        )


@router.get("/catalog", summary="Catalogue des référentiels FDSU")
def list_catalog(
    category: str | None = Query(None),
    status: str | None = Query(None),
) -> dict[str, Any]:
    _ensure_db_mode()
    catalog = reference_service.list_catalog(category=category, status=status)
    return {
        "_meta": {"framework": "National Reference Framework", "count": len(catalog)},
        "catalog": catalog,
    }


@router.get("/catalog/{code}", summary="Détail d'un référentiel")
def get_catalog_entry(code: str) -> dict[str, Any]:
    _ensure_db_mode()
    entry = reference_service.get_catalog_entry(code)
    if not entry:
        raise HTTPException(status_code=404, detail="Référentiel introuvable.")
    quality = reference_service.get_quality_indicators(reference_code=code)
    object_types = reference_service.list_object_types(code)
    return {
        "entry": entry,
        "quality": quality[0] if quality else None,
        "object_types": object_types,
    }


@router.get("/quality", summary="Indicateurs de qualité des référentiels")
def reference_quality(
    reference_code: str | None = Query(None),
) -> dict[str, Any]:
    _ensure_db_mode()
    indicators = reference_service.get_quality_indicators(reference_code=reference_code)
    return {
        "_meta": {"framework": "National Reference Framework"},
        "indicators": indicators,
    }


@router.get("/types/{reference_code}", summary="Types d'objets d'un référentiel")
def list_object_types(reference_code: str) -> dict[str, Any]:
    _ensure_db_mode()
    entry = reference_service.get_catalog_entry(reference_code)
    if not entry:
        raise HTTPException(status_code=404, detail="Référentiel introuvable.")
    types = reference_service.list_object_types(reference_code)
    return {
        "reference_code": reference_code.upper(),
        "object_types": types,
    }


@router.get("/panel", summary="Synthèse référentiels sectoriels")
def reference_panel() -> dict[str, Any]:
    _ensure_db_mode()
    return reference_service.get_panel_payload()
