"""API — Program Lifecycle Engine (six dimensions de statut)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Query

from api.services import program_lifecycle_engine as ple

router = APIRouter()


@router.get("/audit/matrix", summary="Matrice d’audit des faux statuts")
def audit_matrix() -> dict[str, Any]:
    return ple.audit_status_matrix()


@router.get("/programs", summary="Tableau de suivi des programmes")
def programs_board() -> dict[str, Any]:
    return ple.build_programs_board()


@router.get("/programs/{program_code}", summary="Cycle de vie d’un programme")
def program_lifecycle(program_code: str) -> dict[str, Any]:
    return ple.resolve_program_lifecycle(program_code)


@router.get("/assets/{asset_id}", summary="Cycle de vie d’un actif (site / CCN)")
def asset_lifecycle(
    asset_id: str,
    program_code: str | None = Query(default=None),
    asset_type: str = Query(default="FDSU_SITE"),
    raw_status: str | None = Query(default=None),
    data_class: str | None = Query(default=None),
) -> dict[str, Any]:
    return ple.resolve_asset_lifecycle(
        program_code=program_code,
        asset_id=asset_id,
        raw_status=raw_status,
        asset_type=asset_type,
        data_class=data_class,
    )


@router.get("/history/contract", summary="Contrat d’historique (sans inventer le passé)")
def history_contract() -> dict[str, Any]:
    return ple.history_contract_template()


@router.get("/labels/data-maturity/{code}", summary="Libellé maturité données (≠ opérationnel physique)")
def data_maturity_label(code: str) -> dict[str, Any]:
    return {"code": code, "label": ple.data_maturity_label(code)}
