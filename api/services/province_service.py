from sqlalchemy.orm import Session

from app.models import Province
from api.schemas.base import ProvinceCreate


def create_province(session: Session, payload: ProvinceCreate) -> Province:
    province = Province(**payload.model_dump())
    session.add(province)
    session.commit()
    session.refresh(province)
    return province


def get_province(session: Session, province_id: int) -> Province | None:
    return session.get(Province, province_id)


def list_provinces(session: Session, skip: int = 0, limit: int = 100) -> list[Province]:
    return session.query(Province).offset(skip).limit(limit).all()


def update_province(session: Session, province_id: int, payload: ProvinceCreate) -> Province | None:
    province = session.get(Province, province_id)
    if province is None:
        return None
    for key, value in payload.model_dump().items():
        setattr(province, key, value)
    session.commit()
    session.refresh(province)
    return province


def delete_province(session: Session, province_id: int) -> bool:
    province = session.get(Province, province_id)
    if province is None:
        return False
    session.delete(province)
    session.commit()
    return True
