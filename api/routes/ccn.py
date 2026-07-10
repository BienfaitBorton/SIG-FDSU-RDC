"""API fondations Capability CCN — lecture seule, pas de CRUD."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from api.services import ccn_capability_service

router = APIRouter()


class CcnCodePreparePayload(BaseModel):
    zone: str
    province_code: str | int
    territoire_code: str | int
    numero: str | int = Field(..., description="Numéro séquentiel CCN dans le territoire")


@router.get("/capability", summary="Manifeste capacité CCN (fondations Phase 2)")
def ccn_capability() -> dict[str, Any]:
    return ccn_capability_service.capability_manifest()


@router.get("/decision-extensions", summary="Points d'extension Centre de Décision CCN")
def ccn_decision_extensions() -> dict[str, Any]:
    return {
        "_meta": {
            "title": "Extensions Centre de Décision — CCN",
            "ui_ready": False,
            "note": "Points préparés ; écrans complets non branchés.",
        },
        "extensions": ccn_capability_service.decision_extension_points(),
    }


@router.get("/relationships", summary="Catalogue des relations métier CCN")
def ccn_relationships() -> dict[str, Any]:
    return {
        "relationships": ccn_capability_service.relationship_catalog(),
        "required_connectivity_link": ccn_capability_service.required_connectivity_link(),
    }


@router.get("/nomenclature/inspect", summary="Inspecter un code CCN préparatoire")
def inspect_ccn_code(business_id: str = Query(..., min_length=3)) -> dict[str, Any]:
    return ccn_capability_service.inspect_ccn_code(business_id)


@router.post("/nomenclature/prepare", summary="Préparer un code CCN (non officiel)")
def prepare_ccn_code(payload: CcnCodePreparePayload) -> dict[str, Any]:
    return ccn_capability_service.prepare_ccn_code(
        zone=payload.zone,
        province_code=payload.province_code,
        territoire_code=payload.territoire_code,
        numero=payload.numero,
    )
