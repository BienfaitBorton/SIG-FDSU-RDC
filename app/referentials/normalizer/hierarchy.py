from __future__ import annotations

from .entity_classifier import AdministrativeEntityType
from .normalizer import StagingEntity


ALLOWED_PARENTS: dict[str, tuple[str, ...]] = {
    AdministrativeEntityType.PROVINCE.value: (AdministrativeEntityType.ZONE_FDSU.value,),
    AdministrativeEntityType.TERRITOIRE.value: (AdministrativeEntityType.PROVINCE.value,),
    AdministrativeEntityType.SECTEUR.value: (AdministrativeEntityType.TERRITOIRE.value,),
    AdministrativeEntityType.CHEFFERIE.value: (AdministrativeEntityType.TERRITOIRE.value,),
    AdministrativeEntityType.GROUPEMENT.value: (
        AdministrativeEntityType.SECTEUR.value,
        AdministrativeEntityType.CHEFFERIE.value,
    ),
    AdministrativeEntityType.GROUPEMENT_INCORPORE.value: (
        AdministrativeEntityType.SECTEUR.value,
        AdministrativeEntityType.CHEFFERIE.value,
    ),
    AdministrativeEntityType.VILLAGE.value: (
        AdministrativeEntityType.GROUPEMENT.value,
        AdministrativeEntityType.GROUPEMENT_INCORPORE.value,
    ),
    AdministrativeEntityType.VILLE.value: (AdministrativeEntityType.PROVINCE.value,),
    AdministrativeEntityType.COMMUNE_URBAINE.value: (AdministrativeEntityType.VILLE.value,),
    AdministrativeEntityType.COMMUNE_RURALE.value: (AdministrativeEntityType.TERRITOIRE.value,),
    AdministrativeEntityType.QUARTIER.value: (AdministrativeEntityType.COMMUNE_URBAINE.value,),
}


class HierarchyResolver:
    """Builds parent relationships in staging without mutating source data."""

    def build_hierarchy(self, entities: list[StagingEntity]) -> None:
        by_code = {entity.normalized_code: entity for entity in entities if entity.normalized_code}

        for entity in entities:
            if entity.parent_code and entity.parent_code in by_code:
                entity.parent_source_id = by_code[entity.parent_code].source_id
                continue

            parent = self._find_parent(entity, entities)
            if parent is not None:
                entity.parent_source_id = parent.source_id
                entity.parent_code = parent.normalized_code

    def allowed_parents(self, entity_type: str | None) -> tuple[str, ...]:
        if not entity_type:
            return ()
        return ALLOWED_PARENTS.get(entity_type, ())

    def _find_parent(self, entity: StagingEntity, entities: list[StagingEntity]) -> StagingEntity | None:
        allowed = set(self.allowed_parents(entity.entity_type))
        if not allowed:
            return None

        for candidate in entities:
            if candidate.source_id == entity.source_id:
                continue
            if candidate.entity_type not in allowed:
                continue
            if entity.province_name and candidate.normalized_name == entity.province_name.upper():
                return candidate
            if entity.territoire_name and candidate.normalized_name == entity.territoire_name.upper():
                return candidate
        return None
