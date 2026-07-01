from __future__ import annotations

from pathlib import Path
from typing import Iterable

from .base import Importer, Exporter
from .exceptions import DependencyMissing, ValidationError
from .utils import iter_with_progress, ensure_parent_dir

try:
    import fiona
    from shapely.geometry import shape, mapping
except Exception:  # pragma: no cover
    fiona = None
    shape = None
    mapping = None


class ShapefileHandler(Importer, Exporter):
    """Handler pour Shapefile (.shp) en lecture/écriture via Fiona/Shapely.
    Utilise des schémas simples: properties -> dict, geometry -> shapely geometry.
    """

    def _require_deps(self):
        if fiona is None:
            raise DependencyMissing("fiona et shapely sont requis pour Shapefile")

    def import_data(self, path: Path, **kwargs) -> Iterable[dict]:
        self._require_deps()
        features = []
        with fiona.open(str(path), "r") as src:
            for feat in src:
                props = feat.get("properties", {})
                geom = feat.get("geometry")
                props["geometry"] = shape(geom) if geom is not None else None
                features.append(props)
        for rec in iter_with_progress(features, desc=f"Import Shapefile {path.name}", disable=not self.progress):
            valid, errors = self.validate(rec)
            if not valid:
                raise ValidationError(errors)
            yield rec

    def export_data(self, path: Path, records: Iterable[dict], schema: dict | None = None, crs: dict | None = None, **kwargs) -> None:
        self._require_deps()
        ensure_parent_dir(path)
        # records should be iterable of dicts with 'geometry' as shapely geometry
        # if schema is None, attempt to build minimal schema from first record
        with fiona.open(str(path), "w", driver="ESRI Shapefile", schema=schema or {}, crs=crs or {}) as dst:
            for rec in iter_with_progress(records, desc=f"Export Shapefile {path.name}", disable=not self.progress):
                geom = rec.get("geometry")
                props = {k: v for k, v in rec.items() if k != "geometry"}
                dst.write({"geometry": mapping(geom) if geom is not None else None, "properties": props})

    def validate(self, record: dict) -> tuple[bool, list[str]]:
        return True, []
