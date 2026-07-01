from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from api.dependencies import get_db
from api.schemas.base import VillageCreate, VillageRead
from api.services.village_service import (
    create_village,
    delete_village,
    get_village,
    list_villages,
    update_village,
)

router = APIRouter()


@router.post(
    "/",
    response_model=VillageRead,
    summary="Créer un village",
)
def create(payload: VillageCreate, db: Session = Depends(get_db)) -> VillageRead:
    """Crée un village rattaché à un groupement du référentiel administratif."""
    return create_village(db, payload)


@router.get(
    "/",
    response_model=list[VillageRead],
    summary="Lister les villages",
)
def read_all(
    skip: int = Query(0, ge=0, description="Nombre d'éléments à ignorer pour la pagination"),
    limit: int = Query(100, gt=0, description="Nombre maximal d'éléments renvoyés"),
    db: Session = Depends(get_db),
) -> list[VillageRead]:
    """Retourne la liste des villages avec options de pagination."""
    return list_villages(db, skip=skip, limit=limit)


@router.get(
    "/{village_id}",
    response_model=VillageRead,
    summary="Obtenir un village",
)
def read_one(village_id: int, db: Session = Depends(get_db)) -> VillageRead:
    """Récupère un village par son identifiant."""
    village = get_village(db, village_id)
    if village is None:
        raise HTTPException(status_code=404, detail="Village non trouvé")
    return village


@router.put(
    "/{village_id}",
    response_model=VillageRead,
    summary="Mettre à jour un village",
)
def update(village_id: int, payload: VillageCreate, db: Session = Depends(get_db)) -> VillageRead:
    """Met à jour les informations d'un village existant."""
    village = update_village(db, village_id, payload)
    if village is None:
        raise HTTPException(status_code=404, detail="Village non trouvé")
    return village


@router.delete(
    "/{village_id}",
    summary="Supprimer un village",
)
def delete(village_id: int, db: Session = Depends(get_db)) -> dict[str, bool]:
    """Supprime un village du référentiel administratif."""
    success = delete_village(db, village_id)
    if not success:
        raise HTTPException(status_code=404, detail="Village non trouvé")
    return {"deleted": True}
