from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
import json


@dataclass(slots=True)
class GeospatialAnalysisReport:
    source_file: str
    kml_document: str | None = None
    feature_count: int = 0
    classified_counts: dict[str, int] = field(default_factory=dict)
    missing_geometries: int = 0
    parsed_descriptions: int = 0
    warnings: list[str] = field(default_factory=list)
    details: list[dict[str, Any]] = field(default_factory=list)

    def add_warning(self, message: str) -> None:
        self.warnings.append(message)

    def add_detail(self, detail: dict[str, Any]) -> None:
        self.details.append(detail)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_file": self.source_file,
            "kml_document": self.kml_document,
            "feature_count": self.feature_count,
            "classified_counts": dict(self.classified_counts),
            "missing_geometries": self.missing_geometries,
            "parsed_descriptions": self.parsed_descriptions,
            "warnings": list(self.warnings),
            "details": list(self.details),
        }

    def to_json(self, path: str | Path) -> Path:
        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(self.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
        return output_path
