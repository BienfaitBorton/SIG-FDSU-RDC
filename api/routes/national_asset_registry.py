"""API National FDSU Asset Registry v1."""

from typing import Any

from fastapi import APIRouter, HTTPException, Query

from api.services import national_asset_registry_service as registry

router = APIRouter()


def _required(value: dict[str, Any] | None) -> dict[str, Any]:
    if value is None:
        raise HTTPException(status_code=404, detail="Actif introuvable dans le Registry.")
    return value


@router.get("/manifest")
def manifest() -> dict[str, Any]:
    return registry.manifest()


@router.get("/statistics")
def statistics() -> dict[str, Any]:
    return registry.statistics()


@router.get("/assets")
def assets(
    program: str | None = Query(None),
    asset_type: str | None = Query(None),
    province: str | None = Query(None),
    q: str | None = Query(None),
    limit: int = Query(100, ge=1, le=2000),
    offset: int = Query(0, ge=0),
) -> dict[str, Any]:
    return registry.list_assets(program=program, asset_type=asset_type, province=province, q=q, limit=limit, offset=offset)


@router.get("/assets/{asset_id}")
def asset(asset_id: str) -> dict[str, Any]:
    return {"asset": _required(registry.get_asset(asset_id))}


@router.get("/assets/{asset_id}/relationships")
def relationships(asset_id: str) -> dict[str, Any]:
    return _required(registry.relationships(asset_id))


@router.get("/assets/{asset_id}/population")
def population(asset_id: str) -> dict[str, Any]:
    return _required(registry.population(asset_id))


@router.get("/assets/{asset_id}/lifecycle")
def lifecycle(asset_id: str) -> dict[str, Any]:
    return _required(registry.lifecycle(asset_id))


@router.get("/assets/{asset_id}/impact")
def impact(asset_id: str) -> dict[str, Any]:
    return _required(registry.impact(asset_id))


@router.get("/assets/{asset_id}/explainability")
def explainability(asset_id: str, field: str | None = Query(None)) -> dict[str, Any]:
    return _required(registry.explainability(asset_id, field=field))
