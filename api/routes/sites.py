from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from api.dependencies import get_db
from api.schemas.base import SiteCreate, SiteRead
from api.services.site_service import (
    create_site,
    delete_site,
    get_site,
    list_sites,
    update_site,
)

router = APIRouter()


@router.post(
    "/",
    response_model=SiteRead,
    summary="Créer une fiche site FDSU",
)
def create(payload: SiteCreate, db: Session = Depends(get_db)) -> SiteRead:
    """Crée une fiche technique de site FDSU en utilisant les informations du référentiel administratif."""
    return create_site(db, payload)


@router.get(
    "/",
    response_model=list[SiteRead],
    summary="Lister les sites",
)
def read_all(
    skip: int = Query(0, ge=0, description="Nombre d'éléments à ignorer pour la pagination"),
    limit: int = Query(100, gt=0, description="Nombre maximal d'éléments renvoyés"),
    db: Session = Depends(get_db),
) -> list[SiteRead]:
    """Retourne la liste des sites FDSU avec options de pagination."""
    return list_sites(db, skip=skip, limit=limit)


@router.get(
    "/{site_id}",
    response_model=SiteRead,
    summary="Obtenir un site",
)
def read_one(site_id: int, db: Session = Depends(get_db)) -> SiteRead:
    """Récupère un site FDSU par son identifiant."""
    site = get_site(db, site_id)
    if site is None:
        raise HTTPException(status_code=404, detail="Site non trouvé")
    return site


@router.put(
    "/{site_id}",
    response_model=SiteRead,
    summary="Mettre à jour un site",
)
def update(site_id: int, payload: SiteCreate, db: Session = Depends(get_db)) -> SiteRead:
    """Met à jour la fiche technique d'un site FDSU."""
    site = update_site(db, site_id, payload)
    if site is None:
        raise HTTPException(status_code=404, detail="Site non trouvé")
    return site


@router.delete(
    "/{site_id}",
    summary="Supprimer un site",
)
def delete(site_id: int, db: Session = Depends(get_db)) -> dict[str, bool]:
    """Supprime un site du référentiel FDSU."""
    success = delete_site(db, site_id)
    if not success:
        raise HTTPException(status_code=404, detail="Site non trouvé")
    return {"deleted": True}
