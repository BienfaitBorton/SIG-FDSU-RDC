"""API FDSU Knowledge Hub — domaines de connaissance & National Indicators Framework."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query

from api.services import knowledge_hub_service

router = APIRouter()


@router.get("/domains", summary="Lister les domaines de connaissance FDSU")
def list_domains() -> dict[str, Any]:
    return knowledge_hub_service.list_domains()


@router.get("/domain/{domain_id}", summary="Détail d'un domaine de connaissance")
def get_domain(domain_id: str) -> dict[str, Any]:
    result = knowledge_hub_service.get_domain(domain_id)
    if not result:
        raise HTTPException(status_code=404, detail="Domaine de connaissance introuvable.")
    return result


@router.get("/indicators", summary="Catalogue National Indicators Framework")
def list_indicators(
    family: str | None = Query(None, description="Filtrer par famille d'indicateur"),
    domain_id: str | None = Query(None, description="Filtrer par domaine"),
) -> dict[str, Any]:
    return knowledge_hub_service.list_indicators(family=family, domain_id=domain_id)


@router.get("/indicator/{indicator_id}", summary="Détail d'un indicateur national")
def get_indicator(indicator_id: str) -> dict[str, Any]:
    result = knowledge_hub_service.get_indicator(indicator_id)
    if not result:
        raise HTTPException(status_code=404, detail="Indicateur introuvable.")
    return result


@router.get("/manifest", summary="Manifeste Knowledge Hub")
def hub_manifest() -> dict[str, Any]:
    return knowledge_hub_service.hub_manifest()


@router.get("/integrations", summary="Points de connexion avec les modules existants")
def integrations() -> dict[str, Any]:
    return knowledge_hub_service.integration_points()
