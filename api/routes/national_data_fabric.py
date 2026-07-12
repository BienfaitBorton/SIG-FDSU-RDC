"""API REST — National Data Fabric (NDF)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from api.services import national_data_fabric_service as ndf

router = APIRouter()


class RegistryRegistration(BaseModel):
    id: str = Field(..., min_length=2, max_length=64)
    name: str
    category: str
    description: str
    owner: str
    official_source: str
    update_frequency: str
    version: str
    confidence_level: str
    geographic_coverage: str
    geometry_type: str
    crs: str = "EPSG:4326"
    status: str | None = "registered"
    quality_baseline: str | None = "not_measured"
    related_registry_ids: list[str] | None = None
    apis: list[str] | None = None
    metrics_exposed: list[str] | None = None
    aggregation_rules: str | None = None
    integration_module: str | None = None
    data_path: str | None = None
    update_history: list[dict[str, Any]] | None = None


@router.get("/manifest", summary="Manifeste National Data Fabric")
def manifest() -> dict[str, Any]:
    return ndf.fabric_manifest()


@router.get("/registries", summary="Inventaire des référentiels nationaux")
def list_registries(
    category: str | None = Query(None),
    status: str | None = Query(None, description="active | planned | registered"),
) -> dict[str, Any]:
    return ndf.list_registries(category=category, status=status)


@router.get("/registries/{registry_id}", summary="Métadonnées détaillées d'un référentiel")
def get_registry(registry_id: str) -> dict[str, Any]:
    result = ndf.get_registry(registry_id)
    if not result:
        raise HTTPException(status_code=404, detail="Référentiel introuvable dans le NDF.")
    return result


@router.post("/registries", summary="Enregistrer un nouveau référentiel (extension NDF)")
def register_registry(body: RegistryRegistration) -> dict[str, Any]:
    try:
        return ndf.register_registry(body.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/registries/{registry_id}/quality", summary="Indicateurs qualité d'un référentiel")
def registry_quality(registry_id: str) -> dict[str, Any]:
    if not ndf.get_registry(registry_id):
        raise HTTPException(status_code=404, detail="Référentiel introuvable dans le NDF.")
    return ndf.compute_quality(registry_id)


@router.get("/quality", summary="Vue qualité globale NDF")
def quality_overview() -> dict[str, Any]:
    return ndf.quality_overview()


@router.get("/statistics", summary="Statistiques globales du fabric")
def statistics() -> dict[str, Any]:
    return ndf.statistics()


@router.get("/search", summary="Recherche de référentiels")
def search(q: str = Query(..., min_length=1, description="Texte libre")) -> dict[str, Any]:
    return ndf.search_registries(q)


@router.get("/relations", summary="Relations documentées entre référentiels")
def relations(registry_id: str | None = Query(None)) -> dict[str, Any]:
    return ndf.list_relations(registry_id=registry_id)


@router.get("/consumers", summary="Compatibilité TST / Decision / Knowledge Hub / NSME")
def consumers() -> dict[str, Any]:
    return ndf.consumers_compatibility()
