from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from api.dependencies import get_db
from api.schemas.base import PhotoCreate, PhotoRead
from api.services.photo_service import (
    create_photo,
    delete_photo,
    get_photo,
    list_photos,
    update_photo,
)

router = APIRouter()


@router.post("/", response_model=PhotoRead)
def create(payload: PhotoCreate, db: Session = Depends(get_db)) -> PhotoRead:
    return create_photo(db, payload)


@router.get("/", response_model=list[PhotoRead])
def read_all(skip: int = Query(0, ge=0), limit: int = Query(100, gt=0), db: Session = Depends(get_db)) -> list[PhotoRead]:
    return list_photos(db, skip=skip, limit=limit)


@router.get("/{photo_id}", response_model=PhotoRead)
def read_one(photo_id: int, db: Session = Depends(get_db)) -> PhotoRead:
    photo = get_photo(db, photo_id)
    if photo is None:
        raise HTTPException(status_code=404, detail="Photo non trouvée")
    return photo


@router.put("/{photo_id}", response_model=PhotoRead)
def update(photo_id: int, payload: PhotoCreate, db: Session = Depends(get_db)) -> PhotoRead:
    photo = update_photo(db, photo_id, payload)
    if photo is None:
        raise HTTPException(status_code=404, detail="Photo non trouvée")
    return photo


@router.delete("/{photo_id}")
def delete(photo_id: int, db: Session = Depends(get_db)) -> dict[str, bool]:
    success = delete_photo(db, photo_id)
    if not success:
        raise HTTPException(status_code=404, detail="Photo non trouvée")
    return {"deleted": True}
