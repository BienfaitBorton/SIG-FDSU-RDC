from sqlalchemy.orm import Session

from app.models import Collectivite
from api.schemas.base import CollectiviteCreate


def create_collectivite(session: Session, payload: CollectiviteCreate) -> Collectivite:
    collectivite = Collectivite(**payload.model_dump())
    session.add(collectivite)
    session.commit()
    session.refresh(collectivite)
    return collectivite


def get_collectivite(session: Session, collectivite_id: int) -> Collectivite | None:
    return session.get(Collectivite, collectivite_id)


def list_collectivites(session: Session, skip: int = 0, limit: int = 100) -> list[Collectivite]:
    return session.query(Collectivite).offset(skip).limit(limit).all()


def update_collectivite(session: Session, collectivite_id: int, payload: CollectiviteCreate) -> Collectivite | None:
    collectivite = session.get(Collectivite, collectivite_id)
    if collectivite is None:
        return None
    for key, value in payload.model_dump().items():
        setattr(collectivite, key, value)
    session.commit()
    session.refresh(collectivite)
    return collectivite


def delete_collectivite(session: Session, collectivite_id: int) -> bool:
    collectivite = session.get(Collectivite, collectivite_id)
    if collectivite is None:
        return False
    session.delete(collectivite)
    session.commit()
    return True
