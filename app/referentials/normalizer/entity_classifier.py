from __future__ import annotations

from enum import Enum

from .normalizer import StagingEntity


class AdministrativeEntityType(str, Enum):
    ZONE_FDSU = "zone_fdsu"
    PROVINCE = "province"
    VILLE = "ville"
    TERRITOIRE = "territoire"
    COMMUNE_URBAINE = "commune_urbaine"
    COMMUNE_RURALE = "commune_rurale"
    SECTEUR = "secteur"
    CHEFFERIE = "chefferie"
    GROUPEMENT = "groupement"
    GROUPEMENT_INCORPORE = "groupement_incorpore"
    QUARTIER = "quartier"
    VILLAGE = "village"
    UNKNOWN = "unknown"


class EntityClassifier:
    """Heuristic classifier based on attributes, names, hierarchy, geometry, and metadata."""

    NAME_HINTS: dict[AdministrativeEntityType, tuple[str, ...]] = {
        AdministrativeEntityType.ZONE_FDSU: ("ZONE ", "ZONE FDSU", " ND", " SD", " CE", " OT", " ET"),
        AdministrativeEntityType.PROVINCE: ("PROVINCE",),
        AdministrativeEntityType.VILLE: ("VILLE", "CITY"),
        AdministrativeEntityType.TERRITOIRE: ("TERRITOIRE", "TERRITORY"),
        AdministrativeEntityType.COMMUNE_URBAINE: ("COMMUNE URBAINE",),
        AdministrativeEntityType.COMMUNE_RURALE: ("COMMUNE RURALE",),
        AdministrativeEntityType.SECTEUR: ("SECTEUR",),
        AdministrativeEntityType.CHEFFERIE: ("CHEFFERIE",),
        AdministrativeEntityType.GROUPEMENT: ("GROUPEMENT",),
        AdministrativeEntityType.GROUPEMENT_INCORPORE: ("GROUPEMENT INCORPORE",),
        AdministrativeEntityType.QUARTIER: ("QUARTIER",),
        AdministrativeEntityType.VILLAGE: ("VILLAGE",),
    }

    def classify(self, entity: StagingEntity) -> AdministrativeEntityType:
        candidates = self._collect_candidates(entity)

        explicit_type = self._match_explicit_type(candidates)
        if explicit_type is not None:
            return explicit_type

        if entity.zone_code:
            return AdministrativeEntityType.ZONE_FDSU
        if entity.territoire_name and not entity.province_name:
            return AdministrativeEntityType.TERRITOIRE
        if entity.province_name and entity.geometry_type == "Polygon" and not entity.territoire_name:
            return AdministrativeEntityType.PROVINCE
        if entity.geometry_type == "Point":
            return AdministrativeEntityType.VILLAGE
        return AdministrativeEntityType.UNKNOWN

    def _collect_candidates(self, entity: StagingEntity) -> list[str]:
        values = [
            entity.normalized_name,
            entity.attributes.get("type", ""),
            entity.attributes.get("TYPE", ""),
            entity.metadata.get("level", ""),
            entity.metadata.get("admin_level", ""),
        ]
        return [str(value).upper() for value in values if value]

    def _match_explicit_type(self, candidates: list[str]) -> AdministrativeEntityType | None:
        for entity_type, hints in self.NAME_HINTS.items():
            for candidate in candidates:
                if any(hint in candidate for hint in hints):
                    return entity_type
        return None
