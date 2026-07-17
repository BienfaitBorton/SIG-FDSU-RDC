"""API du Référentiel National CENI v1.0."""

from typing import Any

from fastapi import APIRouter, HTTPException, Query

from api.services import ceni_registry_service as service

router = APIRouter()


@router.get("/sites")
def sites(q: str | None = None, category: str | None = None, province: str | None = None, territory: str | None = None, quality: str | None = None, limit: int = Query(100, ge=1, le=5000), offset: int = Query(0, ge=0)) -> dict[str, Any]:
    return service.list_sites(q=q, category=category, province=province, territory=territory, quality=quality, limit=limit, offset=offset)


@router.get("/sites/{asset_uid}")
def site(asset_uid: str) -> dict[str, Any]:
    row = service.get_site(asset_uid)
    if row is None:
        raise HTTPException(status_code=404, detail="Site CENI introuvable.")
    return {"site": row}


@router.get("/statistics")
def statistics() -> dict[str, Any]:
    return service.statistics()


@router.get("/classification/statistics")
def classification_statistics() -> dict[str, Any]:
    return service.classification_statistics()


@router.get("/classification/rules")
def classification_rules() -> dict[str, Any]:
    return service.classification_rules()


@router.get("/classification/review")
def classification_review(limit: int = Query(100, ge=1, le=5000), offset: int = Query(0, ge=0)) -> dict[str, Any]:
    return service.classification_review(limit=limit, offset=offset)


@router.get("/sites/{asset_uid}/classification")
def site_classification(asset_uid: str) -> dict[str, Any]:
    payload = service.site_classification(asset_uid)
    if payload is None:
        raise HTTPException(status_code=404, detail="Classification CENI introuvable.")
    return {"classification": payload}


@router.get("/data-quality")
def data_quality(limit: int = Query(500, ge=1, le=5000), offset: int = Query(0, ge=0)) -> dict[str, Any]:
    return service.data_quality(limit=limit, offset=offset)


@router.get("/categories")
def categories() -> dict[str, Any]:
    return service.categories()


@router.get("/map")
def map_data(category: str | None = None, province: str | None = None, limit: int = Query(5000, ge=1, le=10000)) -> dict[str, Any]:
    return service.map_features(category=category, province=province, limit=limit)


@router.get("/import-batches")
def import_batches() -> dict[str, Any]:
    return service.import_batches()
