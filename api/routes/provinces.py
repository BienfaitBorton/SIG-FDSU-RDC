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


@router.post(
    "/",
    response_model=ProvinceRead,
    summary="Créer une province",
)
def create(payload: ProvinceCreate, db: Session = Depends(get_db)) -> ProvinceRead:
    """Crée une nouvelle province dans le référentiel administratif FDSU RDC."""
    return create_province(db, payload)


@router.get(
    "/",
    response_model=list[ProvinceRead],
    summary="Lister les provinces",
)
def read_all(
    skip: int = Query(0, ge=0, description="Nombre d'éléments à ignorer pour la pagination"),
    limit: int = Query(100, gt=0, description="Nombre maximal d'éléments renvoyés"),
    db: Session = Depends(get_db),
) -> list[ProvinceRead]:
    """Retourne la liste des provinces avec options de pagination."""
    return list_provinces(db, skip=skip, limit=limit)


@router.get(
    "/{province_id}",
    response_model=ProvinceRead,
    summary="Obtenir une province",
)
def read_one(province_id: int, db: Session = Depends(get_db)) -> ProvinceRead:
    """Récupère une province par son identifiant."""
    province = get_province(db, province_id)
    if province is None:
        raise HTTPException(status_code=404, detail="Province non trouvée")
    return province


@router.put(
    "/{province_id}",
    response_model=ProvinceRead,
    summary="Mettre à jour une province",
)
def update(province_id: int, payload: ProvinceCreate, db: Session = Depends(get_db)) -> ProvinceRead:
    """Met à jour les informations d'une province existante."""
    province = update_province(db, province_id, payload)
    if province is None:
        raise HTTPException(status_code=404, detail="Province non trouvée")
    return province


@router.delete(
    "/{province_id}",
    summary="Supprimer une province",
)
def delete(province_id: int, db: Session = Depends(get_db)) -> dict[str, bool]:
    """Supprime une province du référentiel administratif."""
    success = delete_province(db, province_id)
    if not success:
        raise HTTPException(status_code=404, detail="Province non trouvée")
    return {"deleted": True}
