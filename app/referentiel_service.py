"""
Services pour le référentiel administratif FDSU.
- Recherches par nom et par code
- Recherches hiérarchiques (enfants d'une entité)
- Statistiques d'import et lecture de l'historique

Conçu pour être utilisé depuis des scripts ou des routes existantes sans modifier l'API.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import List

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.models import (
    Province,
    Territoire,
    Collectivite,
    Groupement,
    Village,
    ImportHistory,
)


# Recherche par nom (recherche approximative, sensible à la casse DB)
def search_provinces_by_name(session: Session, name: str, limit: int = 50) -> List[Province]:
    pattern = f"%{name}%"
    stmt = select(Province).where(Province.nom.ilike(pattern)).limit(limit)
    return session.execute(stmt).scalars().all()


def search_territoires_by_name(session: Session, name: str, province_code: str | None = None, limit: int = 50) -> List[Territoire]:
    pattern = f"%{name}%"
    stmt = select(Territoire).where(Territoire.nom.ilike(pattern))
    if province_code:
        stmt = stmt.join(Province).where(Province.code == province_code.upper())
    stmt = stmt.limit(limit)
    return session.execute(stmt).scalars().all()


def search_collectivites_by_name(session: Session, name: str, territoire_code: str | None = None, limit: int = 50) -> List[Collectivite]:
    pattern = f"%{name}%"
    stmt = select(Collectivite).where(Collectivite.nom.ilike(pattern))
    if territoire_code:
        stmt = stmt.join(Territoire).where(Territoire.code == territoire_code.upper())
    stmt = stmt.limit(limit)
    return session.execute(stmt).scalars().all()


def search_groupements_by_name(session: Session, name: str, collectivite_code: str | None = None, limit: int = 50) -> List[Groupement]:
    pattern = f"%{name}%"
    stmt = select(Groupement).where(Groupement.nom.ilike(pattern))
    if collectivite_code:
        stmt = stmt.join(Collectivite).where(Collectivite.code == collectivite_code.upper())
    stmt = stmt.limit(limit)
    return session.execute(stmt).scalars().all()


def search_villages_by_name(session: Session, name: str, groupement_code: str | None = None, limit: int = 50) -> List[Village]:
    pattern = f"%{name}%"
    stmt = select(Village).where(Village.nom.ilike(pattern))
    if groupement_code:
        stmt = stmt.join(Groupement).where(Groupement.code == groupement_code.upper())
    stmt = stmt.limit(limit)
    return session.execute(stmt).scalars().all()


# Recherche par code (recherche exacte)
def get_province_by_code(session: Session, code: str) -> Province | None:
    return session.scalar(select(Province).where(Province.code == code.upper()))


def get_territoire_by_code(session: Session, code: str, province_code: str | None = None) -> Territoire | None:
    stmt = select(Territoire).where(Territoire.code == code)
    if province_code:
        stmt = stmt.join(Province).where(Province.code == province_code.upper())
    return session.scalar(stmt)


def get_collectivite_by_code(session: Session, code: str, territoire_code: str | None = None) -> Collectivite | None:
    stmt = select(Collectivite).where(Collectivite.code == code)
    if territoire_code:
        stmt = stmt.join(Territoire).where(Territoire.code == territoire_code.upper())
    return session.scalar(stmt)


def get_groupement_by_code(session: Session, code: str, collectivite_code: str | None = None) -> Groupement | None:
    stmt = select(Groupement).where(Groupement.code == code)
    if collectivite_code:
        stmt = stmt.join(Collectivite).where(Collectivite.code == collectivite_code.upper())
    return session.scalar(stmt)


def get_village_by_code(session: Session, code: str, groupement_code: str | None = None) -> Village | None:
    stmt = select(Village).where(Village.code == code)
    if groupement_code:
        stmt = stmt.join(Groupement).where(Groupement.code == groupement_code.upper())
    return session.scalar(stmt)


# Recherches hiérarchiques (enfants)
def territoires_by_province_code(session: Session, province_code: str) -> List[Territoire]:
    stmt = select(Territoire).join(Province).where(Province.code == province_code.upper()).order_by(Territoire.nom)
    return session.execute(stmt).scalars().all()


def collectivites_by_territoire_code(session: Session, territoire_code: str) -> List[Collectivite]:
    stmt = select(Collectivite).join(Territoire).where(Territoire.code == territoire_code.upper()).order_by(Collectivite.nom)
    return session.execute(stmt).scalars().all()


def groupements_by_collectivite_code(session: Session, collectivite_code: str) -> List[Groupement]:
    stmt = select(Groupement).join(Collectivite).where(Collectivite.code == collectivite_code.upper()).order_by(Groupement.nom)
    return session.execute(stmt).scalars().all()


def villages_by_groupement_code(session: Session, groupement_code: str) -> List[Village]:
    stmt = select(Village).join(Groupement).where(Groupement.code == groupement_code.upper()).order_by(Village.nom)
    return session.execute(stmt).scalars().all()


# Récupérer la hiérarchie complète pour un village (par id)
def hierarchy_for_village(session: Session, village_id: int) -> dict:
    village = session.get(Village, village_id)
    if village is None:
        return {}
    groupement = village.groupement
    collectivite = groupement.collectivite if groupement is not None else None
    territoire = collectivite.territoire if collectivite is not None else None
    province = territoire.province if territoire is not None else None
    return {
        "province": province,
        "territoire": territoire,
        "collectivite": collectivite,
        "groupement": groupement,
        "village": village,
    }


# Statistiques et historique d'import
def recent_imports(session: Session, limit: int = 50) -> List[ImportHistory]:
    stmt = select(ImportHistory).order_by(ImportHistory.imported_at.desc()).limit(limit)
    return session.execute(stmt).scalars().all()


def import_aggregates(session: Session, days: int | None = None) -> dict:
    stmt = select(
        func.count(ImportHistory.id),
        func.sum(ImportHistory.rows_inserted),
        func.sum(ImportHistory.rows_updated),
        func.sum(ImportHistory.rows_rejected),
    )
    if days is not None:
        since = datetime.utcnow() - timedelta(days=days)
        stmt = stmt.where(ImportHistory.imported_at >= since)
    row = session.execute(stmt).one()
    return {
        "imports_count": int(row[0] or 0),
        "rows_inserted": int(row[1] or 0),
        "rows_updated": int(row[2] or 0),
        "rows_rejected": int(row[3] or 0),
    }
