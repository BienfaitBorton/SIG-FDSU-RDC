from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .models import FieldDictionaryEntry, FeatureRecord, FolderCatalogEntry, SourceCatalogReport
from .tagging import classify_category, compute_tags, suggest_module


class SourceAnalyzer:
    """Builds data catalog + dictionary from read-only source records."""

    def analyze(
        self,
        source_path: str | Path,
        source_format: str,
        records: list[FeatureRecord],
        warnings: list[str] | None = None,
    ) -> SourceCatalogReport:
        source = Path(source_path)
        warnings_list = list(warnings or [])
        by_folder: dict[str, list[FeatureRecord]] = defaultdict(list)
        for record in records:
            by_folder[record.folder or source.stem].append(record)

        folders = [self._build_folder_entry(folder_name, items) for folder_name, items in sorted(by_folder.items(), key=lambda item: item[0].lower())]
        dictionary = self._build_data_dictionary(records)

        return SourceCatalogReport(
            source_file=str(source),
            source_format=source_format,
            generated_at=datetime.now(timezone.utc),
            object_count=len(records),
            field_count=len(dictionary),
            folders=folders,
            data_dictionary=dictionary,
            warnings=warnings_list,
        )

    def _build_folder_entry(self, folder_name: str, records: list[FeatureRecord]) -> FolderCatalogEntry:
        attributes = sorted({key for record in records for key in record.properties.keys()}, key=str.lower)
        geometry_types = sorted({record.geometry_type for record in records if record.geometry_type})
        category = classify_category(folder_name, attributes)
        tags = compute_tags(folder_name, attributes, category)
        module = suggest_module(category)
        quality = self._compute_quality(records, attributes)
        preview_values = self._compute_preview_values(records, attributes)

        return FolderCatalogEntry(
            folder_name=folder_name,
            dataset_type=category,
            object_count=len(records),
            attributes=attributes,
            geometry_types=geometry_types,
            quality=quality,
            module_sig_conseille=module,
            category=category,
            tags=tags,
            preview_values=preview_values,
        )

    def _compute_quality(self, records: list[FeatureRecord], attributes: list[str]) -> float:
        if not records:
            return 0.0
        if not attributes:
            return 40.0

        filled = 0
        total = len(records) * len(attributes)
        for record in records:
            for attribute in attributes:
                value = record.properties.get(attribute)
                if value is not None and str(value).strip() != "":
                    filled += 1

        completeness = (filled / total) * 100 if total else 0.0
        geometry_bonus = 10.0 if any(record.geometry_type != "Inconnue" for record in records) else 0.0
        return round(min(100.0, completeness * 0.9 + geometry_bonus), 2)

    def _compute_preview_values(self, records: list[FeatureRecord], attributes: list[str]) -> dict[str, list[str]]:
        preview: dict[str, list[str]] = {}
        for attribute in attributes:
            values: list[str] = []
            for record in records:
                raw = record.properties.get(attribute)
                if raw is None or str(raw).strip() == "":
                    continue
                normalized = str(raw).strip()
                if normalized not in values:
                    values.append(normalized)
                if len(values) >= 3:
                    break
            preview[attribute] = values
        return preview

    def _build_data_dictionary(self, records: list[FeatureRecord]) -> list[FieldDictionaryEntry]:
        values_by_field: dict[str, list[Any]] = defaultdict(list)
        for record in records:
            for key, value in record.properties.items():
                values_by_field[key].append(value)

        entries: list[FieldDictionaryEntry] = []
        for field_name in sorted(values_by_field.keys(), key=str.lower):
            field_values = values_by_field[field_name]
            non_null_values = [value for value in field_values if value is not None and str(value).strip() != ""]
            null_count = len(field_values) - len(non_null_values)
            unique_counter = Counter(str(value).strip() for value in non_null_values)
            unique_values = list(unique_counter.keys())
            entries.append(
                FieldDictionaryEntry(
                    name=field_name,
                    value_type=self._infer_type(non_null_values),
                    value_count=len(field_values),
                    unique_count=len(unique_values),
                    null_count=null_count,
                    example=str(non_null_values[0]).strip() if non_null_values else "Non renseigné",
                    unique_values_preview=unique_values[:10],
                )
            )

        return entries

    def _infer_type(self, values: list[Any]) -> str:
        if not values:
            return "inconnu"

        if all(isinstance(value, bool) for value in values):
            return "bool"
        if all(isinstance(value, int) and not isinstance(value, bool) for value in values):
            return "int"
        if all(isinstance(value, (int, float)) and not isinstance(value, bool) for value in values):
            return "float"
        return "str"
