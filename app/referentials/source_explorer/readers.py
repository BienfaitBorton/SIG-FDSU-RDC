from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from pathlib import Path
from zipfile import ZipFile

from app.geospatial.description_parser import DescriptionParser
from app.geospatial.kmz_reader import KML_NAMESPACE, KMZReader

from .models import FeatureRecord


class SourceReadError(RuntimeError):
    pass


class SourceReader:
    """Read-only source reader for KMZ/KML/GeoJSON/Shapefile."""

    def __init__(self) -> None:
        self.kmz_reader = KMZReader()
        self.description_parser = DescriptionParser()

    def read(self, source_path: str | Path) -> tuple[str, list[FeatureRecord], list[str]]:
        path = Path(source_path)
        extension = path.suffix.lower()
        if extension == ".kmz":
            records = self._read_kmz(path)
            return "KMZ", records, []
        if extension == ".kml":
            records = self._read_kml(path.read_text(encoding="utf-8", errors="replace"), default_folder=path.stem)
            return "KML", records, []
        if extension in {".geojson", ".json"}:
            records = self._read_geojson(path)
            return "GeoJSON", records, []
        if extension == ".shp":
            records, warnings = self._read_shapefile(path)
            return "Shapefile", records, warnings
        if extension == ".gpkg":
            return "GeoPackage", [], ["Support GeoPackage prévu plus tard."]
        raise SourceReadError(f"Format non supporté: {path.suffix}")

    def _read_kmz(self, kmz_path: Path) -> list[FeatureRecord]:
        document = self.kmz_reader.read(kmz_path)
        return self._read_kml(document.kml_text, default_folder=document.document_name)

    def _read_kml(self, kml_text: str, default_folder: str) -> list[FeatureRecord]:
        root = ET.fromstring(kml_text)
        records: list[FeatureRecord] = []

        def walk(node: ET.Element, current_folder: str) -> None:
            tag = node.tag.split("}")[-1]
            folder_name = current_folder
            if tag in {"Folder", "Document"}:
                name = node.findtext("kml:name", default="", namespaces=KML_NAMESPACE).strip()
                if name:
                    folder_name = name

            if tag == "Placemark":
                records.append(self._placemark_to_record(node, folder_name or default_folder))
                return

            for child in list(node):
                walk(child, folder_name)

        walk(root, default_folder)
        return records

    def _placemark_to_record(self, placemark: ET.Element, folder_name: str) -> FeatureRecord:
        description_html = placemark.findtext("kml:description", default="", namespaces=KML_NAMESPACE)
        description_values = self.description_parser.parse(description_html)
        name = placemark.findtext("kml:name", default="", namespaces=KML_NAMESPACE).strip()

        properties = {
            "name": name,
            **self._extract_extended_data(placemark),
            **description_values,
        }

        geometry_type = self._detect_geometry_type(placemark)
        return FeatureRecord(folder=folder_name or "Racine", geometry_type=geometry_type, properties=properties)

    def _extract_extended_data(self, placemark: ET.Element) -> dict[str, str]:
        data: dict[str, str] = {}
        for data_node in placemark.findall(".//kml:Data", KML_NAMESPACE):
            key = data_node.attrib.get("name")
            value = data_node.findtext("kml:value", default="", namespaces=KML_NAMESPACE).strip()
            if key:
                data[key] = value
        for node in placemark.findall(".//kml:SimpleData", KML_NAMESPACE):
            key = node.attrib.get("name")
            value = (node.text or "").strip()
            if key:
                data[key] = value
        return data

    def _detect_geometry_type(self, placemark: ET.Element) -> str:
        if placemark.find("kml:Point", KML_NAMESPACE) is not None:
            return "Point"
        if placemark.find("kml:LineString", KML_NAMESPACE) is not None:
            return "Ligne"
        if placemark.find("kml:Polygon", KML_NAMESPACE) is not None:
            return "Polygone"
        if placemark.find("kml:MultiGeometry", KML_NAMESPACE) is not None:
            return "MultiPolygone"
        return "Inconnue"

    def _read_geojson(self, path: Path) -> list[FeatureRecord]:
        payload = json.loads(path.read_text(encoding="utf-8", errors="replace"))
        if payload.get("type") != "FeatureCollection":
            raise SourceReadError("Le GeoJSON doit être de type FeatureCollection.")

        records: list[FeatureRecord] = []
        for feature in payload.get("features", []):
            if not isinstance(feature, dict):
                continue
            properties = feature.get("properties") or {}
            geometry = feature.get("geometry") or {}
            geometry_type = self._geojson_geometry_label(str(geometry.get("type") or ""))
            folder_name = str(properties.get("folder") or properties.get("layer") or path.stem)
            records.append(
                FeatureRecord(
                    folder=folder_name,
                    geometry_type=geometry_type,
                    properties={key: value for key, value in properties.items()},
                )
            )
        return records

    def _geojson_geometry_label(self, geometry_type: str) -> str:
        normalized = geometry_type.lower()
        if normalized == "point" or normalized == "multipoint":
            return "Point"
        if normalized in {"linestring", "multilinestring"}:
            return "Ligne"
        if normalized == "polygon":
            return "Polygone"
        if normalized in {"multipolygon", "geometrycollection"}:
            return "MultiPolygone"
        return "Inconnue"

    def _read_shapefile(self, path: Path) -> tuple[list[FeatureRecord], list[str]]:
        warnings: list[str] = []
        try:
            import shapefile  # type: ignore
        except Exception:
            return [], [
                "Le support Shapefile nécessite la dépendance optionnelle 'pyshp' (module 'shapefile').",
            ]

        records: list[FeatureRecord] = []
        with shapefile.Reader(str(path)) as reader:
            fields = [field[0] for field in reader.fields if field[0] != "DeletionFlag"]
            for shape_record in reader.iterShapeRecords():
                props = dict(zip(fields, shape_record.record))
                geometry_type = self._shape_type_label(getattr(shape_record.shape, "shapeTypeName", ""))
                records.append(FeatureRecord(folder=path.stem, geometry_type=geometry_type, properties=props))

        warnings.append("Lecture Shapefile effectuée en mode attributaire (sans écriture base).")
        return records, warnings

    def _shape_type_label(self, shape_type_name: str) -> str:
        normalized = shape_type_name.lower()
        if "point" in normalized:
            return "Point"
        if "line" in normalized or "polyline" in normalized:
            return "Ligne"
        if "polygon" in normalized and "multi" not in normalized:
            return "Polygone"
        if "multi" in normalized or "multipatch" in normalized:
            return "MultiPolygone"
        return "Inconnue"
