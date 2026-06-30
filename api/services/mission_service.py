from sqlalchemy.orm import Session

from app.models import Mission
from api.schemas.base import MissionCreate


def create_mission(session: Session, payload: MissionCreate) -> Mission:
    mission = Mission(**payload.model_dump())
    session.add(mission)
    session.commit()
    session.refresh(mission)
    return mission


def get_mission(session: Session, mission_id: int) -> Mission | None:
    return session.get(Mission, mission_id)


def list_missions(session: Session, skip: int = 0, limit: int = 100) -> list[Mission]:
    return session.query(Mission).offset(skip).limit(limit).all()


def update_mission(session: Session, mission_id: int, payload: MissionCreate) -> Mission | None:
    mission = session.get(Mission, mission_id)
    if mission is None:
        return None
    for key, value in payload.model_dump().items():
        setattr(mission, key, value)
    session.commit()
    session.refresh(mission)
    return mission


def delete_mission(session: Session, mission_id: int) -> bool:
    mission = session.get(Mission, mission_id)
    if mission is None:
        return False
    session.delete(mission)
    session.commit()
    return True
