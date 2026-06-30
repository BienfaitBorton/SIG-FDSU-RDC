from sqlalchemy.orm import Session

from app.models import Village
from api.schemas.base import VillageCreate


def create_village(session: Session, payload: VillageCreate) -> Village:
    village = Village(**payload.model_dump())
    session.add(village)
    session.commit()
    session.refresh(village)
    return village


def get_village(session: Session, village_id: int) -> Village | None:
    return session.get(Village, village_id)


def list_villages(session: Session, skip: int = 0, limit: int = 100) -> list[Village]:
    return session.query(Village).offset(skip).limit(limit).all()


def update_village(session: Session, village_id: int, payload: VillageCreate) -> Village | None:
    village = session.get(Village, village_id)
    if village is None:
        return None
    for key, value in payload.model_dump().items():
        setattr(village, key, value)
    session.commit()
    session.refresh(village)
    return village


def delete_village(session: Session, village_id: int) -> bool:
    village = session.get(Village, village_id)
    if village is None:
        return False
    session.delete(village)
    session.commit()
    return True
