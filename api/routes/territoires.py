from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from api.dependencies import get_db
from api.schemas.base import TerritoireCreate, TerritoireRead
from api.services.territoire_service import (
    create_territoire,
    delete_territoire,
    get_territoire,
    list_territoires,
    update_territoire,
)

router = APIRouter()


@router.post(
    "/",
    response_model=TerritoireRead,
    summary="Créer un territoire",
)
def create(payload: TerritoireCreate, db: Session = Depends(get_db)) -> TerritoireRead:
    """Crée un territoire dans le référentiel administratif FDSU RDC."""
    return create_territoire(db, payload)


@router.get(
    "/",
    response_model=list[TerritoireRead],
    summary="Lister les territoires",
)
def read_all(
    skip: int = Query(0, ge=0, description="Nombre d'éléments à ignorer pour la pagination"),
    limit: int = Query(100, gt=0, description="Nombre maximal d'éléments renvoyés"),
    db: Session = Depends(get_db),
) -> list[TerritoireRead]:
    """Retourne la liste des territoires avec options de pagination."""
    return list_territoires(db, skip=skip, limit=limit)


@router.get(
    "/{territoire_id}",
    response_model=TerritoireRead,
    summary="Obtenir un territoire",
)
def read_one(territoire_id: int, db: Session = Depends(get_db)) -> TerritoireRead:
    """Récupère un territoire par son identifiant."""
    territoire = get_territoire(db, territoire_id)
    if territoire is None:
        raise HTTPException(status_code=404, detail="Territoire non trouvé")
    return territoire


@router.put(
    "/{territoire_id}",
    response_model=TerritoireRead,
    summary="Mettre à jour un territoire",
)
def update(territoire_id: int, payload: TerritoireCreate, db: Session = Depends(get_db)) -> TerritoireRead:
    """Met à jour les informations d'un territoire existant."""
    territoire = update_territoire(db, territoire_id, payload)
    if territoire is None:
        raise HTTPException(status_code=404, detail="Territoire non trouvé")
    return territoire


@router.delete(
    "/{territoire_id}",
    summary="Supprimer un territoire",
)
def delete(territoire_id: int, db: Session = Depends(get_db)) -> dict[str, bool]:
    """Supprime un territoire du référentiel administratif."""
    success = delete_territoire(db, territoire_id)
    if not success:
        raise HTTPException(status_code=404, detail="Territoire non trouvé")
    return {"deleted": True}
