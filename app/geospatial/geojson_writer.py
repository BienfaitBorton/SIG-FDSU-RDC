from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
import json
from copy import deepcopy

try:
    from shapely.geometry import mapping
except Exception:  # pragma: no cover - optional dependency
    mapping = None


@dataclass(slots=True)
class GeoJSONWriter:
    """Produit un GeoJSON enrichi sans modifier la source KMZ originale."""

    indent: int = 2
    ensure_ascii: bool = False
    extra_collection_properties: dict[str, Any] = field(default_factory=dict)

    def write(self, path: str | Path, features: list[dict[str, Any]]) -> Path:
        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        collection = self.build_collection(features)
        output_path.write_text(json.dumps(collection, ensure_ascii=self.ensure_ascii, indent=self.indent), encoding="utf-8")
        return output_path

    def build_collection(self, features: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "type": "FeatureCollection",
            "properties": dict(self.extra_collection_properties),
            "features": [self._build_feature(feature) for feature in features],
        }

    def _build_feature(self, feature: dict[str, Any]) -> dict[str, Any]:
        payload = deepcopy(feature)
        geometry = payload.pop("geometry", None)
        if mapping is not None and geometry is not None and hasattr(geometry, "geom_type"):
            geometry = mapping(geometry)
        return {
            "type": "Feature",
            "properties": payload,
            "geometry": geometry,
        }
