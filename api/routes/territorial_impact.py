"""API — Moteur d’Impact Territorial et Progression de Couverture."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query

from api.services import territorial_impact_engine as tie

router = APIRouter()


@router.get("/audit/sources", summary="Matrice d’audit des sources démographiques")
def audit_sources() -> dict[str, Any]:
    return tie.audit_population_sources()


@router.get("/sites/{asset_id}", summary="Profil d’impact territorial d’un site FDSU")
def site_impact(
    asset_id: str,
    program_code: str | None = Query(default=None),
    mode: str = Query(default="planned", description="planned | simulation | real"),
) -> dict[str, Any]:
    payload = tie.build_site_impact_profile(asset_id, program_code=program_code, scenario_mode=mode)
    if not payload:
        raise HTTPException(status_code=404, detail="Site introuvable pour le calcul d’impact.")
    return payload


@router.get("/ccn/{ccn_id}", summary="Profil d’impact d’un CCN (≠ couverture radio)")
def ccn_impact(ccn_id: str) -> dict[str, Any]:
    payload = tie.build_ccn_impact_profile(ccn_id)
    if not payload:
        raise HTTPException(status_code=404, detail="CCN introuvable.")
    return payload


@router.get("/scenario", summary="Scénario de déploiement et progression cumulative")
def deployment_scenario(
    level: str = Query(default="national"),
    province: str | None = Query(default=None),
    territoire: str | None = Query(default=None),
    zone: str | None = Query(default=None),
    programs: str = Query(default="sites_40,sites_300,sites_20476"),
    mode: str = Query(default="planned"),
    order: str = Query(default="program_phase"),
    limit_per_program: int = Query(default=25, ge=1, le=100),
    include_ccn: bool = Query(default=True),
) -> dict[str, Any]:
    prog_list = [p.strip() for p in programs.split(",") if p.strip()]
    return tie.build_deployment_scenario(
        scope={
            "level": level,
            "province": province,
            "territoire": territoire,
            "zone": zone,
        },
        programs=prog_list,
        mode=mode,
        order=order,
        limit_per_program=limit_per_program,
        include_ccn=include_ccn,
    )
