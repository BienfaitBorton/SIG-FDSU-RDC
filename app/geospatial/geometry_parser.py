from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable
import xml.etree.ElementTree as ET

try:
    from shapely.geometry import shape
except Exception:  # pragma: no cover - optional dependency
    shape = None

from .kmz_reader import KML_NAMESPACE


@dataclass(slots=True)
class ParsedFeatureGeometry:
    geometry: Any
    geometry_type: str


class GeometryParser:
    """Extrait les géométries d'un document KML/KMZ."""

    def parse(self, kml_text: str) -> list[ParsedFeatureGeometry]:
        root = ET.fromstring(kml_text)
        geometries: list[ParsedFeatureGeometry] = []

        for placemark in root.findall(".//kml:Placemark", KML_NAMESPACE):
            geometry = self._parse_placemark_geometry(placemark)
            if geometry is not None:
                geometries.append(geometry)
        return geometries

    def _parse_placemark_geometry(self, placemark: ET.Element) -> ParsedFeatureGeometry | None:
        for tag in ("Point", "LineString", "Polygon", "MultiGeometry"):
            node = placemark.find(f"kml:{tag}", KML_NAMESPACE)
            if node is not None:
                parsed = self._parse_geometry_node(node)
                if parsed is not None:
                    return parsed
        return None

    def _parse_geometry_node(self, node: ET.Element) -> ParsedFeatureGeometry | None:
        if shape is None:
            return ParsedFeatureGeometry(geometry=self._extract_raw_coordinates(node), geometry_type=node.tag.split("}")[-1])

        geojson_like = self._to_geojson_like(node)
        if geojson_like is None:
            return None
        geometry = shape(geojson_like)
        return ParsedFeatureGeometry(geometry=geometry, geometry_type=geometry.geom_type)

    def _extract_raw_coordinates(self, node: ET.Element) -> dict[str, Any] | list[str] | None:
        coordinates = node.findtext(".//kml:coordinates", default="", namespaces=KML_NAMESPACE).strip()
        if not coordinates:
            return None
        return [coord.strip() for coord in coordinates.split() if coord.strip()]

    def _to_geojson_like(self, node: ET.Element) -> dict[str, Any] | None:
        tag = node.tag.split("}")[-1]
        coordinates = self._parse_coordinates(node.findtext(".//kml:coordinates", default="", namespaces=KML_NAMESPACE))
        if not coordinates:
            return None

        if tag == "Point":
            lon, lat, *rest = coordinates[0]
            return {"type": "Point", "coordinates": (lon, lat) if not rest else (lon, lat, rest[0])}

        if tag == "LineString":
            return {"type": "LineString", "coordinates": [(coord[0], coord[1]) for coord in coordinates]}

        if tag == "Polygon":
            return {"type": "Polygon", "coordinates": [[(coord[0], coord[1]) for coord in coordinates]]}

        if tag == "MultiGeometry":
            geometries = []
            for child in node:
                child_parsed = self._to_geojson_like(child)
                if child_parsed is not None:
                    geometries.append(child_parsed)
            if geometries:
                return {"type": "GeometryCollection", "geometries": geometries}
        return None

    def _parse_coordinates(self, coordinates_text: str) -> list[tuple[float, float, float | None]]:
        coordinates: list[tuple[float, float, float | None]] = []
        for chunk in coordinates_text.replace("\n", " ").split():
            parts = [part for part in chunk.split(",") if part]
            if len(parts) >= 2:
                lon = float(parts[0])
                lat = float(parts[1])
                alt = float(parts[2]) if len(parts) > 2 else None
                coordinates.append((lon, lat, alt))
        return coordinates
