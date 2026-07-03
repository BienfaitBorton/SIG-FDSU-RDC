from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class FeatureRecord:
    folder: str
    geometry_type: str
    properties: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class FieldDictionaryEntry:
    name: str
    value_type: str
    value_count: int
    unique_count: int
    null_count: int
    example: str
    unique_values_preview: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "type": self.value_type,
            "value_count": self.value_count,
            "unique_count": self.unique_count,
            "null_count": self.null_count,
            "example": self.example,
            "unique_values_preview": list(self.unique_values_preview),
        }


@dataclass(slots=True)
class FolderCatalogEntry:
    folder_name: str
    dataset_type: str
    object_count: int
    attributes: list[str]
    geometry_types: list[str]
    quality: float
    module_sig_conseille: str
    category: str
    tags: list[str]
    preview_values: dict[str, list[str]] = field(default_factory=dict)

    @property
    def field_count(self) -> int:
        return len(self.attributes)

    def to_dict(self) -> dict[str, Any]:
        return {
            "folder_name": self.folder_name,
            "type": self.dataset_type,
            "object_count": self.object_count,
            "field_count": self.field_count,
            "attributes": list(self.attributes),
            "geometry_types": list(self.geometry_types),
            "quality": self.quality,
            "module_sig_conseille": self.module_sig_conseille,
            "category": self.category,
            "tags": list(self.tags),
            "preview_values": dict(self.preview_values),
        }


@dataclass(slots=True)
class SourceCatalogReport:
    source_file: str
    source_format: str
    generated_at: datetime
    object_count: int
    field_count: int
    folders: list[FolderCatalogEntry] = field(default_factory=list)
    data_dictionary: list[FieldDictionaryEntry] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_file": self.source_file,
            "source_format": self.source_format,
            "generated_at": self.generated_at.isoformat(timespec="seconds"),
            "object_count": self.object_count,
            "field_count": self.field_count,
            "folders": [folder.to_dict() for folder in self.folders],
            "data_dictionary": [entry.to_dict() for entry in self.data_dictionary],
            "warnings": list(self.warnings),
        }


@dataclass(slots=True)
class SourceExplorerRunResult:
    source_path: Path
    report: SourceCatalogReport
    report_json_path: Path
    report_markdown_path: Path
