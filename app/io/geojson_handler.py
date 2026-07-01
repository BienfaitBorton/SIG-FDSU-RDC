from __future__ import annotations

from pathlib import Path
from typing import Iterable

import json
from shapely.geometry import shape, mapping

from .base import Importer, Exporter
from .exceptions import ValidationError, DependencyMissing
from .utils import iter_with_progress, ensure_parent_dir


class GeoJSONHandler(Importer, Exporter):
    """Handler pour GeoJSON. Utilise shapely pour géométries.

    Le handler renvoie/consomme des dicts GeoJSON Feature/FeatureCollection.
    """

    def import_data(self, path: Path, **kwargs) -> Iterable[dict]:
        data = json.loads(path.read_text(encoding="utf-8"))
        features = data.get("features") if isinstance(data, dict) else []
        for feat in iter_with_progress(features, desc=f"Import GeoJSON {path.name}", disable=not self.progress):
            props = feat.get("properties", {})
            geom = feat.get("geometry")
            if geom is not None:
                try:
                    props["geometry"] = shape(geom)
                except Exception as exc:
                    raise ValidationError(f"Géométrie invalide: {exc}")
            valid, errors = self.validate(props)
            if not valid:
                raise ValidationError(errors)
            yield props

    def export_data(self, path: Path, records: Iterable[dict], **kwargs) -> None:
        ensure_parent_dir(path)
        features = []
        for rec in iter_with_progress(records, desc=f"Export GeoJSON {path.name}", disable=not self.progress):
            rec_copy = dict(rec)
            geom = rec_copy.pop("geometry", None)
            features.append({
                "type": "Feature",
                "properties": rec_copy,
                "geometry": mapping(geom) if geom is not None else None,
            })
        collection = {"type": "FeatureCollection", "features": features}
        path.write_text(json.dumps(collection, ensure_ascii=False, indent=2), encoding="utf-8")

    def validate(self, record: dict) -> tuple[bool, list[str]]:
        return True, []
