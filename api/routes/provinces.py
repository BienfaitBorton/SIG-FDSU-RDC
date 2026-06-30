from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from api.dependencies import get_db
from api.schemas.base import ProvinceCreate, ProvinceRead
from api.services.province_service import (
    create_province,
    delete_province,
    get_province,
    list_provinces,
    update_province,
)

router = APIRouter()


@router.post("/", response_model=ProvinceRead)
def create(payload: ProvinceCreate, db: Session = Depends(get_db)) -> ProvinceRead:
    return create_province(db, payload)


@router.get("/", response_model=list[ProvinceRead])
def read_all(skip: int = Query(0, ge=0), limit: int = Query(100, gt=0), db: Session = Depends(get_db)) -> list[ProvinceRead]:
    return list_provinces(db, skip=skip, limit=limit)


@router.get("/{province_id}", response_model=ProvinceRead)
def read_one(province_id: int, db: Session = Depends(get_db)) -> ProvinceRead:
    province = get_province(db, province_id)
    if province is None:
        raise HTTPException(status_code=404, detail="Province non trouvée")
    return province


@router.put("/{province_id}", response_model=ProvinceRead)
def update(province_id: int, payload: ProvinceCreate, db: Session = Depends(get_db)) -> ProvinceRead:
    province = update_province(db, province_id, payload)
    if province is None:
        raise HTTPException(status_code=404, detail="Province non trouvée")
    return province


@router.delete("/{province_id}")
def delete(province_id: int, db: Session = Depends(get_db)) -> dict[str, bool]:
    success = delete_province(db, province_id)
    if not success:
        raise HTTPException(status_code=404, detail="Province non trouvée")
    return {"deleted": True}
