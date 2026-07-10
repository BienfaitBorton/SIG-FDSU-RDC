"""API Territorial Intelligence Explorer v1."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query

from api.services import territorial_intelligence_service as tis

router = APIRouter()


@router.get("/territories", summary="Lister les territoires (intelligence territoriale)")
def list_territories(
    province: str | None = Query(None),
    zone: str | None = Query(None),
    priority_level: str | None = Query(None),
    data_quality: str | None = Query(None),
    q: str | None = Query(None, description="Recherche rapide"),
    limit: int = Query(500, gt=0, le=5000),
) -> dict[str, Any]:
    return tis.list_territories(
        province=province,
        zone=zone,
        priority_level=priority_level,
        data_quality=data_quality,
        q=q,
        limit=limit,
    )


@router.get("/territories/{territory_id}", summary="Profil Territorial FDSU")
def get_territory_profile(territory_id: str) -> dict[str, Any]:
    result = tis.build_territorial_profile(territory_id)
    if not result:
        raise HTTPException(status_code=404, detail="Territoire introuvable.")
    return result


@router.get("/territories/{territory_id}/map", summary="Carte GeoJSON du territoire")
def get_territory_map(territory_id: str) -> dict[str, Any]:
    result = tis.build_map_payload(territory_id)
    if not result:
        raise HTTPException(status_code=404, detail="Carte territoriale introuvable.")
    return result


@router.get("/territories/{territory_id}/indicators", summary="Indicateurs territoriaux")
def get_territory_indicators(territory_id: str) -> dict[str, Any]:
    result = tis.build_indicators(territory_id)
    if not result:
        raise HTTPException(status_code=404, detail="Indicateurs territoriaux introuvables.")
    return result


@router.get("/territories/{territory_id}/recommendations", summary="Recommandations explicables")
def get_territory_recommendations(territory_id: str) -> dict[str, Any]:
    result = tis.build_recommendations(territory_id)
    if not result:
        raise HTTPException(status_code=404, detail="Recommandations introuvables.")
    return result


@router.get("/territories/{territory_id}/explain", summary="Justification territoriale")
def explain_territory(territory_id: str) -> dict[str, Any]:
    result = tis.explain_territory(territory_id)
    if not result:
        raise HTTPException(status_code=404, detail="Justification territoriale introuvable.")
    return result
