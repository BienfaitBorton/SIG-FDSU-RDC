from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from api.dependencies import get_db
from api.schemas.base import CollectiviteCreate, CollectiviteRead
from api.services.collectivite_service import (
    create_collectivite,
    delete_collectivite,
    get_collectivite,
    list_collectivites,
    update_collectivite,
)

router = APIRouter()


@router.post("/", response_model=CollectiviteRead)
def create(payload: CollectiviteCreate, db: Session = Depends(get_db)) -> CollectiviteRead:
    return create_collectivite(db, payload)


@router.get("/", response_model=list[CollectiviteRead])
def read_all(skip: int = Query(0, ge=0), limit: int = Query(100, gt=0), db: Session = Depends(get_db)) -> list[CollectiviteRead]:
    return list_collectivites(db, skip=skip, limit=limit)


@router.get("/{collectivite_id}", response_model=CollectiviteRead)
def read_one(collectivite_id: int, db: Session = Depends(get_db)) -> CollectiviteRead:
    collectivite = get_collectivite(db, collectivite_id)
    if collectivite is None:
        raise HTTPException(status_code=404, detail="Collectivité non trouvée")
    return collectivite


@router.put("/{collectivite_id}", response_model=CollectiviteRead)
def update(collectivite_id: int, payload: CollectiviteCreate, db: Session = Depends(get_db)) -> CollectiviteRead:
    collectivite = update_collectivite(db, collectivite_id, payload)
    if collectivite is None:
        raise HTTPException(status_code=404, detail="Collectivité non trouvée")
    return collectivite


@router.delete("/{collectivite_id}")
def delete(collectivite_id: int, db: Session = Depends(get_db)) -> dict[str, bool]:
    success = delete_collectivite(db, collectivite_id)
    if not success:
        raise HTTPException(status_code=404, detail="Collectivité non trouvée")
    return {"deleted": True}
