from __future__ import annotations

from pathlib import Path
from typing import Iterable

from .base import Importer, Exporter
from .exceptions import DependencyMissing, ValidationError
from .utils import iter_with_progress, ensure_parent_dir

try:
    from fastkml import kml
    from shapely.geometry import shape, mapping
except Exception:  # pragma: no cover - optional dependency
    kml = None
    shape = None
    mapping = None


class KMLHandler(Importer, Exporter):
    """Handler KML/KMZ. Dépend de `fastkml` et `shapely`.
    Si non présent, lève `DependencyMissing`.
    """

    def _require_deps(self):
        if kml is None or shape is None:
            raise DependencyMissing("fastkml et shapely sont requis pour KML/KMZ")

    def import_data(self, path: Path, **kwargs) -> Iterable[dict]:
        self._require_deps()
        # lecture basique: renvoie les placemarks properties + geometry
        with path.open("rb") as handle:
            doc = handle.read()
        k = kml.KML()
        k.from_string(doc)
        features = []
        for feature in k.features():
            for placemark in feature.features():
                geom = placemark.geometry
                props = dict(placemark.extended_data or {})
                props["geometry"] = shape(geom.geojson)
                features.append(props)
        for feat in iter_with_progress(features, desc=f"Import KML {path.name}", disable=not self.progress):
            valid, errors = self.validate(feat)
            if not valid:
                raise ValidationError(errors)
            yield feat

    def export_data(self, path: Path, records: Iterable[dict], **kwargs) -> None:
        self._require_deps()
        ensure_parent_dir(path)
        k = kml.KML()
        doc = kml.Document()
        k.append(doc)
        for rec in iter_with_progress(records, desc=f"Export KML {path.name}", disable=not self.progress):
            geom = rec.get("geometry")
            props = {k: v for k, v in rec.items() if k != "geometry"}
            placemark = kml.Placemark(name=props.get("nom") or "", description=str(props), geometry=geom)
            doc.append(placemark)
        path.write_bytes(k.to_string().encode("utf-8"))

    def validate(self, record: dict) -> tuple[bool, list[str]]:
        return True, []
