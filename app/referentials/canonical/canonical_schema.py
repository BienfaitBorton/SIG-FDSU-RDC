from __future__ import annotations

from enum import Enum


class CanonicalLevel(str, Enum):
    """Administrative levels normalized for the national SIG-FDSU model."""

    COUNTRY = "country"
    PROVINCE = "province"
    VILLE = "ville"
    TERRITOIRE = "territoire"
    COMMUNE = "commune"
    SECTEUR = "secteur"
    CHEFFERIE = "chefferie"
    GROUPEMENT = "groupement"
    QUARTIER = "quartier"
    VILLAGE = "village"
    LOCALITE = "localite"
    UNKNOWN = "unknown"


class SourceKey(str, Enum):
    """Known source keys supported by the canonical layer."""

    HDX = "hdx"
    CENI = "ceni"
    CAID = "caid"
    KMZ = "kmz"
    EXCEL_FDSU = "excel_fdsu"
    CUSTOM = "custom"


class CanonicalStatus(str, Enum):
    """Lifecycle state of a canonical entity."""

    DRAFT = "draft"
    VALIDATED = "validated"
    PUBLISHED = "published"
    ARCHIVED = "archived"


DEFAULT_COUNTRY_CODE = "COD"


LEVEL_ORDER: dict[CanonicalLevel, int] = {
    CanonicalLevel.COUNTRY: 0,
    CanonicalLevel.PROVINCE: 1,
    CanonicalLevel.VILLE: 2,
    CanonicalLevel.TERRITOIRE: 2,
    CanonicalLevel.COMMUNE: 3,
    CanonicalLevel.SECTEUR: 3,
    CanonicalLevel.CHEFFERIE: 3,
    CanonicalLevel.GROUPEMENT: 4,
    CanonicalLevel.QUARTIER: 4,
    CanonicalLevel.VILLAGE: 5,
    CanonicalLevel.LOCALITE: 6,
    CanonicalLevel.UNKNOWN: 99,
}


def parse_level(value: str | CanonicalLevel | None) -> CanonicalLevel:
    if isinstance(value, CanonicalLevel):
        return value
    if not value:
        return CanonicalLevel.UNKNOWN
    normalized = str(value).strip().lower()
    aliases = {
        "adm0": CanonicalLevel.COUNTRY,
        "adm1": CanonicalLevel.PROVINCE,
        "adm2": CanonicalLevel.TERRITOIRE,
        "adm3": CanonicalLevel.GROUPEMENT,
        "adm4": CanonicalLevel.VILLAGE,
        "city": CanonicalLevel.VILLE,
    }
    if normalized in aliases:
        return aliases[normalized]
    for level in CanonicalLevel:
        if level.value == normalized:
            return level
    return CanonicalLevel.UNKNOWN
