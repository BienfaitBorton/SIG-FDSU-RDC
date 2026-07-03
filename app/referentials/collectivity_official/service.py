from __future__ import annotations

import json
import re
import unicodedata
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.geospatial.description_parser import DescriptionParser
from app.geospatial.kmz_reader import KML_NAMESPACE, KMZReader

from .models import (
    CollectivityAnomaly,
    CollectivityCanonicalEntity,
    CollectivityFactSheet,
    CollectivityOfficialRunResult,
    CollectivityQualityReport,
    CollectivityReferentialReport,
)
from .reporting import CollectivityReportWriter


class CollectivityOfficialReferentialService:
    """Builds the official collectivity referential from collectivites.kmz only."""

    def __init__(self) -> None:
        self.reader = KMZReader()
        self.description_parser = DescriptionParser()
        self.writer = CollectivityReportWriter()

    def run(
        self,
        source_path: str | Path,
        output_dir: str | Path = Path("data/reports/collectivity_official"),
        territory_report_path: str | Path = Path("data/reports/territory_hierarchy/territoires_hierarchie_kmz.report.json"),
    ) -> CollectivityOfficialRunResult:
        source = Path(source_path)
        output = Path(output_dir)

        territory_index = self._load_territory_index(territory_report_path)
        document = self.reader.read(source)
        root = ET.fromstring(document.kml_text)

        raw_entities = self._extract_candidates(root, source.name, territory_index)
        collectivity_referential = self._build_canonical_entities(raw_entities, source.name)
        fact_sheets = self._build_fact_sheets(collectivity_referential)
        territory_collectivity_index = self._build_territory_index(collectivity_referential)
        province_collectivity_index = self._build_province_index(collectivity_referential)
        quality = self._build_quality_report(source.name, collectivity_referential)

        report = CollectivityReferentialReport(
            source_file=source.name,
            generated_at=datetime.now(timezone.utc),
            collectivity_referential=collectivity_referential,
            collectivity_fact_sheets=fact_sheets,
            territory_collectivity_index=territory_collectivity_index,
            province_collectivity_index=province_collectivity_index,
            quality=quality,
        )

        referential_json_path = output / "collectivity_referential_official.json"
        fact_sheets_json_path = output / "collectivity_fact_sheets.json"
        quality_json_path = output / "collectivity_quality_report.json"
        report_markdown_path = output / "collectivity_referential_report.md"
        files_report_path = output / "collectivity_files_report.json"
        territory_index_json_path = output / "territory_collectivity_index.json"
        province_index_json_path = output / "province_collectivity_index.json"
        national_counter_registry_path = output.parent / "national_counter_registry.json"

        self.writer.write_referential_json(report, referential_json_path)
        self.writer.write_fact_sheets_json(report.collectivity_fact_sheets, fact_sheets_json_path)
        self.writer.write_quality_json(report.quality, quality_json_path)
        self.writer.write_markdown(report, report_markdown_path)
        self.writer.write_json(report.territory_collectivity_index, territory_index_json_path)
        self.writer.write_json(report.province_collectivity_index, province_index_json_path)
        self.writer.write_json(
            self._build_national_counter_registry(report),
            national_counter_registry_path,
        )
        self.writer.write_json(
            {
                "source": source.name,
                "created_files": [
                    str(referential_json_path),
                    str(fact_sheets_json_path),
                    str(quality_json_path),
                    str(report_markdown_path),
                    str(files_report_path),
                    str(territory_index_json_path),
                    str(province_index_json_path),
                    str(national_counter_registry_path),
                ],
                "generated_at": report.generated_at.isoformat(timespec="seconds"),
            },
            files_report_path,
        )

        return CollectivityOfficialRunResult(
            source_path=source,
            report=report,
            referential_json_path=referential_json_path,
            fact_sheets_json_path=fact_sheets_json_path,
            quality_json_path=quality_json_path,
            report_markdown_path=report_markdown_path,
            files_report_path=files_report_path,
            territory_index_json_path=territory_index_json_path,
            province_index_json_path=province_index_json_path,
            national_counter_registry_path=national_counter_registry_path,
        )

    def _load_territory_index(self, path: str | Path) -> dict[str, dict[str, str]]:
        report_path = Path(path)
        if not report_path.exists():
            return {}

        payload = json.loads(report_path.read_text(encoding="utf-8"))
        territories: dict[str, dict[str, str]] = {}
        for item in payload.get("territories", []):
            extended_data = item.get("attributs", {}).get("extended_data", {})
            if self._normalize_type(extended_data.get("TYPE", "")) != "territoire":
                continue
            code = self._clean_code(extended_data.get("CODE_INS"))
            if not code:
                continue
            territories[code[:4]] = {
                "territoire": item.get("nom", ""),
                "province": item.get("province", ""),
                "zone_fdsu": item.get("zone_fdsu", ""),
            }
        return territories

    def _extract_candidates(
        self,
        root: ET.Element,
        source_name: str,
        territory_index: dict[str, dict[str, str]],
    ) -> list[dict[str, Any]]:
        entities: list[dict[str, Any]] = []

        def walk(node: ET.Element, path: list[str]) -> None:
            tag = node.tag.split("}")[-1]
            current_path = list(path)
            if tag in {"Document", "Folder"}:
                name = (node.findtext("kml:name", default="", namespaces=KML_NAMESPACE) or "").strip()
                if name:
                    current_path.append(name)

            if tag == "Placemark":
                entity = self._placemark_to_candidate(node, current_path, source_name, territory_index)
                if entity is not None:
                    entities.append(entity)
                return

            for child in list(node):
                walk(child, current_path)

        walk(root, [])
        return entities

    def _placemark_to_candidate(
        self,
        placemark: ET.Element,
        path: list[str],
        source_name: str,
        territory_index: dict[str, dict[str, str]],
    ) -> dict[str, Any] | None:
        name = (placemark.findtext("kml:name", default="", namespaces=KML_NAMESPACE) or "").strip()
        if not name:
            return None

        extended_data = self._extract_extended_data(placemark)
        description_html = (placemark.findtext("kml:description", default="", namespaces=KML_NAMESPACE) or "").strip()
        description_values = self.description_parser.parse(description_html)
        classification = self._classify_collectivity(extended_data, description_values, description_html, path)
        if classification == "Autre":
            return None

        code_officiel = self._extract_code(extended_data, description_values)
        territory_info = territory_index.get((code_officiel or "")[:4], {})
        province_from_path = self._extract_province_from_path(path)
        zone_from_path = self._extract_zone_from_path(path)

        province = territory_info.get("province") or province_from_path
        territoire = territory_info.get("territoire", "")
        zone_fdsu = territory_info.get("zone_fdsu") or self._zone_code(zone_from_path)
        geometry = self._extract_geometry(placemark)
        hierarchy_path = ["RDC"]
        if zone_fdsu:
            hierarchy_path.append(self._zone_label(zone_fdsu))
        if province:
            hierarchy_path.append(province)
        if territoire:
            hierarchy_path.append(territoire)
        hierarchy_path.append(name)

        return {
            "name": name,
            "type_collectivite": classification,
            "province": province,
            "territoire": territoire,
            "zone_fdsu": zone_fdsu,
            "geometry": geometry,
            "code_officiel": code_officiel,
            "metadata": {
                "hierarchy_path": hierarchy_path,
                "kmz_path": [*path, name],
                "classification_priority": self._classification_source(extended_data, description_values, description_html, path),
                "description": description_html,
                "description_values": description_values,
                "extended_data": extended_data,
                "source_file": source_name,
                "geometry_type": (geometry or {}).get("type") if geometry else None,
                "future_children": "Groupements",
            },
        }

    def _build_canonical_entities(
        self,
        raw_entities: list[dict[str, Any]],
        source_name: str,
    ) -> list[CollectivityCanonicalEntity]:
        entities: list[CollectivityCanonicalEntity] = []
        for item in raw_entities:
            normalized_name = self._normalize_token(item["name"])
            normalized_territory = self._normalize_token(item["territoire"] or "TERRITOIRE_INCONNU")
            normalized_type = self._normalize_token(item["type_collectivite"])
            zone = item["zone_fdsu"] or "INCONNU"
            canonical_id = f"RDC-{zone}-COLL-{normalized_territory}-{normalized_type}-{normalized_name}"
            quality = self._compute_entity_quality(item)
            entities.append(
                CollectivityCanonicalEntity(
                    canonical_id=canonical_id,
                    nom=item["name"],
                    niveau="Collectivité",
                    type_collectivite=item["type_collectivite"],
                    province=item["province"],
                    territoire=item["territoire"],
                    zone_fdsu=zone,
                    geometry=item["geometry"],
                    code_officiel=item["code_officiel"],
                    source=source_name,
                    statut="official_candidate",
                    qualite=quality,
                    metadata=item["metadata"],
                )
            )

        entities.sort(key=lambda item: (item.zone_fdsu, item.province, item.territoire, item.type_collectivite, item.nom))
        return entities

    def _build_fact_sheets(self, entities: list[CollectivityCanonicalEntity]) -> list[CollectivityFactSheet]:
        fact_sheets: list[CollectivityFactSheet] = []
        for item in entities:
            flags: list[str] = []
            if not item.territoire:
                flags.append("missing_territory")
            if not item.province:
                flags.append("missing_province")
            if not item.zone_fdsu or item.zone_fdsu == "INCONNU":
                flags.append("missing_zone")
            if not self._is_valid_geometry(item.geometry):
                flags.append("invalid_geometry")
            if item.type_collectivite == "Type inconnu":
                flags.append("unknown_type")

            fact_sheets.append(
                CollectivityFactSheet(
                    canonical_id=item.canonical_id,
                    nom=item.nom,
                    type_collectivite=item.type_collectivite,
                    province=item.province,
                    territoire=item.territoire,
                    zone_fdsu=item.zone_fdsu,
                    code_officiel=item.code_officiel,
                    geometry_type=(item.geometry or {}).get("type") if item.geometry else None,
                    source=item.source,
                    quality_flags=flags,
                    metadata={
                        "niveau": item.niveau,
                        "statut": item.statut,
                        "qualite": item.qualite,
                        "hierarchy_path": item.metadata.get("hierarchy_path", []),
                        "future_children": item.metadata.get("future_children"),
                    },
                )
            )
        return fact_sheets

    def _build_quality_report(
        self,
        source_file: str,
        entities: list[CollectivityCanonicalEntity],
    ) -> CollectivityQualityReport:
        anomalies: list[CollectivityAnomaly] = []
        duplicate_keys = self._duplicate_keys(entities)

        for item in entities:
            if not item.territoire:
                anomalies.append(self._missing_territory_anomaly(item))
            if not item.province:
                anomalies.append(self._anomaly(item, "province parent non determinee", "Collectivite sans province heritee", "Verifier l'arborescence KMZ et le rattachement territorial."))
            if not item.zone_fdsu or item.zone_fdsu == "INCONNU":
                anomalies.append(self._anomaly(item, "zone FDSU non determinee", "Collectivite sans zone FDSU heritee", "Verifier le dossier Zone du KMZ ou le territoire parent."))
            if not self._is_valid_geometry(item.geometry):
                anomalies.append(self._anomaly(item, "geometrie invalide", "Geometrie absente, vide ou non polygonale", "Controler la geometrie source dans collectivites.kmz."))
            if item.type_collectivite == "Type inconnu":
                anomalies.append(self._anomaly(item, "type non determine", "Type collectivité non determine", "Renseigner TYPE=Secteur ou TYPE=Chefferie dans la source."))

        for key in duplicate_keys:
            matching = [item for item in entities if self._dedupe_key(item) == key]
            for item in matching:
                anomalies.append(self._anomaly(item, "doublon referentiel", f"Doublon detecte: {key}", "Verifier les occurrences homonymes dans le meme territoire."))

        secteur_count = sum(1 for item in entities if item.type_collectivite == "Secteur")
        chefferie_count = sum(1 for item in entities if item.type_collectivite == "Chefferie")
        missing_territory_count = sum(1 for item in entities if not item.territoire)
        missing_province_count = sum(1 for item in entities if not item.province)
        missing_zone_count = sum(1 for item in entities if not item.zone_fdsu or item.zone_fdsu == "INCONNU")
        invalid_geometry_count = sum(1 for item in entities if not self._is_valid_geometry(item.geometry))
        unknown_type_count = sum(1 for item in entities if item.type_collectivite == "Type inconnu")
        duplicate_count = len(duplicate_keys)

        penalties = (
            (missing_territory_count * 25.0)
            + (missing_province_count * 25.0)
            + (missing_zone_count * 25.0)
            + (invalid_geometry_count * 20.0)
            + (duplicate_count * 20.0)
            + (unknown_type_count * 15.0)
        )
        global_score = round(max(0.0, 100.0 - (penalties / max(len(entities), 1))), 2)

        return CollectivityQualityReport(
            source_file=source_file,
            generated_at=datetime.now(timezone.utc),
            collectivity_count=len(entities),
            secteur_count=secteur_count,
            chefferie_count=chefferie_count,
            missing_territory_count=missing_territory_count,
            missing_province_count=missing_province_count,
            missing_zone_count=missing_zone_count,
            invalid_geometry_count=invalid_geometry_count,
            duplicate_count=duplicate_count,
            unknown_type_count=unknown_type_count,
            duplicate_keys=duplicate_keys,
            anomalies=anomalies,
            global_score=global_score,
        )

    def _build_territory_index(self, entities: list[CollectivityCanonicalEntity]) -> dict[str, Any]:
        grouped: dict[tuple[str, str, str], list[CollectivityCanonicalEntity]] = defaultdict(list)
        for item in entities:
            grouped[(item.zone_fdsu, item.province, item.territoire)].append(item)

        territories: list[dict[str, Any]] = []
        for (zone, province, territory), items in sorted(grouped.items(), key=lambda row: row[0]):
            secteurs = sorted(item.nom for item in items if item.type_collectivite == "Secteur")
            chefferies = sorted(item.nom for item in items if item.type_collectivite == "Chefferie")
            territories.append(
                {
                    "territoire": territory,
                    "province": province,
                    "zone_fdsu": zone,
                    "secteurs": secteurs,
                    "chefferies": chefferies,
                    "nombre_collectivites": len(items),
                }
            )
        return {"territories": territories, "count": len(territories)}

    def _build_province_index(self, entities: list[CollectivityCanonicalEntity]) -> dict[str, Any]:
        provinces: dict[tuple[str, str], dict[str, Any]] = {}
        territory_groups: dict[tuple[str, str, str], list[CollectivityCanonicalEntity]] = defaultdict(list)
        for item in entities:
            provinces.setdefault((item.zone_fdsu, item.province), {"province": item.province, "zone_fdsu": item.zone_fdsu})
            territory_groups[(item.zone_fdsu, item.province, item.territoire)].append(item)

        out: list[dict[str, Any]] = []
        for (zone, province), base in sorted(provinces.items()):
            territories: list[dict[str, Any]] = []
            for (territory_zone, territory_province, territory), items in sorted(territory_groups.items()):
                if territory_zone != zone or territory_province != province:
                    continue
                territories.append(
                    {
                        "territoire": territory,
                        "collectivites": [
                            {
                                "nom": item.nom,
                                "type_collectivite": item.type_collectivite,
                                "canonical_id": item.canonical_id,
                                "code_officiel": item.code_officiel,
                            }
                            for item in sorted(items, key=lambda value: (value.type_collectivite, value.nom))
                        ],
                        "nombre_collectivites": len(items),
                    }
                )
            out.append({**base, "territoires": territories, "nombre_territoires": len(territories)})
        return {"provinces": out, "count": len(out)}

    def _build_national_counter_registry(self, report: CollectivityReferentialReport) -> dict[str, Any]:
        return {
            "generated_at": report.generated_at.isoformat(timespec="seconds"),
            "source": report.source_file,
            "registre_national_des_compteurs": {
                "provinces": {"nombre": 26, "statut": "validées"},
                "territoires": {"nombre": 145, "statut": "validés"},
                "villes": {"nombre": 11, "statut": "validées"},
                "secteurs": {"nombre": report.quality.secteur_count, "statut": "validés provisoirement"},
                "chefferies": {"nombre": report.quality.chefferie_count, "statut": "validées provisoirement"},
                "collectivites": {"nombre": report.quality.collectivity_count, "statut": "validées provisoirement"},
                "anomalies_collectivites": {"nombre": len(report.quality.anomalies)},
            },
        }

    def _classify_collectivity(
        self,
        extended_data: dict[str, str],
        description_values: dict[str, str],
        description_html: str,
        path: list[str],
    ) -> str:
        type_value = extended_data.get("TYPE") or extended_data.get("type")
        classified = self._classify_text(type_value)
        if classified:
            return classified
        if self._is_explicit_other(type_value):
            return "Autre"

        for key, value in extended_data.items():
            if key.lower() in {"type", "type_collectivite", "nature", "categorie"}:
                classified = self._classify_text(value)
                if classified:
                    return classified
                if self._is_explicit_other(value):
                    return "Autre"

        for key, value in description_values.items():
            if any(hint in key for hint in ("type", "nature", "categorie")):
                classified = self._classify_text(value)
                if classified:
                    return classified
                if self._is_explicit_other(value):
                    return "Autre"

        classified = self._classify_text(description_html)
        if classified:
            return classified

        classified = self._classify_text(" ".join(path))
        return classified or "Type inconnu"

    def _classification_source(
        self,
        extended_data: dict[str, str],
        description_values: dict[str, str],
        description_html: str,
        path: list[str],
    ) -> str:
        type_value = extended_data.get("TYPE") or extended_data.get("type")
        if self._classify_text(type_value) or self._is_explicit_other(type_value):
            return "TYPE"
        for key, value in extended_data.items():
            if key.lower() in {"type", "type_collectivite", "nature", "categorie"} and (self._classify_text(value) or self._is_explicit_other(value)):
                return "ExtendedData"
        for key, value in description_values.items():
            if any(hint in key for hint in ("type", "nature", "categorie")) and (self._classify_text(value) or self._is_explicit_other(value)):
                return "Description"
        if self._classify_text(description_html):
            return "Description"
        if self._classify_text(" ".join(path)):
            return "Arborescence KMZ"
        return "Non determine"

    def _classify_text(self, value: str | None) -> str | None:
        normalized = self._normalize_type(value or "")
        if "secteur" in normalized:
            return "Secteur"
        if "chefferie" in normalized:
            return "Chefferie"
        return None

    def _is_explicit_other(self, value: str | None) -> bool:
        normalized = self._normalize_type(value or "")
        return normalized in {"commune", "communes", "cite", "cites", "ville", "villes", "territoire", "territoires"}

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

    def _extract_code(self, extended_data: dict[str, str], description_values: dict[str, str]) -> str | None:
        for key in ("CODE_INS", "code_ins", "CODE", "code", "code_officiel"):
            code = self._clean_code(extended_data.get(key) or description_values.get(key.lower()))
            if code:
                return code
        return None

    def _extract_province_from_path(self, path: list[str]) -> str:
        for item in reversed(path):
            name = item.strip()
            normalized = self._normalize_type(name)
            if normalized.startswith("collectivites "):
                return name.split(" ", 1)[1].strip()
        return ""

    def _extract_zone_from_path(self, path: list[str]) -> str:
        for item in path:
            if self._normalize_type(item).startswith("zone "):
                return item.strip()
        return ""

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
                out: list[float] = [lon, lat]
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
        coords: list[tuple[float, float, float | None]] = []
        for chunk in text.replace("\n", " ").split():
            parts = [part for part in chunk.split(",") if part]
            if len(parts) >= 2:
                lon = float(parts[0])
                lat = float(parts[1])
                alt = float(parts[2]) if len(parts) > 2 else None
                coords.append((lon, lat, alt))
        return coords

    def _is_valid_geometry(self, geometry: dict[str, Any] | None) -> bool:
        if not geometry:
            return False
        if geometry.get("type") == "Polygon":
            rings = geometry.get("coordinates") or []
            return bool(rings and self._valid_ring(rings[0]))
        if geometry.get("type") == "MultiPolygon":
            polygons = geometry.get("coordinates") or []
            return bool(polygons) and all(poly and self._valid_ring(poly[0]) for poly in polygons)
        return False

    def _valid_ring(self, ring: list[Any]) -> bool:
        if len(ring) < 4:
            return False
        first = ring[0]
        last = ring[-1]
        return len(first) >= 2 and len(last) >= 2 and first[0] == last[0] and first[1] == last[1]

    def _compute_entity_quality(self, item: dict[str, Any]) -> float:
        score = 100.0
        if not item["territoire"]:
            score -= 25.0
        if not item["province"]:
            score -= 25.0
        if not item["zone_fdsu"] or item["zone_fdsu"] == "INCONNU":
            score -= 25.0
        if not self._is_valid_geometry(item["geometry"]):
            score -= 20.0
        if item["type_collectivite"] == "Type inconnu":
            score -= 15.0
        return round(max(0.0, score), 2)

    def _duplicate_keys(self, entities: list[CollectivityCanonicalEntity]) -> list[str]:
        counter = Counter(self._dedupe_key(item) for item in entities)
        return sorted(key for key, count in counter.items() if count > 1)

    def _dedupe_key(self, item: CollectivityCanonicalEntity) -> str:
        return "|".join(
            [
                self._normalize_token(item.province),
                self._normalize_token(item.territoire),
                self._normalize_token(item.type_collectivite),
                self._normalize_token(item.nom),
            ]
        )

    def _missing_territory_anomaly(self, item: CollectivityCanonicalEntity) -> CollectivityAnomaly:
        if item.nom == "Bahema" and item.province == "Ituri" and item.code_officiel == "10":
            return CollectivityAnomaly(
                entite="Bahema",
                type="Chefferie",
                province="Ituri",
                probleme="territoire parent non déterminé",
                cause="CODE_INS = 10 insuffisant pour rattachement territorial fiable",
                statut="À valider manuellement",
                suggestion="vérifier le territoire de rattachement officiel avant publication",
            )
        return self._anomaly(
            item,
            "territoire parent non determine",
            "Collectivite sans territoire herite",
            "Verifier le CODE_INS et le referentiel territorial parent.",
        )

    def _anomaly(self, item: CollectivityCanonicalEntity, probleme: str, cause: str, suggestion: str) -> CollectivityAnomaly:
        return CollectivityAnomaly(
            entite=item.nom,
            type=item.type_collectivite,
            province=item.province,
            probleme=probleme,
            cause=cause,
            statut="À valider manuellement",
            suggestion=suggestion,
        )

    def _clean_code(self, value: Any) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        if not text:
            return None
        if "." in text:
            text = text.split(".", 1)[0]
        digits = "".join(ch for ch in text if ch.isdigit())
        return digits or None

    def _zone_code(self, zone_name: str) -> str:
        normalized = self._normalize_type(zone_name)
        if "nord" in normalized:
            return "ND"
        if "ouest" in normalized:
            return "OT"
        if "centre" in normalized:
            return "CE"
        if "sud" in normalized:
            return "SD"
        if "est" in normalized:
            return "ET"
        return "INCONNU"

    def _zone_label(self, zone_code: str) -> str:
        return {
            "ND": "Zone Nord",
            "OT": "Zone Ouest",
            "CE": "Zone Centre",
            "SD": "Zone Sud",
            "ET": "Zone Est",
        }.get(zone_code, "Zone inconnue")

    def _normalize_type(self, value: str) -> str:
        normalized = unicodedata.normalize("NFKD", value)
        ascii_text = "".join(ch for ch in normalized if not unicodedata.combining(ch))
        return re.sub(r"\s+", " ", ascii_text).strip().lower()

    def _normalize_token(self, value: str) -> str:
        normalized = unicodedata.normalize("NFKD", value or "")
        ascii_text = "".join(ch for ch in normalized if not unicodedata.combining(ch))
        token = ascii_text.strip().upper().replace("-", "_").replace(" ", "_")
        token = "".join(ch for ch in token if ch.isalnum() or ch == "_")
        return token or "INCONNU"
