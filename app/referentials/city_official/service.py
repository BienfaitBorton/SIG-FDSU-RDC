from __future__ import annotations

import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.geospatial.description_parser import DescriptionParser
from app.geospatial.kmz_reader import KML_NAMESPACE, KMZReader

from .models import (
    CityCanonicalEntity,
    CityFactSheet,
    CityOfficialRunResult,
    CityQualityReport,
    CityReferentialReport,
)
from .reporting import CityReportWriter


class CityOfficialReferentialService:
    """Builds official city referential from KMZ Zones using TYPE=Commune only."""

    def __init__(self) -> None:
        self.reader = KMZReader()
        self.description_parser = DescriptionParser()
        self.writer = CityReportWriter()

    def run(
        self,
        source_path: str | Path,
        output_dir: str | Path = Path("data/reports/city_official"),
    ) -> CityOfficialRunResult:
        source = Path(source_path)
        output = Path(output_dir)

        document = self.reader.read(source)
        root = ET.fromstring(document.kml_text)

        raw_entities = self._extract_city_candidates(root, source_name=source.name)
        city_referential = self._build_canonical_entities(raw_entities, source.name)
        city_fact_sheets = self._build_fact_sheets(city_referential)
        quality = self._build_quality_report(source.name, city_referential)

        report = CityReferentialReport(
            source_file=source.name,
            generated_at=datetime.now(timezone.utc),
            city_referential=city_referential,
            city_fact_sheets=city_fact_sheets,
            quality=quality,
        )

        referential_json_path = output / "city_referential_official.json"
        fact_sheets_json_path = output / "city_fact_sheets.json"
        quality_json_path = output / "city_quality_report.json"
        report_markdown_path = output / "city_referential_report.md"
        files_report_path = output / "city_files_report.json"

        self.writer.write_referential_json(report, referential_json_path)
        self.writer.write_fact_sheets_json(report.city_fact_sheets, fact_sheets_json_path)
        self.writer.write_quality_json(report.quality, quality_json_path)
        self.writer.write_markdown(report, report_markdown_path)
        self.writer.write_json(
            {
                "source": source.name,
                "created_files": [
                    str(referential_json_path),
                    str(fact_sheets_json_path),
                    str(quality_json_path),
                    str(report_markdown_path),
                ],
                "generated_at": report.generated_at.isoformat(timespec="seconds"),
            },
            files_report_path,
        )

        return CityOfficialRunResult(
            source_path=source,
            report=report,
            referential_json_path=referential_json_path,
            fact_sheets_json_path=fact_sheets_json_path,
            quality_json_path=quality_json_path,
            report_markdown_path=report_markdown_path,
            files_report_path=files_report_path,
        )

    def _extract_city_candidates(self, root: ET.Element, source_name: str) -> list[dict[str, Any]]:
        entities: list[dict[str, Any]] = []

        def walk(node: ET.Element, path: list[str]) -> None:
            tag = node.tag.split("}")[-1]
            current_path = list(path)
            if tag in {"Document", "Folder"}:
                name = (node.findtext("kml:name", default="", namespaces=KML_NAMESPACE) or "").strip()
                if name:
                    current_path.append(name)

            if tag == "Placemark":
                entity = self._placemark_to_city_candidate(node, current_path, source_name)
                if entity is not None:
                    entities.append(entity)
                return

            for child in list(node):
                walk(child, current_path)

        walk(root, [])
        return entities

    def _placemark_to_city_candidate(self, placemark: ET.Element, path: list[str], source_name: str) -> dict[str, Any] | None:
        if len(path) != 6:
            return None
        if path[-1].strip().lower() not in {"territoire", "territoires"}:
            return None

        extended_data = self._extract_extended_data(placemark)
        type_value = (extended_data.get("TYPE") or extended_data.get("type") or "").strip().lower()
        if type_value not in {"commune", "communes"}:
            return None

        city_name = (placemark.findtext("kml:name", default="", namespaces=KML_NAMESPACE) or "").strip()
        if not city_name:
            return None

        zone_folder = path[2].strip() if len(path) > 2 else ""
        province = path[4].strip() if len(path) > 4 else ""
        zone_fdsu = self._zone_code(zone_folder)
        geometry = self._extract_geometry(placemark)

        description_html = (placemark.findtext("kml:description", default="", namespaces=KML_NAMESPACE) or "").strip()
        description_values = self.description_parser.parse(description_html)

        full_path = ["RDC", self._zone_label(zone_folder), province, city_name]

        return {
            "name": city_name,
            "province": province,
            "zone_fdsu": zone_fdsu,
            "geometry": geometry,
            "metadata": {
                "hierarchy_path": full_path,
                "kmz_path": [*path, city_name],
                "parent_folder": path[-1],
                "source_type": extended_data.get("TYPE") or extended_data.get("type") or "",
                "description": description_html,
                "description_values": description_values,
                "extended_data": extended_data,
                "future_commune_model": {
                    "role": "ville_reference",
                    "next_step": "attacher_communes_urbaines_et_rurales",
                },
            },
            "source": source_name,
        }

    def _build_canonical_entities(self, raw_entities: list[dict[str, Any]], source_name: str) -> list[CityCanonicalEntity]:
        entities: list[CityCanonicalEntity] = []
        for item in raw_entities:
            score = self._compute_quality(
                province=item["province"],
                zone=item["zone_fdsu"],
                geometry=item["geometry"],
            )
            normalized_name = self._normalize_token(item["name"])
            canonical_id = f"RDC-{item['zone_fdsu']}-VILLE-{normalized_name}"
            entities.append(
                CityCanonicalEntity(
                    canonical_id=canonical_id,
                    nom=item["name"],
                    niveau="Ville",
                    province=item["province"],
                    zone_fdsu=item["zone_fdsu"],
                    geometry=item["geometry"],
                    source=source_name,
                    statut="official_candidate",
                    qualite=score,
                    metadata=item["metadata"],
                )
            )

        entities.sort(key=lambda city: (city.zone_fdsu, city.province, city.nom))
        return entities

    def _build_fact_sheets(self, entities: list[CityCanonicalEntity]) -> list[CityFactSheet]:
        fact_sheets: list[CityFactSheet] = []
        for city in entities:
            flags: list[str] = []
            if not city.province:
                flags.append("orphan_city")
            if not city.zone_fdsu or city.zone_fdsu == "INCONNU":
                flags.append("unknown_zone")
            if not city.geometry:
                flags.append("empty_geometry")

            fact_sheets.append(
                CityFactSheet(
                    canonical_id=city.canonical_id,
                    nom=city.nom,
                    province=city.province,
                    zone_fdsu=city.zone_fdsu,
                    geometry_type=(city.geometry or {}).get("type") if city.geometry else None,
                    source=city.source,
                    quality_flags=flags,
                    metadata={
                        "niveau": city.niveau,
                        "statut": city.statut,
                        "qualite": city.qualite,
                        "hierarchy_path": city.metadata.get("hierarchy_path", []),
                    },
                )
            )
        return fact_sheets

    def _build_quality_report(self, source_file: str, entities: list[CityCanonicalEntity]) -> CityQualityReport:
        anomalies: list[str] = []

        orphan_count = sum(1 for city in entities if not city.province)
        if orphan_count:
            anomalies.append(f"{orphan_count} ville(s) orpheline(s) sans province")

        empty_geometry_count = sum(1 for city in entities if not city.geometry)
        if empty_geometry_count:
            anomalies.append(f"{empty_geometry_count} ville(s) avec géométrie vide")

        by_name_provinces: dict[str, set[str]] = defaultdict(set)
        by_name_zones: dict[str, set[str]] = defaultdict(set)
        for city in entities:
            key = self._normalize_token(city.nom)
            by_name_provinces[key].add(city.province)
            by_name_zones[key].add(city.zone_fdsu)

        multi_province_conflicts = sum(1 for values in by_name_provinces.values() if len(values) > 1)
        if multi_province_conflicts:
            anomalies.append(f"{multi_province_conflicts} conflit(s) ville multi-province")

        multi_zone_conflicts = sum(1 for values in by_name_zones.values() if len(values) > 1)
        if multi_zone_conflicts:
            anomalies.append(f"{multi_zone_conflicts} conflit(s) ville multi-zone")

        normalized_names = [self._normalize_token(city.nom) for city in entities]
        duplicate_counter = Counter(normalized_names)
        duplicate_names = sorted(name for name, count in duplicate_counter.items() if count > 1)
        duplicate_count = len(duplicate_names)
        if duplicate_count:
            anomalies.append(f"{duplicate_count} doublon(s) de villes")

        penalties = (orphan_count * 25.0) + (empty_geometry_count * 20.0) + (multi_province_conflicts * 25.0) + (multi_zone_conflicts * 25.0) + (duplicate_count * 20.0)
        base = 100.0 - (penalties / max(len(entities), 1))
        global_score = round(max(0.0, base), 2)

        return CityQualityReport(
            source_file=source_file,
            generated_at=datetime.now(timezone.utc),
            city_count=len(entities),
            orphan_city_count=orphan_count,
            multi_province_conflicts=multi_province_conflicts,
            multi_zone_conflicts=multi_zone_conflicts,
            empty_geometry_count=empty_geometry_count,
            duplicate_count=duplicate_count,
            duplicate_names=duplicate_names,
            anomalies=anomalies,
            global_score=global_score,
        )

    def _extract_extended_data(self, placemark: ET.Element) -> dict[str, str]:
        data: dict[str, str] = {}
        for node in placemark.findall('.//kml:Data', KML_NAMESPACE):
            key = node.attrib.get('name')
            value = (node.findtext('kml:value', default='', namespaces=KML_NAMESPACE) or '').strip()
            if key:
                data[key] = value
        for node in placemark.findall('.//kml:SimpleData', KML_NAMESPACE):
            key = node.attrib.get('name')
            value = (node.text or '').strip()
            if key:
                data[key] = value
        return data

    def _extract_geometry(self, placemark: ET.Element) -> dict[str, Any] | None:
        polygon = placemark.find('kml:Polygon', KML_NAMESPACE)
        if polygon is not None:
            coordinates = self._extract_coordinates(polygon)
            return {"type": "Polygon", "coordinates": [coordinates]} if coordinates else {"type": "Polygon", "coordinates": []}

        multi = placemark.find('kml:MultiGeometry', KML_NAMESPACE)
        if multi is not None:
            polygons: list[list[tuple[float, float, float | None]]] = []
            for node in multi.findall('kml:Polygon', KML_NAMESPACE):
                polygons.append(self._extract_coordinates(node))
            return {"type": "MultiPolygon", "coordinates": [[poly] for poly in polygons]}

        point = placemark.find('kml:Point', KML_NAMESPACE)
        if point is not None:
            coordinates = self._extract_coordinates(point)
            if coordinates:
                lon, lat, alt = coordinates[0]
                payload = [lon, lat]
                if alt is not None:
                    payload.append(alt)
                return {"type": "Point", "coordinates": payload}
            return {"type": "Point", "coordinates": []}

        line = placemark.find('kml:LineString', KML_NAMESPACE)
        if line is not None:
            coordinates = self._extract_coordinates(line)
            return {"type": "LineString", "coordinates": [[lon, lat] for lon, lat, _ in coordinates]}

        return None

    def _extract_coordinates(self, node: ET.Element) -> list[tuple[float, float, float | None]]:
        text = (node.findtext('.//kml:coordinates', default='', namespaces=KML_NAMESPACE) or '').strip()
        if not text:
            return []
        coordinates: list[tuple[float, float, float | None]] = []
        for chunk in text.replace('\n', ' ').split():
            parts = [part for part in chunk.split(',') if part]
            if len(parts) >= 2:
                lon = float(parts[0])
                lat = float(parts[1])
                alt = float(parts[2]) if len(parts) > 2 else None
                coordinates.append((lon, lat, alt))
        return coordinates

    def _zone_code(self, zone_name: str) -> str:
        upper = zone_name.upper()
        if 'NORD' in upper:
            return 'ND'
        if 'OUEST' in upper:
            return 'OT'
        if 'CENTRE' in upper:
            return 'CE'
        if 'SUD' in upper:
            return 'SD'
        if 'EST' in upper:
            return 'ET'
        return 'INCONNU'

    def _zone_label(self, zone_folder: str) -> str:
        upper = zone_folder.upper().replace('ZONE ', '').strip()
        mapping = {
            'NORD': 'Zone Nord',
            'OUEST': 'Zone Ouest',
            'CENTRE': 'Zone Centre',
            'SUD': 'Zone Sud',
            'EST': 'Zone Est',
        }
        return mapping.get(upper, f"Zone {upper.title()}")

    def _compute_quality(self, province: str, zone: str, geometry: dict[str, Any] | None) -> float:
        score = 100.0
        if not province:
            score -= 30.0
        if not zone or zone == 'INCONNU':
            score -= 30.0
        if not geometry:
            score -= 40.0
        return max(0.0, round(score, 2))

    def _normalize_token(self, value: str) -> str:
        normalized = value.strip().upper()
        normalized = normalized.replace('É', 'E').replace('È', 'E').replace('Ê', 'E')
        normalized = normalized.replace('À', 'A').replace('Â', 'A')
        normalized = normalized.replace('-', '_').replace(' ', '_')
        return ''.join(ch for ch in normalized if ch.isalnum() or ch == '_')
