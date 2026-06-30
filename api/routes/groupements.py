from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from api.dependencies import get_db
from api.schemas.base import GroupementCreate, GroupementRead
from api.services.groupement_service import (
    create_groupement,
    delete_groupement,
    get_groupement,
    list_groupements,
    update_groupement,
)

router = APIRouter()


@router.post("/", response_model=GroupementRead)
def create(payload: GroupementCreate, db: Session = Depends(get_db)) -> GroupementRead:
    return create_groupement(db, payload)


@router.get("/", response_model=list[GroupementRead])
def read_all(skip: int = Query(0, ge=0), limit: int = Query(100, gt=0), db: Session = Depends(get_db)) -> list[GroupementRead]:
    return list_groupements(db, skip=skip, limit=limit)


@router.get("/{groupement_id}", response_model=GroupementRead)
def read_one(groupement_id: int, db: Session = Depends(get_db)) -> GroupementRead:
    groupement = get_groupement(db, groupement_id)
    if groupement is None:
        raise HTTPException(status_code=404, detail="Groupement non trouvé")
    return groupement


@router.put("/{groupement_id}", response_model=GroupementRead)
def update(groupement_id: int, payload: GroupementCreate, db: Session = Depends(get_db)) -> GroupementRead:
    groupement = update_groupement(db, groupement_id, payload)
    if groupement is None:
        raise HTTPException(status_code=404, detail="Groupement non trouvé")
    return groupement


@router.delete("/{groupement_id}")
def delete(groupement_id: int, db: Session = Depends(get_db)) -> dict[str, bool]:
    success = delete_groupement(db, groupement_id)
    if not success:
        raise HTTPException(status_code=404, detail="Groupement non trouvé")
    return {"deleted": True}
