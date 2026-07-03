from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

from app.geospatial.description_parser import DescriptionParser
from app.geospatial.kmz_reader import KML_NAMESPACE, KMZReader

from .models import ProvinceSourceRecord


class ProvinceSourceReadError(RuntimeError):
    pass


class ProvinceKMZReader:
    def __init__(self) -> None:
        self.kmz_reader = KMZReader()
        self.description_parser = DescriptionParser()

    def read(self, source_path: str | Path) -> list[ProvinceSourceRecord]:
        source = Path(source_path)
        if source.suffix.lower() != ".kmz":
            raise ProvinceSourceReadError("Le référentiel Province officiel doit provenir d'un fichier KMZ.")

        document = self.kmz_reader.read(source)
        root = ET.fromstring(document.kml_text)
        parent_map = {child: parent for parent in root.iter() for child in parent}

        styles = self._collect_styles(root)
        records: list[ProvinceSourceRecord] = []

        for placemark in root.findall(".//kml:Placemark", KML_NAMESPACE):
            record = self._placemark_to_record(placemark, styles, parent_map, source)
            if record is not None:
                records.append(record)

        return records

    def _placemark_to_record(
        self,
        placemark: ET.Element,
        styles: dict[str, dict[str, str]],
        parent_map: dict[ET.Element, ET.Element],
        source: Path,
    ) -> ProvinceSourceRecord | None:
        name = (placemark.findtext("kml:name", default="", namespaces=KML_NAMESPACE) or "").strip()
        if not name:
            return None

        description_html = (placemark.findtext("kml:description", default="", namespaces=KML_NAMESPACE) or "").strip()
        description_values = self.description_parser.parse(description_html)
        extended_data = self._extract_extended_data(placemark)
        geometry_type, geometry = self._extract_geometry(placemark)

        style_url = (placemark.findtext("kml:styleUrl", default="", namespaces=KML_NAMESPACE) or "").strip() or None
        style_inline = self._extract_inline_style(placemark)
        style_ref = style_url[1:] if style_url and style_url.startswith("#") else style_url
        resolved_style = styles.get(style_ref or "", {})

        folder = self._resolve_folder(placemark, parent_map)
        metadata = {
            "style_reference": style_url,
            "resolved_style": resolved_style,
            "folder": folder,
            "style_inline": style_inline,
            "source_file": source.name,
        }

        return ProvinceSourceRecord(
            name=name,
            folder=folder,
            description=description_html,
            description_values=description_values,
            extended_data=extended_data,
            geometry_type=geometry_type,
            geometry=geometry,
            style_url=style_url,
            style_inline=style_inline,
            metadata=metadata,
        )

    def _extract_extended_data(self, placemark: ET.Element) -> dict[str, str]:
        data: dict[str, str] = {}

        for item in placemark.findall(".//kml:Data", KML_NAMESPACE):
            key = item.attrib.get("name")
            value = (item.findtext("kml:value", default="", namespaces=KML_NAMESPACE) or "").strip()
            if key:
                data[key] = value

        for item in placemark.findall(".//kml:SimpleData", KML_NAMESPACE):
            key = item.attrib.get("name")
            value = (item.text or "").strip()
            if key:
                data[key] = value

        return data

    def _extract_geometry(self, placemark: ET.Element) -> tuple[str | None, dict[str, object] | None]:
        polygon = placemark.find("kml:Polygon", KML_NAMESPACE)
        if polygon is not None:
            coords = self._extract_coordinates(polygon)
            return "Polygon", {"type": "Polygon", "coordinates": [coords]} if coords else {"type": "Polygon", "coordinates": []}

        multi = placemark.find("kml:MultiGeometry", KML_NAMESPACE)
        if multi is not None:
            polygons: list[list[tuple[float, float, float | None]]] = []
            for node in multi.findall("kml:Polygon", KML_NAMESPACE):
                coords = self._extract_coordinates(node)
                polygons.append(coords)
            return "MultiGeometry", {"type": "MultiPolygon", "coordinates": [[polygon] for polygon in polygons]}

        point = placemark.find("kml:Point", KML_NAMESPACE)
        if point is not None:
            coords = self._extract_coordinates(point)
            if coords:
                lon, lat, alt = coords[0]
                base = [lon, lat]
                if alt is not None:
                    base.append(alt)
                return "Point", {"type": "Point", "coordinates": base}
            return "Point", {"type": "Point", "coordinates": []}

        line = placemark.find("kml:LineString", KML_NAMESPACE)
        if line is not None:
            coords = self._extract_coordinates(line)
            return "LineString", {"type": "LineString", "coordinates": [[lon, lat] for lon, lat, _ in coords]}

        return None, None

    def _extract_coordinates(self, node: ET.Element) -> list[tuple[float, float, float | None]]:
        text = (node.findtext(".//kml:coordinates", default="", namespaces=KML_NAMESPACE) or "").strip()
        if not text:
            return []

        coords: list[tuple[float, float, float | None]] = []
        for chunk in text.replace("\n", " ").split():
            parts = [part for part in chunk.split(",") if part]
            if len(parts) >= 2:
                lon = float(parts[0])
                lat = float(parts[1])
                alt = float(parts[2]) if len(parts) > 2 else None
                coords.append((lon, lat, alt))
        return coords

    def _extract_inline_style(self, placemark: ET.Element) -> dict[str, str]:
        inline: dict[str, str] = {}
        style = placemark.find("kml:Style", KML_NAMESPACE)
        if style is None:
            return inline

        for child in list(style):
            tag = child.tag.split("}")[-1]
            for sub in list(child):
                key = f"{tag}.{sub.tag.split('}')[-1]}"
                inline[key] = (sub.text or "").strip()

        return inline

    def _collect_styles(self, root: ET.Element) -> dict[str, dict[str, str]]:
        styles: dict[str, dict[str, str]] = {}
        for style in root.findall(".//kml:Style", KML_NAMESPACE):
            style_id = style.attrib.get("id")
            if not style_id:
                continue
            attrs: dict[str, str] = {}
            for child in list(style):
                tag = child.tag.split("}")[-1]
                for sub in list(child):
                    key = f"{tag}.{sub.tag.split('}')[-1]}"
                    attrs[key] = (sub.text or "").strip()
            styles[style_id] = attrs
        return styles

    def _resolve_folder(self, placemark: ET.Element, parent_map: dict[ET.Element, ET.Element]) -> str:
        current: ET.Element | None = placemark
        while current is not None:
            parent = parent_map.get(current)
            if parent is None:
                break
            tag = parent.tag.split("}")[-1]
            if tag in {"Folder", "Document"}:
                name = (parent.findtext("kml:name", default="", namespaces=KML_NAMESPACE) or "").strip()
                if name:
                    return name
            current = parent
        return "Racine"
