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


@router.post(
    "/",
    response_model=CollectiviteRead,
    summary="Créer une collectivité",
)
def create(payload: CollectiviteCreate, db: Session = Depends(get_db)) -> CollectiviteRead:
    """Crée une nouvelle collectivité administrative dans le référentiel FDSU RDC."""
    return create_collectivite(db, payload)


@router.get(
    "/",
    response_model=list[CollectiviteRead],
    summary="Lister les collectivités",
)
def read_all(
    skip: int = Query(0, ge=0, description="Nombre d'éléments à ignorer pour la pagination"),
    limit: int = Query(100, gt=0, description="Nombre maximal d'éléments renvoyés"),
    db: Session = Depends(get_db),
) -> list[CollectiviteRead]:
    """Retourne la liste des collectivités avec pagination."""
    return list_collectivites(db, skip=skip, limit=limit)


@router.get(
    "/{collectivite_id}",
    response_model=CollectiviteRead,
    summary="Obtenir une collectivité",
)
def read_one(collectivite_id: int, db: Session = Depends(get_db)) -> CollectiviteRead:
    """Récupère une collectivité par son identifiant."""
    collectivite = get_collectivite(db, collectivite_id)
    if collectivite is None:
        raise HTTPException(status_code=404, detail="Collectivité non trouvée")
    return collectivite


@router.put(
    "/{collectivite_id}",
    response_model=CollectiviteRead,
    summary="Mettre à jour une collectivité",
)
def update(collectivite_id: int, payload: CollectiviteCreate, db: Session = Depends(get_db)) -> CollectiviteRead:
    """Met à jour les informations d'une collectivité existante."""
    collectivite = update_collectivite(db, collectivite_id, payload)
    if collectivite is None:
        raise HTTPException(status_code=404, detail="Collectivité non trouvée")
    return collectivite


@router.delete(
    "/{collectivite_id}",
    summary="Supprimer une collectivité",
)
def delete(collectivite_id: int, db: Session = Depends(get_db)) -> dict[str, bool]:
    """Supprime une collectivité du référentiel administratif."""
    success = delete_collectivite(db, collectivite_id)
    if not success:
        raise HTTPException(status_code=404, detail="Collectivité non trouvée")
    return {"deleted": True}
