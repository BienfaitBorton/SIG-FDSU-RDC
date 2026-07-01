from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from api.dependencies import get_db
from api.schemas.base import MissionCreate, MissionRead
from api.services.mission_service import (
    create_mission,
    delete_mission,
    get_mission,
    list_missions,
    update_mission,
)

router = APIRouter()


@router.post(
    "/",
    response_model=MissionRead,
    summary="Créer une mission",
)
def create(payload: MissionCreate, db: Session = Depends(get_db)) -> MissionRead:
    """Crée une mission de terrain rattachée à un site FDSU."""
    return create_mission(db, payload)


@router.get(
    "/",
    response_model=list[MissionRead],
    summary="Lister les missions",
)
def read_all(
    skip: int = Query(0, ge=0, description="Nombre d'éléments à ignorer pour la pagination"),
    limit: int = Query(100, gt=0, description="Nombre maximal d'éléments renvoyés"),
    db: Session = Depends(get_db),
) -> list[MissionRead]:
    """Retourne la liste des missions avec pagination."""
    return list_missions(db, skip=skip, limit=limit)


@router.get(
    "/{mission_id}",
    response_model=MissionRead,
    summary="Obtenir une mission",
)
def read_one(mission_id: int, db: Session = Depends(get_db)) -> MissionRead:
    """Récupère une mission par son identifiant."""
    mission = get_mission(db, mission_id)
    if mission is None:
        raise HTTPException(status_code=404, detail="Mission non trouvée")
    return mission


@router.put(
    "/{mission_id}",
    response_model=MissionRead,
    summary="Mettre à jour une mission",
)
def update(mission_id: int, payload: MissionCreate, db: Session = Depends(get_db)) -> MissionRead:
    """Met à jour les informations d'une mission existante."""
    mission = update_mission(db, mission_id, payload)
    if mission is None:
        raise HTTPException(status_code=404, detail="Mission non trouvée")
    return mission


@router.delete(
    "/{mission_id}",
    summary="Supprimer une mission",
)
def delete(mission_id: int, db: Session = Depends(get_db)) -> dict[str, bool]:
    """Supprime une mission du référentiel FDSU."""
    success = delete_mission(db, mission_id)
    if not success:
        raise HTTPException(status_code=404, detail="Mission non trouvée")
    return {"deleted": True}
