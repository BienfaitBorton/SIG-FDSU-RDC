from __future__ import annotations

import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.geospatial.description_parser import DescriptionParser
from app.geospatial.kmz_reader import KML_NAMESPACE, KMZReader

from .models import TerritoryHierarchyReport, TerritoryHierarchyRunResult, TerritoryRecord
from .reporting import TerritoryHierarchyReportWriter


class TerritoryHierarchyService:
    """Builds territory referential strictly from KMZ folder hierarchy."""

    def __init__(self) -> None:
        self.reader = KMZReader()
        self.description_parser = DescriptionParser()
        self.writer = TerritoryHierarchyReportWriter()

    def run(
        self,
        kmz_path: str | Path,
        output_dir: str | Path = Path("data/reports/territory_hierarchy"),
    ) -> TerritoryHierarchyRunResult:
        source = Path(kmz_path)
        output = Path(output_dir)

        document = self.reader.read(source)
        root = ET.fromstring(document.kml_text)

        territories: list[TerritoryRecord] = []
        self._walk(node=root, path=[], territories=territories)

        territories.sort(key=lambda item: (item.zone_fdsu, item.province, item.nom))
        incoherence_count = sum(len(item.incoherences) for item in territories)

        report = TerritoryHierarchyReport(
            source_file=source.name,
            generated_at=datetime.now(timezone.utc),
            territory_count=len(territories),
            incoherence_count=incoherence_count,
            territories=territories,
        )

        report_json_path = output / "territoires_hierarchie_kmz.report.json"
        report_markdown_path = output / "territoires_hierarchie_kmz.report.md"
        self.writer.write_json(report, report_json_path)
        self.writer.write_markdown(report, report_markdown_path)

        return TerritoryHierarchyRunResult(
            source_path=source,
            report_json_path=report_json_path,
            report_markdown_path=report_markdown_path,
            report=report,
        )

    def _walk(self, node: ET.Element, path: list[str], territories: list[TerritoryRecord]) -> None:
        tag = node.tag.split("}")[-1]
        current_path = list(path)

        if tag in {"Document", "Folder"}:
            name = (node.findtext("kml:name", default="", namespaces=KML_NAMESPACE) or "").strip()
            if name:
                current_path.append(name)

        if tag == "Placemark":
            territory = self._placemark_to_territory(node, current_path)
            if territory is not None:
                territories.append(territory)
            return

        for child in list(node):
            self._walk(child, current_path, territories)

    def _placemark_to_territory(self, placemark: ET.Element, path: list[str]) -> TerritoryRecord | None:
        if not self._is_territory_path(path):
            return None

        territory_name = (placemark.findtext("kml:name", default="", namespaces=KML_NAMESPACE) or "").strip()
        if not territory_name:
            return None

        zone_name = self._extract_zone_from_path(path)
        province_name = self._extract_province_from_path(path)
        if not zone_name or not province_name:
            return None

        zone_code = self._zone_code_from_name(zone_name)
        geometry = self._extract_geometry(placemark)
        description_html = (placemark.findtext("kml:description", default="", namespaces=KML_NAMESPACE) or "").strip()
        description_values = self.description_parser.parse(description_html)
        extended_data = self._extract_extended_data(placemark)

        attributs = {
            "description": description_html,
            "description_values": description_values,
            "extended_data": extended_data,
        }

        full_path = ["RDC", self._normalize_zone_label(zone_name), province_name, territory_name]
        incoherences = self._check_inconsistencies(
            zone_name=zone_name,
            province_name=province_name,
            territory_name=territory_name,
            extended_data=extended_data,
            description_values=description_values,
        )

        score = self._compute_score(geometry=geometry, incoherences=incoherences, attributes=attributs)

        return TerritoryRecord(
            nom=territory_name,
            province=province_name,
            zone_fdsu=zone_code,
            chemin_hierarchique=full_path,
            geometry=geometry,
            attributs=attributs,
            score_qualite=score,
            incoherences=incoherences,
        )

    def _is_territory_path(self, path: list[str]) -> bool:
        if len(path) < 6:
            return False
        tail = path[-1].strip().lower()
        return tail in {"territoire", "territoires"}

    def _extract_zone_from_path(self, path: list[str]) -> str | None:
        for item in path:
            name = item.strip().upper()
            if name.startswith("ZONE "):
                return item.strip()
        return None

    def _extract_province_from_path(self, path: list[str]) -> str | None:
        if len(path) < 2:
            return None
        # expected ... > Provinces > <Province> > Territoire(s)
        for index in range(len(path) - 1):
            if path[index].strip().lower() == "provinces" and index + 1 < len(path):
                return path[index + 1].strip()
        return None

    def _zone_code_from_name(self, zone_name: str) -> str:
        normalized = zone_name.strip().upper()
        if "NORD" in normalized:
            return "ND"
        if "OUEST" in normalized:
            return "OT"
        if "CENTRE" in normalized:
            return "CE"
        if "SUD" in normalized:
            return "SD"
        if "EST" in normalized:
            return "ET"
        return "INCONNU"

    def _normalize_zone_label(self, zone_name: str) -> str:
        label = zone_name.strip().upper().replace("ZONE ", "")
        mapping = {
            "NORD": "Zone Nord",
            "OUEST": "Zone Ouest",
            "CENTRE": "Zone Centre",
            "SUD": "Zone Sud",
            "EST": "Zone Est",
        }
        return mapping.get(label, f"Zone {label.title()}")

    def _extract_extended_data(self, placemark: ET.Element) -> dict[str, str]:
        data: dict[str, str] = {}
        for node in placemark.findall(".//kml:Data", KML_NAMESPACE):
            key = node.attrib.get("name")
            value = (node.findtext("kml:value", default="", namespaces=KML_NAMESPACE) or "").strip()
            if key:
                data[key] = value
        for node in placemark.findall(".//kml:SimpleData", KML_NAMESPACE):
            key = node.attrib.get("name")
            value = (node.text or "").strip()
            if key:
                data[key] = value
        return data

    def _extract_geometry(self, placemark: ET.Element) -> dict[str, Any] | None:
        polygon = placemark.find("kml:Polygon", KML_NAMESPACE)
        if polygon is not None:
            coords = self._extract_coordinates(polygon)
            return {"type": "Polygon", "coordinates": [coords]} if coords else {"type": "Polygon", "coordinates": []}

        multi = placemark.find("kml:MultiGeometry", KML_NAMESPACE)
        if multi is not None:
            polygons: list[list[tuple[float, float, float | None]]] = []
            for node in multi.findall("kml:Polygon", KML_NAMESPACE):
                polygons.append(self._extract_coordinates(node))
            return {"type": "MultiPolygon", "coordinates": [[poly] for poly in polygons]}

        point = placemark.find("kml:Point", KML_NAMESPACE)
        if point is not None:
            coords = self._extract_coordinates(point)
            if coords:
                lon, lat, alt = coords[0]
                out = [lon, lat]
                if alt is not None:
                    out.append(alt)
                return {"type": "Point", "coordinates": out}
            return {"type": "Point", "coordinates": []}

        line = placemark.find("kml:LineString", KML_NAMESPACE)
        if line is not None:
            coords = self._extract_coordinates(line)
            return {"type": "LineString", "coordinates": [[lon, lat] for lon, lat, _ in coords]}

        return None

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

    def _check_inconsistencies(
        self,
        zone_name: str,
        province_name: str,
        territory_name: str,
        extended_data: dict[str, str],
        description_values: dict[str, str],
    ) -> list[str]:
        inconsistencies: list[str] = []

        expected_zone_tokens = [self._zone_code_from_name(zone_name), zone_name.replace("ZONE", "").strip()]
        expected_province = province_name.strip().lower()
        expected_territory = territory_name.strip().lower()

        observed_zone_values = self._collect_values_by_hints(
            extended_data=extended_data,
            description_values=description_values,
            hints=("zone",),
        )
        if observed_zone_values and not any(self._matches_zone(value, expected_zone_tokens) for value in observed_zone_values):
            inconsistencies.append("Zone attributaire incohérente avec la zone déduite de l'arborescence")

        observed_province_values = self._collect_values_by_hints(
            extended_data=extended_data,
            description_values=description_values,
            hints=("province",),
        )
        if observed_province_values and not any(self._normalize_text(value) == expected_province for value in observed_province_values):
            inconsistencies.append("Province attributaire incohérente avec la province parente")

        observed_name_values = self._collect_values_by_hints(
            extended_data=extended_data,
            description_values=description_values,
            hints=("nom", "name", "territoire"),
        )
        if observed_name_values and not any(self._normalize_text(value) == expected_territory for value in observed_name_values):
            inconsistencies.append("Nom territoire attributaire incohérent avec le placemark")

        return inconsistencies

    def _collect_values_by_hints(
        self,
        extended_data: dict[str, str],
        description_values: dict[str, str],
        hints: tuple[str, ...],
    ) -> list[str]:
        values: list[str] = []
        for key, value in extended_data.items():
            key_norm = self._normalize_text(key)
            if any(hint in key_norm for hint in hints) and str(value).strip():
                values.append(str(value).strip())
        for key, value in description_values.items():
            key_norm = self._normalize_text(key)
            if any(hint in key_norm for hint in hints) and str(value).strip():
                values.append(str(value).strip())
        return values

    def _matches_zone(self, value: str, expected_zone_tokens: list[str]) -> bool:
        normalized = self._normalize_text(value)
        expected = [self._normalize_text(token) for token in expected_zone_tokens if token]
        return any(token and token in normalized for token in expected)

    def _normalize_text(self, value: str) -> str:
        normalized = str(value).strip().lower()
        normalized = normalized.replace("é", "e").replace("è", "e").replace("ê", "e")
        normalized = normalized.replace("à", "a").replace("â", "a")
        normalized = " ".join(normalized.replace("_", " ").split())
        return normalized

    def _compute_score(self, geometry: dict[str, Any] | None, incoherences: list[str], attributes: dict[str, Any]) -> float:
        score = 100.0
        if not geometry:
            score -= 40.0
        if not attributes.get("extended_data") and not attributes.get("description_values"):
            score -= 10.0
        score -= min(40.0, float(len(incoherences) * 15.0))
        return max(0.0, round(score, 2))
