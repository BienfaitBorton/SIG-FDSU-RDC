"""API du National Territorial Intelligence Engine v1."""

from typing import Any

from fastapi import APIRouter, HTTPException, Query

from api.services import national_territorial_intelligence_engine as ntie

router = APIRouter()


def _profile(entity_id: str) -> dict[str, Any]:
    profile = ntie.build_profile(entity_id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Profil territorial introuvable.")
    return profile


@router.get("")
def profiles(level: str | None = Query(None), limit: int = Query(100, ge=1, le=1000)) -> dict[str, Any]:
    try:
        return ntie.list_profiles(level=level, limit=limit)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/{entity_id}")
def profile(entity_id: str) -> dict[str, Any]:
    return _profile(entity_id)


@router.get("/{entity_id}/score")
def score(entity_id: str) -> dict[str, Any]:
    profile = _profile(entity_id)
    return {"entity": profile["entity"], "score": profile["score"]}


@router.get("/{entity_id}/population")
def population(entity_id: str) -> dict[str, Any]:
    profile = _profile(entity_id)
    return {"entity": profile["entity"], "population": ntie.indicator_section(profile, ("population",))}


@router.get("/{entity_id}/coverage")
def coverage(entity_id: str) -> dict[str, Any]:
    profile = _profile(entity_id)
    keys = ("mobile_coverage", "population_covered", "population_uncovered", "localities", "localities_covered", "localities_uncovered")
    return {"entity": profile["entity"], "coverage": ntie.indicator_section(profile, keys)}


@router.get("/{entity_id}/explainability")
def explainability(entity_id: str) -> dict[str, Any]:
    profile = _profile(entity_id)
    return {"entity": profile["entity"], "explainability": profile["explainability"], "indicators": profile["indicators"]}


@router.get("/{entity_id}/evolution")
def evolution(entity_id: str) -> dict[str, Any]:
    profile = _profile(entity_id)
    return {"entity": profile["entity"], "evolution": profile["evolution"]}
