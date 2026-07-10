"""API Référentiel National des Actifs FDSU (Master Data Registry)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from api.services import fdsu_code_service, master_registry_service

router = APIRouter()


class EntityCreatePayload(BaseModel):
    entity_type: str
    business_id: str | None = None
    name: str | None = None
    status: str | None = "draft"
    validation_status: str | None = "pending"
    confidence_level: str | None = "unknown"
    source: str | None = "api"
    attributes: dict[str, Any] | None = None
    geometry: dict[str, Any] | None = None


class EntityUpdatePayload(BaseModel):
    business_id: str | None = None
    name: str | None = None
    status: str | None = None
    validation_status: str | None = None
    confidence_level: str | None = None
    source: str | None = None
    attributes: dict[str, Any] | None = None
    geometry: dict[str, Any] | None = None
    change_note: str | None = None


class FdsuValidatePayload(BaseModel):
    business_id: str
    expected_zone: str | None = None
    expected_province_code: str | None = None
    expected_territoire_code: str | None = None


class FdsuGeneratePayload(BaseModel):
    zone: str
    province_code: str | int
    territoire_code: str | int
    site_number: str | int
    collectivite_code: str | int | None = None
    site_width: int = Field(default=5, ge=3, le=5)


class MergePayload(BaseModel):
    source_id: str
    target_id: str
    note: str | None = None


@router.get("/entities", summary="Lister les entités du référentiel national")
def list_entities(
    entity_type: str | None = Query(None),
    status: str | None = Query(None),
    validation_status: str | None = Query(None),
    q: str | None = Query(None),
    limit: int = Query(100, gt=0, le=2000),
    offset: int = Query(0, ge=0),
) -> dict[str, Any]:
    return master_registry_service.list_entities(
        entity_type=entity_type,
        status=status,
        validation_status=validation_status,
        q=q,
        limit=limit,
        offset=offset,
    )


@router.get("/entities/{entity_id}", summary="Détail d'une entité master")
def get_entity(entity_id: str) -> dict[str, Any]:
    entity = master_registry_service.get_entity(entity_id)
    if not entity:
        raise HTTPException(status_code=404, detail="Entité introuvable.")
    return {"entity": entity}


@router.post("/entities", summary="Créer une entité master")
def create_entity(payload: EntityCreatePayload) -> dict[str, Any]:
    try:
        entity = master_registry_service.create_entity(payload.model_dump(exclude_none=True))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"entity": entity}


@router.put("/entities/{entity_id}", summary="Mettre à jour une entité master")
def update_entity(entity_id: str, payload: EntityUpdatePayload) -> dict[str, Any]:
    try:
        entity = master_registry_service.update_entity(
            entity_id,
            payload.model_dump(exclude_none=True),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not entity:
        raise HTTPException(status_code=404, detail="Entité introuvable.")
    return {"entity": entity}


@router.get("/search", summary="Recherche dans le référentiel national")
def search_entities(
    q: str = Query(..., min_length=1),
    limit: int = Query(50, gt=0, le=500),
) -> dict[str, Any]:
    return master_registry_service.search_entities(q, limit=limit)


@router.get("/statistics", summary="Statistiques et qualité du référentiel")
def statistics() -> dict[str, Any]:
    return master_registry_service.statistics()


@router.get("/panel", summary="Synthèse Centre de Décision — Référentiel National")
def panel() -> dict[str, Any]:
    return master_registry_service.panel_payload()


@router.get("/entities/{entity_id}/history", summary="Historique d'une entité")
def entity_history(entity_id: str) -> dict[str, Any]:
    history = master_registry_service.get_history(entity_id)
    if not history:
        raise HTTPException(status_code=404, detail="Entité introuvable.")
    return history


@router.post("/entities/merge", summary="Fusionner deux entités")
def merge_entities(payload: MergePayload) -> dict[str, Any]:
    try:
        return master_registry_service.merge_entities(
            payload.source_id,
            payload.target_id,
            note=payload.note,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/entities/{entity_id}/validate", summary="Valider une entité")
def validate_entity(entity_id: str) -> dict[str, Any]:
    try:
        return master_registry_service.validate_entity(entity_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/fdsu-code/{business_id}", summary="Analyser un code FDSU officiel")
def get_fdsu_code(business_id: str) -> dict[str, Any]:
    return master_registry_service.get_fdsu_code_details(business_id)


@router.post("/fdsu-code/validate", summary="Valider un code FDSU")
def validate_fdsu_code(payload: FdsuValidatePayload) -> dict[str, Any]:
    result = fdsu_code_service.validate_fdsu_code(
        payload.business_id,
        expected_zone=payload.expected_zone,
        expected_province_code=payload.expected_province_code,
        expected_territoire_code=payload.expected_territoire_code,
    )
    return result.as_dict()


@router.post("/fdsu-code/generate", summary="Générer un code FDSU officiel")
def generate_fdsu_code(payload: FdsuGeneratePayload) -> dict[str, Any]:
    return fdsu_code_service.generate_fdsu_code(
        zone=payload.zone,
        province_code=payload.province_code,
        territoire_code=payload.territoire_code,
        site_number=payload.site_number,
        collectivite_code=payload.collectivite_code,
        site_width=payload.site_width,
        validate=True,
    )


@router.post("/schema/ensure", summary="Appliquer le schéma PostGIS master.*")
def ensure_schema() -> dict[str, Any]:
    return master_registry_service.ensure_postgis_schema()
