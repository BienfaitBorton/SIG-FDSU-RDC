"""API — Audit de couverture analytique SDG."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Query

from api.services import sdg_coverage_service as coverage

router = APIRouter()


@router.get("/coverage", summary="Matrice nationale de couverture analytique SDG")
def get_coverage(
    deep_sample: int = Query(default=6, ge=0, le=40),
    include_ccn: bool = Query(default=True),
) -> dict[str, Any]:
    return coverage.build_coverage_report(
        deep_sample_per_program=deep_sample,
        include_ccn=include_ccn,
    )


@router.get(
    "/assets/{asset_id}/explainability",
    summary="Fiche explicative — pourquoi l’analyse est complète / partielle / impossible",
)
def get_asset_explainability(
    asset_id: str,
    program_code: str | None = Query(default=None),
    run_matching: bool = Query(default=True),
) -> dict[str, Any]:
    return coverage.assess_asset(asset_id, program_code=program_code, run_matching=run_matching)
