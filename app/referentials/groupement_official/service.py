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
    GroupementAnomaly,
    GroupementCanonicalEntity,
    GroupementFactSheet,
    GroupementOfficialRunResult,
    GroupementQualityReport,
    GroupementReferentialReport,
)
from .reporting import GroupementReportWriter


class GroupementOfficialReferentialService:
    """Builds the official groupement referential from Groupements.kmz only."""

    def __init__(self) -> None:
        self.reader = KMZReader()
        self.description_parser = DescriptionParser()
        self.writer = GroupementReportWriter()

    def run(
        self,
        source_path: str | Path,
        output_dir: str | Path = Path("data/reports/groupement_official"),
        collectivity_referential_path: str | Path = Path("data/reports/collectivity_official/collectivity_referential_official.json"),
    ) -> GroupementOfficialRunResult:
        source = Path(source_path)
        output = Path(output_dir)

        collectivity_indexes = self._load_collectivity_indexes(collectivity_referential_path)
        document = self.reader.read(source)
        root = ET.fromstring(document.kml_text)

        raw_entities = self._extract_groupements(root, source.name, collectivity_indexes)
        groupement_referential = self._build_canonical_entities(raw_entities, source.name)
        fact_sheets = self._build_fact_sheets(groupement_referential)
        collectivity_groupement_index = self._build_collectivity_index(groupement_referential)
        territory_groupement_index = self._build_territory_index(groupement_referential)
        province_groupement_index = self._build_province_index(groupement_referential)
        quality = self._build_quality_report(source.name, groupement_referential)

        report = GroupementReferentialReport(
            source_file=source.name,
            generated_at=datetime.now(timezone.utc),
            groupement_referential=groupement_referential,
            groupement_fact_sheets=fact_sheets,
            collectivity_groupement_index=collectivity_groupement_index,
            territory_groupement_index=territory_groupement_index,
            province_groupement_index=province_groupement_index,
            quality=quality,
        )

        referential_json_path = output / "groupement_referential_official.json"
        fact_sheets_json_path = output / "groupement_fact_sheets.json"
        quality_json_path = output / "groupement_quality_report.json"
        report_markdown_path = output / "groupement_referential_report.md"
        files_report_path = output / "groupement_files_report.json"
        collectivity_index_json_path = output / "collectivity_groupement_index.json"
        territory_index_json_path = output / "territory_groupement_index.json"
        province_index_json_path = output / "province_groupement_index.json"
        national_counter_registry_path = output.parent / "national_counter_registry.json"

        self.writer.write_referential_json(report, referential_json_path)
        self.writer.write_fact_sheets_json(report.groupement_fact_sheets, fact_sheets_json_path)
        self.writer.write_quality_json(report.quality, quality_json_path)
        self.writer.write_markdown(report, report_markdown_path)
        self.writer.write_json(report.collectivity_groupement_index, collectivity_index_json_path)
        self.writer.write_json(report.territory_groupement_index, territory_index_json_path)
        self.writer.write_json(report.province_groupement_index, province_index_json_path)
        self.writer.write_json(
            self._build_national_counter_registry(report, national_counter_registry_path),
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
                    str(collectivity_index_json_path),
                    str(territory_index_json_path),
                    str(province_index_json_path),
                    str(national_counter_registry_path),
                ],
                "generated_at": report.generated_at.isoformat(timespec="seconds"),
            },
            files_report_path,
        )

        return GroupementOfficialRunResult(
            source_path=source,
            report=report,
            referential_json_path=referential_json_path,
            fact_sheets_json_path=fact_sheets_json_path,
            quality_json_path=quality_json_path,
            report_markdown_path=report_markdown_path,
            files_report_path=files_report_path,
            collectivity_index_json_path=collectivity_index_json_path,
            territory_index_json_path=territory_index_json_path,
            province_index_json_path=province_index_json_path,
            national_counter_registry_path=national_counter_registry_path,
        )

    def _load_collectivity_indexes(self, path: str | Path) -> dict[str, dict[Any, dict[str, Any]]]:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        entities = payload.get("collectivity_referential", [])
        by_code: dict[str, dict[str, Any]] = {}
        by_name_territory: dict[tuple[str, str], dict[str, Any]] = {}
        for item in entities:
            code = self._clean_code(item.get("code_officiel"))
            if code:
                by_code[code] = item
            by_name_territory[(self._normalize_key(item.get("nom", "")), self._normalize_key(item.get("territoire", "")))] = item
        return {"by_code": by_code, "by_name_territory": by_name_territory}

    def _extract_groupements(
        self,
        root: ET.Element,
        source_name: str,
        collectivity_indexes: dict[str, dict[Any, dict[str, Any]]],
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
                entity = self._placemark_to_groupement(node, current_path, source_name, collectivity_indexes)
                if entity is not None:
                    entities.append(entity)
                return

            for child in list(node):
                walk(child, current_path)

        walk(root, [])
        return entities

    def _placemark_to_groupement(
        self,
        placemark: ET.Element,
        path: list[str],
        source_name: str,
        collectivity_indexes: dict[str, dict[Any, dict[str, Any]]],
    ) -> dict[str, Any] | None:
        extended_data = self._extract_extended_data(placemark)
        if not extended_data:
            return None

        name = (
            extended_data.get("NOM_BD")
            or extended_data.get("NOM_RGC")
            or (placemark.findtext("kml:name", default="", namespaces=KML_NAMESPACE) or "").strip()
        )
        if not name:
            return None

        code_officiel = self._clean_code(extended_data.get("CODE_GRPT") or extended_data.get("PCODE"))
        source_collectivity_name = extended_data.get("COLLECTIV", "")
        source_territory = extended_data.get("TERRITOIRE", "")
        parent = self._resolve_parent(code_officiel, source_collectivity_name, source_territory, collectivity_indexes)
        description_html = (placemark.findtext("kml:description", default="", namespaces=KML_NAMESPACE) or "").strip()
        description_values = self.description_parser.parse(description_html)
        geometry = self._extract_geometry(placemark)
        style_url = (placemark.findtext("kml:styleUrl", default="", namespaces=KML_NAMESPACE) or "").strip()

        inconsistencies = self._check_inconsistencies(
            source_collectivity_name=source_collectivity_name,
            source_territory=source_territory,
            parent=parent,
        )

        return {
            "name": name.strip(),
            "collectivite_parent": parent.get("nom", ""),
            "type_collectivite_parent": parent.get("type_collectivite", ""),
            "territoire": parent.get("territoire", source_territory if not parent else ""),
            "province": parent.get("province", ""),
            "zone_fdsu": parent.get("zone_fdsu", ""),
            "code_officiel": code_officiel,
            "geometry": geometry,
            "metadata": {
                "kmz_path": [*path, name.strip()],
                "description": description_html,
                "description_values": description_values,
                "extended_data": extended_data,
                "styles": {"style_url": style_url},
                "source_file": source_name,
                "source_collectivite": source_collectivity_name,
                "source_territoire": source_territory,
                "parent_resolution": parent.get("_resolution", "non_rattache"),
                "inconsistencies": inconsistencies,
            },
        }

    def _resolve_parent(
        self,
        code_officiel: str | None,
        source_collectivity_name: str,
        source_territory: str,
        collectivity_indexes: dict[str, dict[Any, dict[str, Any]]],
    ) -> dict[str, Any]:
        if code_officiel and len(code_officiel) >= 6:
            parent_code = code_officiel[:6]
            parent = collectivity_indexes["by_code"].get(parent_code)
            if parent:
                return {**parent, "_resolution": "CODE_GRPT_PREFIX"}

        parent = collectivity_indexes["by_name_territory"].get(
            (self._normalize_key(source_collectivity_name), self._normalize_key(source_territory))
        )
        if parent:
            return {**parent, "_resolution": "COLLECTIV_TERRITOIRE"}
        return {}

    def _build_canonical_entities(self, raw_entities: list[dict[str, Any]], source_name: str) -> list[GroupementCanonicalEntity]:
        entities: list[GroupementCanonicalEntity] = []
        for item in raw_entities:
            canonical_id = "RDC-{zone}-GRPT-{parent}-{name}-{code}".format(
                zone=item["zone_fdsu"] or "INCONNU",
                parent=self._normalize_token(item["collectivite_parent"] or "COLLECTIVITE_INCONNUE"),
                name=self._normalize_token(item["name"]),
                code=item["code_officiel"] or "SANS_CODE",
            )
            quality = self._compute_entity_quality(item)
            entities.append(
                GroupementCanonicalEntity(
                    canonical_id=canonical_id,
                    nom=item["name"],
                    niveau="Groupement",
                    collectivite_parent=item["collectivite_parent"],
                    type_collectivite_parent=item["type_collectivite_parent"],
                    territoire=item["territoire"],
                    province=item["province"],
                    zone_fdsu=item["zone_fdsu"] or "INCONNU",
                    code_officiel=item["code_officiel"],
                    geometry=item["geometry"],
                    source=source_name,
                    statut="official_candidate",
                    qualite=quality,
                    metadata=item["metadata"],
                )
            )
        entities.sort(key=lambda item: (item.zone_fdsu, item.province, item.territoire, item.collectivite_parent, item.nom))
        return entities

    def _build_fact_sheets(self, entities: list[GroupementCanonicalEntity]) -> list[GroupementFactSheet]:
        fact_sheets: list[GroupementFactSheet] = []
        for item in entities:
            flags: list[str] = []
            if not item.collectivite_parent:
                flags.append("missing_collectivity_parent")
            if not item.territoire:
                flags.append("missing_territory")
            if not item.province:
                flags.append("missing_province")
            if not item.zone_fdsu or item.zone_fdsu == "INCONNU":
                flags.append("missing_zone")
            if not self._is_valid_geometry(item.geometry):
                flags.append("invalid_geometry")
            if not item.code_officiel:
                flags.append("missing_code")
            if item.metadata.get("inconsistencies"):
                flags.append("attribute_parent_inconsistency")

            fact_sheets.append(
                GroupementFactSheet(
                    canonical_id=item.canonical_id,
                    nom=item.nom,
                    collectivite_parent=item.collectivite_parent,
                    type_collectivite_parent=item.type_collectivite_parent,
                    territoire=item.territoire,
                    province=item.province,
                    zone_fdsu=item.zone_fdsu,
                    code_officiel=item.code_officiel,
                    geometry_type=(item.geometry or {}).get("type") if item.geometry else None,
                    source=item.source,
                    quality_flags=flags,
                    metadata={
                        "niveau": item.niveau,
                        "statut": item.statut,
                        "qualite": item.qualite,
                        "kmz_path": item.metadata.get("kmz_path", []),
                        "parent_resolution": item.metadata.get("parent_resolution"),
                    },
                )
            )
        return fact_sheets

    def _build_quality_report(self, source_file: str, entities: list[GroupementCanonicalEntity]) -> GroupementQualityReport:
        anomalies: list[GroupementAnomaly] = []
        duplicate_keys = self._duplicate_keys(entities)

        for item in entities:
            if not item.collectivite_parent:
                anomalies.append(self._missing_parent_anomaly(item))
            if not item.territoire:
                anomalies.append(self._anomaly(item, "territoire non determine", "Le groupement n'herite d'aucun territoire parent.", "Verifier le rattachement collectivite et le territoire source."))
            if not item.province:
                anomalies.append(self._anomaly(item, "province non determinee", "Le groupement n'herite d'aucune province.", "Verifier le rattachement collectivite parent."))
            if not item.zone_fdsu or item.zone_fdsu == "INCONNU":
                anomalies.append(self._anomaly(item, "zone FDSU non determinee", "Le groupement n'herite d'aucune zone FDSU.", "Verifier le rattachement collectivite parent."))
            if not self._is_valid_geometry(item.geometry):
                anomalies.append(self._anomaly(item, "geometrie invalide", "Geometrie absente ou coordonnees invalides.", "Controler la geometrie source dans Groupements.kmz."))
            if not item.code_officiel:
                anomalies.append(self._anomaly(item, "code officiel manquant", "Aucun CODE_GRPT ni PCODE exploitable.", "Verifier le code officiel dans ExtendedData."))
            for issue in item.metadata.get("inconsistencies", []):
                anomalies.append(self._anomaly(item, "incoherence attributaire", issue, "Verifier les attributs COLLECTIV/TERRITOIRE face au parent rattache."))

        for key in duplicate_keys:
            for item in [entity for entity in entities if self._dedupe_key(entity) == key]:
                anomalies.append(self._anomaly(item, "doublon referentiel", f"Doublon detecte: {key}", "Verifier les occurrences homonymes dans la meme collectivite."))

        orphan_count = sum(1 for item in entities if not item.collectivite_parent)
        missing_territory_count = sum(1 for item in entities if not item.territoire)
        missing_province_count = sum(1 for item in entities if not item.province)
        missing_zone_count = sum(1 for item in entities if not item.zone_fdsu or item.zone_fdsu == "INCONNU")
        invalid_geometry_count = sum(1 for item in entities if not self._is_valid_geometry(item.geometry))
        missing_code_count = sum(1 for item in entities if not item.code_officiel)
        inconsistency_count = sum(len(item.metadata.get("inconsistencies", [])) for item in entities)
        duplicate_count = len(duplicate_keys)
        attached_count = len(entities) - orphan_count
        validated_count = len([item for item in entities if item.collectivite_parent and item.territoire and item.province and item.zone_fdsu != "INCONNU" and self._is_valid_geometry(item.geometry) and item.code_officiel and not item.metadata.get("inconsistencies")])

        penalties = (
            (orphan_count * 25.0)
            + (missing_territory_count * 20.0)
            + (missing_province_count * 20.0)
            + (missing_zone_count * 20.0)
            + (invalid_geometry_count * 15.0)
            + (missing_code_count * 10.0)
            + (duplicate_count * 15.0)
            + (inconsistency_count * 5.0)
        )
        global_score = round(max(0.0, 100.0 - (penalties / max(len(entities), 1))), 2)

        return GroupementQualityReport(
            source_file=source_file,
            generated_at=datetime.now(timezone.utc),
            groupement_count=len(entities),
            attached_count=attached_count,
            orphan_count=orphan_count,
            missing_territory_count=missing_territory_count,
            missing_province_count=missing_province_count,
            missing_zone_count=missing_zone_count,
            duplicate_count=duplicate_count,
            invalid_geometry_count=invalid_geometry_count,
            missing_code_count=missing_code_count,
            inconsistency_count=inconsistency_count,
            validated_count=validated_count,
            duplicate_keys=duplicate_keys,
            anomalies=anomalies,
            global_score=global_score,
        )

    def _build_collectivity_index(self, entities: list[GroupementCanonicalEntity]) -> dict[str, Any]:
        grouped: dict[tuple[str, str, str, str, str], list[GroupementCanonicalEntity]] = defaultdict(list)
        for item in entities:
            grouped[(item.zone_fdsu, item.province, item.territoire, item.collectivite_parent, item.type_collectivite_parent)].append(item)
        rows = []
        for (zone, province, territory, collectivity, collectivity_type), items in sorted(grouped.items()):
            rows.append(
                {
                    "collectivite_parent": collectivity,
                    "type_collectivite_parent": collectivity_type,
                    "territoire": territory,
                    "province": province,
                    "zone_fdsu": zone,
                    "groupements": [self._index_item(item) for item in sorted(items, key=lambda value: value.nom)],
                    "nombre_groupements": len(items),
                }
            )
        return {"collectivites": rows, "count": len(rows)}

    def _build_territory_index(self, entities: list[GroupementCanonicalEntity]) -> dict[str, Any]:
        grouped: dict[tuple[str, str, str], list[GroupementCanonicalEntity]] = defaultdict(list)
        for item in entities:
            grouped[(item.zone_fdsu, item.province, item.territoire)].append(item)
        rows = []
        for (zone, province, territory), items in sorted(grouped.items()):
            rows.append(
                {
                    "territoire": territory,
                    "province": province,
                    "zone_fdsu": zone,
                    "groupements": [self._index_item(item) for item in sorted(items, key=lambda value: (value.collectivite_parent, value.nom))],
                    "nombre_groupements": len(items),
                }
            )
        return {"territories": rows, "count": len(rows)}

    def _build_province_index(self, entities: list[GroupementCanonicalEntity]) -> dict[str, Any]:
        grouped: dict[tuple[str, str], list[GroupementCanonicalEntity]] = defaultdict(list)
        for item in entities:
            grouped[(item.zone_fdsu, item.province)].append(item)
        rows = []
        for (zone, province), items in sorted(grouped.items()):
            territory_groups: dict[str, list[GroupementCanonicalEntity]] = defaultdict(list)
            for item in items:
                territory_groups[item.territoire].append(item)
            rows.append(
                {
                    "province": province,
                    "zone_fdsu": zone,
                    "territoires": [
                        {
                            "territoire": territory,
                            "groupements": [self._index_item(item) for item in sorted(values, key=lambda value: (value.collectivite_parent, value.nom))],
                            "nombre_groupements": len(values),
                        }
                        for territory, values in sorted(territory_groups.items())
                    ],
                    "nombre_groupements": len(items),
                }
            )
        return {"provinces": rows, "count": len(rows)}

    def _build_national_counter_registry(self, report: GroupementReferentialReport, path: Path) -> dict[str, Any]:
        if path.exists():
            registry = json.loads(path.read_text(encoding="utf-8"))
        else:
            registry = {"registre_national_des_compteurs": {}}
        counters = registry.setdefault("registre_national_des_compteurs", {})
        anomaly_count = len(report.quality.anomalies)
        counters["groupements"] = {
            "nombre": report.quality.groupement_count,
            "valides": report.quality.validated_count,
            "statut": "validé provisoirement" if anomaly_count > 0 else "validé",
        }
        counters["anomalies_groupements"] = {"nombre": anomaly_count}
        registry["generated_at"] = report.generated_at.isoformat(timespec="seconds")
        registry["source_groupements"] = report.source_file
        return registry

    def _index_item(self, item: GroupementCanonicalEntity) -> dict[str, Any]:
        return {
            "nom": item.nom,
            "canonical_id": item.canonical_id,
            "code_officiel": item.code_officiel,
            "collectivite_parent": item.collectivite_parent,
        }

    def _check_inconsistencies(self, source_collectivity_name: str, source_territory: str, parent: dict[str, Any]) -> list[str]:
        if not parent:
            return []
        issues: list[str] = []
        if source_collectivity_name and self._normalize_key(source_collectivity_name) != self._normalize_key(parent.get("nom", "")):
            issues.append(
                f"COLLECTIV='{source_collectivity_name}' different de la collectivite rattachee '{parent.get('nom', '')}'"
            )
        if source_territory and self._normalize_key(source_territory) != self._normalize_key(parent.get("territoire", "")):
            issues.append(
                f"TERRITOIRE='{source_territory}' different du territoire herite '{parent.get('territoire', '')}'"
            )
        return issues

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

        polygon = placemark.find("kml:Polygon", KML_NAMESPACE)
        if polygon is not None:
            coords = self._extract_coordinates(polygon)
            return {"type": "Polygon", "coordinates": [coords]} if coords else {"type": "Polygon", "coordinates": []}

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
        if geometry.get("type") == "Point":
            coords = geometry.get("coordinates") or []
            return len(coords) >= 2 and isinstance(coords[0], (int, float)) and isinstance(coords[1], (int, float))
        if geometry.get("type") == "Polygon":
            rings = geometry.get("coordinates") or []
            return bool(rings and len(rings[0]) >= 4)
        if geometry.get("type") == "LineString":
            return len(geometry.get("coordinates") or []) >= 2
        return False

    def _compute_entity_quality(self, item: dict[str, Any]) -> float:
        score = 100.0
        if not item["collectivite_parent"]:
            score -= 25.0
        if not item["territoire"]:
            score -= 20.0
        if not item["province"]:
            score -= 20.0
        if not item["zone_fdsu"] or item["zone_fdsu"] == "INCONNU":
            score -= 20.0
        if not self._is_valid_geometry(item["geometry"]):
            score -= 15.0
        if not item["code_officiel"]:
            score -= 10.0
        if item["metadata"].get("inconsistencies"):
            score -= min(20.0, 5.0 * len(item["metadata"]["inconsistencies"]))
        return round(max(0.0, score), 2)

    def _duplicate_keys(self, entities: list[GroupementCanonicalEntity]) -> list[str]:
        counter = Counter(self._dedupe_key(item) for item in entities)
        return sorted(key for key, count in counter.items() if count > 1)

    def _dedupe_key(self, item: GroupementCanonicalEntity) -> str:
        return "|".join(
            [
                self._normalize_token(item.province),
                self._normalize_token(item.territoire),
                self._normalize_token(item.collectivite_parent),
                self._normalize_token(item.nom),
                item.code_officiel or "",
            ]
        )

    def _missing_parent_anomaly(self, item: GroupementCanonicalEntity) -> GroupementAnomaly:
        if item.nom == "Bena muhona" and item.code_officiel == "70650801":
            return GroupementAnomaly(
                entite="Bena muhona",
                type="Groupement",
                code="70650801",
                province=item.province,
                territoire=item.territoire,
                collectivite_parent=item.collectivite_parent,
                probleme="collectivité parente non déterminée",
                cause="préfixe CODE_GRPT sans correspondance dans les collectivités officielles générées",
                statut="À valider manuellement",
                suggestion="vérifier le rattachement officiel collectivité/territoire avant publication",
            )
        return self._anomaly(
            item,
            "collectivite parente non determinee",
            "Aucun rattachement fiable par code parent ni par attribut COLLECTIV/TERRITOIRE.",
            "Verifier la collectivite officielle de rattachement avant publication.",
        )

    def _anomaly(self, item: GroupementCanonicalEntity, probleme: str, cause: str, suggestion: str) -> GroupementAnomaly:
        return GroupementAnomaly(
            entite=item.nom,
            type="Groupement",
            code=item.code_officiel,
            province=item.province,
            territoire=item.territoire,
            collectivite_parent=item.collectivite_parent,
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

    def _normalize_key(self, value: str) -> str:
        normalized = unicodedata.normalize("NFKD", value or "")
        ascii_text = "".join(ch for ch in normalized if not unicodedata.combining(ch))
        ascii_text = ascii_text.replace("-", " ").replace("_", " ")
        return re.sub(r"\s+", " ", ascii_text).strip().upper()

    def _normalize_token(self, value: str) -> str:
        token = self._normalize_key(value).replace(" ", "_")
        token = "".join(ch for ch in token if ch.isalnum() or ch == "_")
        return token or "INCONNU"
