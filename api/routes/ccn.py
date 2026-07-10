"""API Capability CCN — fondations + module opérationnel v1 (lecture)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from api.services import ccn_capability_service, ccn_operational_service

router = APIRouter()


class CcnCodePreparePayload(BaseModel):
    zone: str
    province_code: str | int
    territoire_code: str | int
    numero: str | int = Field(..., description="Numéro séquentiel CCN dans le territoire")


@router.get("", summary="Lister les CCN (démonstration)")
@router.get("/", summary="Lister les CCN (démonstration)", include_in_schema=False)
def list_ccn(
    province: str | None = Query(None),
    territoire: str | None = Query(None),
    zone: str | None = Query(None),
    program_code: str | None = Query(None),
    status: str | None = Query(None),
    ccn_type: str | None = Query(None),
    limit: int = Query(200, gt=0, le=1000),
) -> dict[str, Any]:
    return ccn_operational_service.list_ccn(
        province=province,
        territoire=territoire,
        zone=zone,
        program_code=program_code,
        status=status,
        ccn_type=ccn_type,
        limit=limit,
    )


@router.get("/statistics", summary="KPI / statistiques CCN")
def ccn_statistics() -> dict[str, Any]:
    return ccn_operational_service.statistics()


@router.get("/map", summary="GeoJSON CCN + Sites FDSU liés")
def ccn_map(
    province: str | None = Query(None),
    territoire: str | None = Query(None),
    zone: str | None = Query(None),
    program_code: str | None = Query(None),
    status: str | None = Query(None),
    ccn_type: str | None = Query(None),
) -> dict[str, Any]:
    return ccn_operational_service.map_payload(
        province=province,
        territoire=territoire,
        zone=zone,
        program_code=program_code,
        status=status,
        ccn_type=ccn_type,
    )


@router.get("/doctrine", summary="Doctrine métier CCN versionnée")
def ccn_doctrine() -> dict[str, Any]:
    return ccn_operational_service.doctrine_payload()


@router.get("/capability", summary="Manifeste capacité CCN")
def ccn_capability() -> dict[str, Any]:
    manifest = ccn_capability_service.capability_manifest()
    manifest["_meta"]["status"] = "operational_v1_demo"
    manifest["_meta"]["module"] = "dashboard/modules/ccn"
    return manifest


@router.get("/decision-extensions", summary="Points d'extension Centre de Décision CCN")
def ccn_decision_extensions() -> dict[str, Any]:
    doctrine = ccn_operational_service.load_doctrine()
    return {
        "_meta": {
            "title": "Extensions Centre de Décision — CCN",
            "ui_ready": True,
            "note": "Le moteur doit charger doctrine/critères/règles sans hardcode.",
            "doctrine_hooks": (doctrine.get("decision_engine_hooks") or []),
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


@router.get("/{ccn_id}", summary="Fiche CCN")
def get_ccn(ccn_id: str) -> dict[str, Any]:
    result = ccn_operational_service.get_ccn(ccn_id)
    if not result:
        raise HTTPException(status_code=404, detail="CCN introuvable.")
    return result
