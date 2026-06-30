from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from api.dependencies import get_db
from api.schemas.base import SiteCreate, SiteRead
from api.services.site_service import (
    create_site,
    delete_site,
    get_site,
    list_sites,
    update_site,
)

router = APIRouter()


@router.post("/", response_model=SiteRead)
def create(payload: SiteCreate, db: Session = Depends(get_db)) -> SiteRead:
    return create_site(db, payload)


@router.get("/", response_model=list[SiteRead])
def read_all(skip: int = Query(0, ge=0), limit: int = Query(100, gt=0), db: Session = Depends(get_db)) -> list[SiteRead]:
    return list_sites(db, skip=skip, limit=limit)


@router.get("/{site_id}", response_model=SiteRead)
def read_one(site_id: int, db: Session = Depends(get_db)) -> SiteRead:
    site = get_site(db, site_id)
    if site is None:
        raise HTTPException(status_code=404, detail="Site non trouvé")
    return site


@router.put("/{site_id}", response_model=SiteRead)
def update(site_id: int, payload: SiteCreate, db: Session = Depends(get_db)) -> SiteRead:
    site = update_site(db, site_id, payload)
    if site is None:
        raise HTTPException(status_code=404, detail="Site non trouvé")
    return site


@router.delete("/{site_id}")
def delete(site_id: int, db: Session = Depends(get_db)) -> dict[str, bool]:
    success = delete_site(db, site_id)
    if not success:
        raise HTTPException(status_code=404, detail="Site non trouvé")
    return {"deleted": True}
