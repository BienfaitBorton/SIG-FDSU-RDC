from __future__ import annotations

from collections import Counter, defaultdict

from .normalizer import NormalizationIssue, NormalizationIssueLevel, StagingEntity


class EntityStatisticsService:
    """Computes counts and quality indicators from staging entities and issues."""

    def compute(
        self,
        entities: list[StagingEntity],
        issues: list[NormalizationIssue],
    ) -> dict[str, object]:
        by_level = Counter(entity.entity_type for entity in entities if entity.entity_type)
        by_province = Counter(entity.province_name for entity in entities if entity.province_name)
        by_territoire = Counter(entity.territoire_name for entity in entities if entity.territoire_name)

        error_count = sum(1 for issue in issues if issue.level == NormalizationIssueLevel.ERROR)
        completeness_fields = 0
        completeness_total = 0
        for entity in entities:
            for value in (entity.normalized_name, entity.normalized_code, entity.entity_type, entity.parent_source_id or entity.parent_code):
                completeness_total += 1
                if value:
                    completeness_fields += 1

        completeness_rate = (completeness_fields / completeness_total) if completeness_total else 1.0
        quality_score = max(0.0, round((completeness_rate * 100.0) - min(error_count, 100), 2))

        return {
            "by_level": dict(by_level),
            "by_province": {key: value for key, value in by_province.items() if key},
            "by_territoire": {key: value for key, value in by_territoire.items() if key},
            "quality": {
                "completeness_rate": round(completeness_rate, 4),
                "error_rate": round((error_count / len(entities)), 4) if entities else 0.0,
                "quality_score": quality_score,
            },
        }
