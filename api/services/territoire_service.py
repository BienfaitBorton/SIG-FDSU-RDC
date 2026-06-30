from sqlalchemy.orm import Session

from app.models import Territoire
from api.schemas.base import TerritoireCreate


def create_territoire(session: Session, payload: TerritoireCreate) -> Territoire:
    territoire = Territoire(**payload.model_dump())
    session.add(territoire)
    session.commit()
    session.refresh(territoire)
    return territoire


def get_territoire(session: Session, territoire_id: int) -> Territoire | None:
    return session.get(Territoire, territoire_id)


def list_territoires(session: Session, skip: int = 0, limit: int = 100) -> list[Territoire]:
    return session.query(Territoire).offset(skip).limit(limit).all()


def update_territoire(session: Session, territoire_id: int, payload: TerritoireCreate) -> Territoire | None:
    territoire = session.get(Territoire, territoire_id)
    if territoire is None:
        return None
    for key, value in payload.model_dump().items():
        setattr(territoire, key, value)
    session.commit()
    session.refresh(territoire)
    return territoire


def delete_territoire(session: Session, territoire_id: int) -> bool:
    territoire = session.get(Territoire, territoire_id)
    if territoire is None:
        return False
    session.delete(territoire)
    session.commit()
    return True
