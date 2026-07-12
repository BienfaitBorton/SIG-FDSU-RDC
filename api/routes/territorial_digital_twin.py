"""API REST — Territorial Digital Twin Foundation."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException

from api.services import territorial_digital_twin_service as tdt

router = APIRouter()


@router.get("/{entity_type}/{entity_id}", summary="Jumeau numérique territorial complet")
def get_twin(entity_type: str, entity_id: str) -> dict[str, Any]:
    twin = tdt.build_twin(entity_type, entity_id)
    if not twin:
        raise HTTPException(status_code=404, detail="Entité territoriale introuvable.")
    return twin


@router.get("/{entity_type}/{entity_id}/summary", summary="Résumé exécutif du jumeau")
def get_summary(entity_type: str, entity_id: str) -> dict[str, Any]:
    payload = tdt.build_section(entity_type, entity_id, "summary")
    if not payload:
        raise HTTPException(status_code=404, detail="Entité territoriale introuvable.")
    return payload


@router.get("/{entity_type}/{entity_id}/connectivity", summary="Connectivité / besoins")
def get_connectivity(entity_type: str, entity_id: str) -> dict[str, Any]:
    payload = tdt.build_section(entity_type, entity_id, "connectivity")
    if not payload:
        raise HTTPException(status_code=404, detail="Entité territoriale introuvable.")
    return payload


@router.get("/{entity_type}/{entity_id}/services", summary="Services publics")
def get_services(entity_type: str, entity_id: str) -> dict[str, Any]:
    payload = tdt.build_section(entity_type, entity_id, "public_services")
    if not payload:
        raise HTTPException(status_code=404, detail="Entité territoriale introuvable.")
    return payload


@router.get("/{entity_type}/{entity_id}/accessibility", summary="Transport et accessibilité")
def get_accessibility(entity_type: str, entity_id: str) -> dict[str, Any]:
    payload = tdt.build_section(entity_type, entity_id, "accessibility")
    if not payload:
        raise HTTPException(status_code=404, detail="Entité territoriale introuvable.")
    return payload


@router.get("/{entity_type}/{entity_id}/programs", summary="Programmes FDSU / CCN")
def get_programs(entity_type: str, entity_id: str) -> dict[str, Any]:
    payload = tdt.build_section(entity_type, entity_id, "programs")
    if not payload:
        raise HTTPException(status_code=404, detail="Entité territoriale introuvable.")
    return payload


@router.get("/{entity_type}/{entity_id}/decision", summary="Priorité et justifications")
def get_decision(entity_type: str, entity_id: str) -> dict[str, Any]:
    payload = tdt.build_section(entity_type, entity_id, "decision")
    if not payload:
        raise HTTPException(status_code=404, detail="Entité territoriale introuvable.")
    return payload


@router.get("/{entity_type}/{entity_id}/quality", summary="Qualité et provenance")
def get_quality(entity_type: str, entity_id: str) -> dict[str, Any]:
    payload = tdt.build_section(entity_type, entity_id, "quality")
    if not payload:
        raise HTTPException(status_code=404, detail="Entité territoriale introuvable.")
    return payload


@router.get("/{entity_type}/{entity_id}/timeline", summary="Historique unifié (socle)")
def get_timeline(entity_type: str, entity_id: str) -> dict[str, Any]:
    payload = tdt.build_section(entity_type, entity_id, "timeline")
    if not payload:
        raise HTTPException(status_code=404, detail="Entité territoriale introuvable.")
    return payload
