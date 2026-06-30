from sqlalchemy.orm import Session

from app.models import Site
from api.schemas.base import SiteCreate


def create_site(session: Session, payload: SiteCreate) -> Site:
    site = Site(**payload.model_dump())
    session.add(site)
    session.commit()
    session.refresh(site)
    return site


def get_site(session: Session, site_id: int) -> Site | None:
    return session.get(Site, site_id)


def list_sites(session: Session, skip: int = 0, limit: int = 100) -> list[Site]:
    return session.query(Site).offset(skip).limit(limit).all()


def update_site(session: Session, site_id: int, payload: SiteCreate) -> Site | None:
    site = session.get(Site, site_id)
    if site is None:
        return None
    for key, value in payload.model_dump().items():
        setattr(site, key, value)
    session.commit()
    session.refresh(site)
    return site


def delete_site(session: Session, site_id: int) -> bool:
    site = session.get(Site, site_id)
    if site is None:
        return False
    session.delete(site)
    session.commit()
    return True
