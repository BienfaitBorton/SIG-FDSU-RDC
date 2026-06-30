from sqlalchemy.orm import Session

from app.models import Groupement
from api.schemas.base import GroupementCreate


def create_groupement(session: Session, payload: GroupementCreate) -> Groupement:
    groupement = Groupement(**payload.model_dump())
    session.add(groupement)
    session.commit()
    session.refresh(groupement)
    return groupement


def get_groupement(session: Session, groupement_id: int) -> Groupement | None:
    return session.get(Groupement, groupement_id)


def list_groupements(session: Session, skip: int = 0, limit: int = 100) -> list[Groupement]:
    return session.query(Groupement).offset(skip).limit(limit).all()


def update_groupement(session: Session, groupement_id: int, payload: GroupementCreate) -> Groupement | None:
    groupement = session.get(Groupement, groupement_id)
    if groupement is None:
        return None
    for key, value in payload.model_dump().items():
        setattr(groupement, key, value)
    session.commit()
    session.refresh(groupement)
    return groupement


def delete_groupement(session: Session, groupement_id: int) -> bool:
    groupement = session.get(Groupement, groupement_id)
    if groupement is None:
        return False
    session.delete(groupement)
    session.commit()
    return True
