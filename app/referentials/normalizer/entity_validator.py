from __future__ import annotations

from collections import Counter, defaultdict

from .hierarchy import HierarchyResolver
from .normalizer import (
    NormalizationIssue,
    NormalizationIssueCode,
    NormalizationIssueLevel,
    StagingEntity,
)


class EntityValidator:
    """Detects structural and semantic issues on staging entities."""

    def __init__(self, hierarchy_resolver: HierarchyResolver) -> None:
        self.hierarchy_resolver = hierarchy_resolver

    def validate(
        self,
        entities: list[StagingEntity],
        reference_counts: dict[str, int],
    ) -> list[NormalizationIssue]:
        issues: list[NormalizationIssue] = []
        code_counter = Counter(entity.normalized_code for entity in entities if entity.normalized_code)
        name_counter = Counter((entity.entity_type, entity.normalized_name) for entity in entities if entity.normalized_name)
        by_id = {entity.source_id: entity for entity in entities}
        counts_by_type = defaultdict(int)

        for entity in entities:
            if not entity.normalized_name:
                issues.append(self._issue(NormalizationIssueCode.EMPTY_NAME, "Entity name is empty.", entity.source_id))
            if not entity.normalized_code:
                issues.append(self._issue(NormalizationIssueCode.MISSING_CODE, "Entity code is missing.", entity.source_id))
            if entity.normalized_code and code_counter[entity.normalized_code] > 1:
                issues.append(self._issue(NormalizationIssueCode.DUPLICATE_CODE, "Entity code is duplicated.", entity.source_id))
            if entity.normalized_name and name_counter[(entity.entity_type, entity.normalized_name)] > 1:
                issues.append(self._issue(NormalizationIssueCode.DUPLICATE_NAME, "Entity name is duplicated at the same level.", entity.source_id))
            if entity.geometry is not None and not self._is_valid_geometry(entity):
                issues.append(self._issue(NormalizationIssueCode.INVALID_GEOMETRY, "Geometry payload is invalid.", entity.source_id))

            allowed_parents = self.hierarchy_resolver.allowed_parents(entity.entity_type)
            if allowed_parents:
                if not entity.parent_source_id:
                    issues.append(self._issue(NormalizationIssueCode.MISSING_PARENT, "Expected parent entity is missing.", entity.source_id))
                    issues.append(self._issue(NormalizationIssueCode.ORPHAN_ENTITY, "Entity is orphaned.", entity.source_id))
                else:
                    parent = by_id.get(entity.parent_source_id)
                    if parent is None:
                        issues.append(self._issue(NormalizationIssueCode.MISSING_PARENT, "Parent reference does not resolve.", entity.source_id))
                    elif parent.entity_type not in allowed_parents:
                        issues.append(self._issue(NormalizationIssueCode.INVALID_HIERARCHY, "Parent level is not allowed for entity.", entity.source_id))

            if entity.entity_type:
                counts_by_type[entity.entity_type] += 1

        for level_name, expected_count in reference_counts.items():
            actual_count = counts_by_type.get(level_name, 0)
            if actual_count != expected_count:
                issues.append(
                    NormalizationIssue(
                        level=NormalizationIssueLevel.WARNING,
                        code=NormalizationIssueCode.REFERENCE_COUNT_GAP,
                        message=f"Reference count mismatch for {level_name}: expected {expected_count}, got {actual_count}.",
                        context={"level_name": level_name, "expected": expected_count, "actual": actual_count},
                    )
                )

        return issues

    def _issue(self, code: NormalizationIssueCode, message: str, entity_id: str) -> NormalizationIssue:
        return NormalizationIssue(
            level=NormalizationIssueLevel.ERROR,
            code=code,
            message=message,
            entity_id=entity_id,
        )

    def _is_valid_geometry(self, entity: StagingEntity) -> bool:
        if not entity.geometry_type:
            return False
        if not isinstance(entity.geometry, dict):
            return False
        coordinates = entity.geometry.get("coordinates")
        return coordinates is not None
