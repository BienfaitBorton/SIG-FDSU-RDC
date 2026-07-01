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


@router.post(
    "/",
    response_model=GroupementRead,
    summary="Créer un groupement",
)
def create(payload: GroupementCreate, db: Session = Depends(get_db)) -> GroupementRead:
    """Crée un groupement administratif dans le référentiel FDSU RDC."""
    return create_groupement(db, payload)


@router.get(
    "/",
    response_model=list[GroupementRead],
    summary="Lister les groupements",
)
def read_all(
    skip: int = Query(0, ge=0, description="Nombre d'éléments à ignorer pour la pagination"),
    limit: int = Query(100, gt=0, description="Nombre maximal d'éléments renvoyés"),
    db: Session = Depends(get_db),
) -> list[GroupementRead]:
    """Retourne la liste des groupements avec options de pagination."""
    return list_groupements(db, skip=skip, limit=limit)


@router.get(
    "/{groupement_id}",
    response_model=GroupementRead,
    summary="Obtenir un groupement",
)
def read_one(groupement_id: int, db: Session = Depends(get_db)) -> GroupementRead:
    """Récupère un groupement par son identifiant."""
    groupement = get_groupement(db, groupement_id)
    if groupement is None:
        raise HTTPException(status_code=404, detail="Groupement non trouvé")
    return groupement


@router.put(
    "/{groupement_id}",
    response_model=GroupementRead,
    summary="Mettre à jour un groupement",
)
def update(groupement_id: int, payload: GroupementCreate, db: Session = Depends(get_db)) -> GroupementRead:
    """Met à jour les informations d'un groupement existant."""
    groupement = update_groupement(db, groupement_id, payload)
    if groupement is None:
        raise HTTPException(status_code=404, detail="Groupement non trouvé")
    return groupement


@router.delete(
    "/{groupement_id}",
    summary="Supprimer un groupement",
)
def delete(groupement_id: int, db: Session = Depends(get_db)) -> dict[str, bool]:
    """Supprime un groupement du référentiel administratif."""
    success = delete_groupement(db, groupement_id)
    if not success:
        raise HTTPException(status_code=404, detail="Groupement non trouvé")
    return {"deleted": True}
