from sqlalchemy.orm import Session

from app.models import Photo
from api.schemas.base import PhotoCreate


def create_photo(session: Session, payload: PhotoCreate) -> Photo:
    photo = Photo(**payload.model_dump())
    session.add(photo)
    session.commit()
    session.refresh(photo)
    return photo


def get_photo(session: Session, photo_id: int) -> Photo | None:
    return session.get(Photo, photo_id)


def list_photos(session: Session, skip: int = 0, limit: int = 100) -> list[Photo]:
    return session.query(Photo).offset(skip).limit(limit).all()


def update_photo(session: Session, photo_id: int, payload: PhotoCreate) -> Photo | None:
    photo = session.get(Photo, photo_id)
    if photo is None:
        return None
    for key, value in payload.model_dump().items():
        setattr(photo, key, value)
    session.commit()
    session.refresh(photo)
    return photo


def delete_photo(session: Session, photo_id: int) -> bool:
    photo = session.get(Photo, photo_id)
    if photo is None:
        return False
    session.delete(photo)
    session.commit()
    return True
