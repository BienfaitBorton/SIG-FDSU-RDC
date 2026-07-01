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


@router.post(
    "/",
    response_model=PhotoRead,
    summary="Créer une photo",
)
def create(payload: PhotoCreate, db: Session = Depends(get_db)) -> PhotoRead:
    """Crée une photo associée à une mission FDSU."""
    return create_photo(db, payload)


@router.get(
    "/",
    response_model=list[PhotoRead],
    summary="Lister les photos",
)
def read_all(
    skip: int = Query(0, ge=0, description="Nombre d'éléments à ignorer pour la pagination"),
    limit: int = Query(100, gt=0, description="Nombre maximal d'éléments renvoyés"),
    db: Session = Depends(get_db),
) -> list[PhotoRead]:
    """Retourne la liste des photos avec pagination."""
    return list_photos(db, skip=skip, limit=limit)


@router.get(
    "/{photo_id}",
    response_model=PhotoRead,
    summary="Obtenir une photo",
)
def read_one(photo_id: int, db: Session = Depends(get_db)) -> PhotoRead:
    """Récupère une photo par son identifiant."""
    photo = get_photo(db, photo_id)
    if photo is None:
        raise HTTPException(status_code=404, detail="Photo non trouvée")
    return photo


@router.put(
    "/{photo_id}",
    response_model=PhotoRead,
    summary="Mettre à jour une photo",
)
def update(photo_id: int, payload: PhotoCreate, db: Session = Depends(get_db)) -> PhotoRead:
    """Met à jour les informations d'une photo existante."""
    photo = update_photo(db, photo_id, payload)
    if photo is None:
        raise HTTPException(status_code=404, detail="Photo non trouvée")
    return photo


@router.delete(
    "/{photo_id}",
    summary="Supprimer une photo",
)
def delete(photo_id: int, db: Session = Depends(get_db)) -> dict[str, bool]:
    """Supprime une photo du référentiel FDSU."""
    success = delete_photo(db, photo_id)
    if not success:
        raise HTTPException(status_code=404, detail="Photo non trouvée")
    return {"deleted": True}
