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


class LocalityOfficialReferentialService:
    """Builds the official locality referential from Localites.kmz only."""

    TYPE_CODE_MAP = {
        "0": "Village",
        "4": "Cité",
        "5": "Quartier",
        "6": "Localité",
        "7": "Camp",
        "8": "Village",
        "9": "Localité",
    }

    FUTURE_PROFILE = {
        "population": None,
        "ecoles": [],
        "centres_de_sante": [],
        "couverture_reseau": None,
        "sites_fdsu": [],
        "activites_economiques": [],
        "energie": None,
        "photos": [],
        "rapports_de_mission": [],
        "indicateurs_caid": {},
    }

    def __init__(self) -> None:
        self.reader = KMZReader()
        self.description_parser = DescriptionParser()

    def run(
        self,
        source_path: str | Path,
        output_dir: str | Path = Path("data/reports/locality_official"),
        groupement_referential_path: str | Path = Path("data/reports/groupement_official/groupement_referential_official.json"),
        collectivity_referential_path: str | Path = Path("data/reports/collectivity_official/collectivity_referential_official.json"),
        registry_path: str | Path = Path("data/reports/national_counter_registry.json"),
    ) -> dict[str, Any]:
        source = Path(source_path)
        output = Path(output_dir)
        generated_at = datetime.now(timezone.utc)

        parents = self._load_parent_indexes(groupement_referential_path, collectivity_referential_path)
        document = self.reader.read(source)
        root = ET.fromstring(document.kml_text)
        raw_entities = self._extract_localities(root, source.name, parents)
        referential = self._build_canonical_entities(raw_entities, source.name)
        fact_sheets = self._build_fact_sheets(referential)
        indexes = {
            "groupement_locality_index": self._build_groupement_index(referential),
            "collectivity_locality_index": self._build_collectivity_index(referential),
            "territory_locality_index": self._build_territory_index(referential),
            "province_locality_index": self._build_province_index(referential),
        }
        quality = self._build_quality(source.name, referential, generated_at)
        report = {
            "source_file": source.name,
            "generated_at": generated_at.isoformat(timespec="seconds"),
            "locality_referential": referential,
            "locality_fact_sheets": fact_sheets,
            **indexes,
            "quality": quality,
            "conclusion": self._build_conclusion(quality),
        }

        paths = {
            "referential": output / "locality_referential_official.json",
            "fact_sheets": output / "locality_fact_sheets.json",
            "quality": output / "locality_quality_report.json",
            "markdown": output / "locality_referential_report.md",
            "files": output / "locality_files_report.json",
            "groupement_index": output / "groupement_locality_index.json",
            "collectivity_index": output / "collectivity_locality_index.json",
            "territory_index": output / "territory_locality_index.json",
            "province_index": output / "province_locality_index.json",
            "registry": Path(registry_path),
        }
        self._write_json(report, paths["referential"])
        self._write_json({"locality_fact_sheets": fact_sheets, "count": len(fact_sheets)}, paths["fact_sheets"])
        self._write_json(quality, paths["quality"])
        self._write_text(self._to_markdown(report), paths["markdown"])
        self._write_json(indexes["groupement_locality_index"], paths["groupement_index"])
        self._write_json(indexes["collectivity_locality_index"], paths["collectivity_index"])
        self._write_json(indexes["territory_locality_index"], paths["territory_index"])
        self._write_json(indexes["province_locality_index"], paths["province_index"])
        self._write_json(self._update_registry(report, paths["registry"]), paths["registry"])
        created_files = [str(path) for path in paths.values()]
        self._write_json({"source": source.name, "created_files": created_files, "generated_at": report["generated_at"]}, paths["files"])
        return {"source_path": source, "report": report, "quality": quality, "created_files": created_files}

    def _load_parent_indexes(self, groupement_path: str | Path, collectivity_path: str | Path) -> dict[str, Any]:
        groupements = json.loads(Path(groupement_path).read_text(encoding="utf-8")).get("groupement_referential", [])
        collectivities = json.loads(Path(collectivity_path).read_text(encoding="utf-8")).get("collectivity_referential", [])
        by_groupement_code = {}
        by_groupement_name = {}
        for item in groupements:
            code = self._clean_code(item.get("code_officiel"))
            if code:
                by_groupement_code[code] = item
            key = (
                self._normalize_key(item.get("nom", "")),
                self._normalize_key(item.get("collectivite_parent", "")),
                self._normalize_key(item.get("territoire", "")),
            )
            by_groupement_name[key] = item

        by_collectivity_code = {}
        by_collectivity_name = {}
        by_territory = {}
        for item in collectivities:
            code = self._clean_code(item.get("code_officiel"))
            if code:
                by_collectivity_code[code] = item
            by_collectivity_name[(self._normalize_key(item.get("nom", "")), self._normalize_key(item.get("territoire", "")))] = item
            by_territory.setdefault(self._normalize_key(item.get("territoire", "")), item)
        return {
            "groupement_code": by_groupement_code,
            "groupement_name": by_groupement_name,
            "collectivity_code": by_collectivity_code,
            "collectivity_name": by_collectivity_name,
            "territory": by_territory,
        }

    def _extract_localities(self, root: ET.Element, source_name: str, parents: dict[str, Any]) -> list[dict[str, Any]]:
        entities: list[dict[str, Any]] = []

        def walk(node: ET.Element, path: list[str]) -> None:
            tag = node.tag.split("}")[-1]
            current_path = list(path)
            if tag in {"Document", "Folder"}:
                name = (node.findtext("kml:name", default="", namespaces=KML_NAMESPACE) or "").strip()
                if name:
                    current_path.append(name)
            if tag == "Placemark":
                entity = self._placemark_to_locality(node, current_path, source_name, parents)
                if entity:
                    entities.append(entity)
                return
            for child in list(node):
                walk(child, current_path)

        walk(root, [])
        return entities

    def _placemark_to_locality(
        self,
        placemark: ET.Element,
        path: list[str],
        source_name: str,
        parents: dict[str, Any],
    ) -> dict[str, Any] | None:
        extended_data = self._extract_extended_data(placemark)
        name = (extended_data.get("NOM1") or extended_data.get("NOM2") or placemark.findtext("kml:name", default="", namespaces=KML_NAMESPACE) or "").strip()
        if not name:
            return None
        description = (placemark.findtext("kml:description", default="", namespaces=KML_NAMESPACE) or "").strip()
        description_values = self.description_parser.parse(description)
        geometry = self._extract_geometry(placemark)
        source_type = (extended_data.get("TYPE") or "").strip()
        type_localite, type_reason = self._classify_type(source_type, name, extended_data, description, path)
        parent = self._resolve_parent(extended_data, parents)
        style_url = (placemark.findtext("kml:styleUrl", default="", namespaces=KML_NAMESPACE) or "").strip()
        return {
            "name": name,
            "type_localite": type_localite,
            "groupement": parent.get("groupement", ""),
            "collectivite": parent.get("collectivite", ""),
            "territoire": parent.get("territoire", extended_data.get("TERRITOIRE", "")),
            "province": parent.get("province", ""),
            "zone_fdsu": parent.get("zone_fdsu", ""),
            "geometry": geometry,
            "code_officiel": self._clean_code(extended_data.get("PCODE")) or self._clean_code(extended_data.get("CODE_INS")),
            "metadata": {
                "kmz_path": [*path, name],
                "description": description,
                "description_values": description_values,
                "extended_data": extended_data,
                "styles": {"style_url": style_url},
                "source_file": source_name,
                "coordinates_source": {"longitude": extended_data.get("LONGITUDE", ""), "latitude": extended_data.get("LATITUDE", "")},
                "source_type_code": source_type,
                "type_classification": type_reason,
                "parent_resolution": parent.get("resolution", "non_rattache"),
                "best_parent_level": parent.get("best_parent_level", "Aucun"),
            },
        }

    def _resolve_parent(self, data: dict[str, str], parents: dict[str, Any]) -> dict[str, str]:
        code_grpt = self._clean_code(data.get("CODE_GRPT"))
        if code_grpt and code_grpt != "0" and code_grpt in parents["groupement_code"]:
            item = parents["groupement_code"][code_grpt]
            return self._parent_from_groupement(item, "CODE_GRPT")
        key = (self._normalize_key(data.get("GROUPEMENT", "")), self._normalize_key(data.get("COLLECTIV", "")), self._normalize_key(data.get("TERRITOIRE", "")))
        if key in parents["groupement_name"]:
            return self._parent_from_groupement(parents["groupement_name"][key], "GROUPEMENT_COLLECTIV_TERRITOIRE")

        pcode = self._clean_code(data.get("PCODE"))
        if pcode and len(pcode) >= 6 and pcode[:6] in parents["collectivity_code"]:
            item = parents["collectivity_code"][pcode[:6]]
            return self._parent_from_collectivity(item, "PCODE_PREFIX_COLLECTIVITE")
        ckey = (self._normalize_key(data.get("COLLECTIV", "")), self._normalize_key(data.get("TERRITOIRE", "")))
        if ckey in parents["collectivity_name"]:
            return self._parent_from_collectivity(parents["collectivity_name"][ckey], "COLLECTIV_TERRITOIRE")
        tkey = self._normalize_key(data.get("TERRITOIRE", ""))
        if tkey in parents["territory"]:
            item = parents["territory"][tkey]
            return {
                "groupement": "",
                "collectivite": "",
                "territoire": item.get("territoire", data.get("TERRITOIRE", "")),
                "province": item.get("province", ""),
                "zone_fdsu": item.get("zone_fdsu", ""),
                "resolution": "TERRITOIRE_SOURCE",
                "best_parent_level": "Territoire",
            }
        return {}

    def _parent_from_groupement(self, item: dict[str, Any], resolution: str) -> dict[str, str]:
        return {
            "groupement": item.get("nom", ""),
            "collectivite": item.get("collectivite_parent", ""),
            "territoire": item.get("territoire", ""),
            "province": item.get("province", ""),
            "zone_fdsu": item.get("zone_fdsu", ""),
            "resolution": resolution,
            "best_parent_level": "Groupement",
        }

    def _parent_from_collectivity(self, item: dict[str, Any], resolution: str) -> dict[str, str]:
        return {
            "groupement": "",
            "collectivite": item.get("nom", ""),
            "territoire": item.get("territoire", ""),
            "province": item.get("province", ""),
            "zone_fdsu": item.get("zone_fdsu", ""),
            "resolution": resolution,
            "best_parent_level": "Collectivité",
        }

    def _build_canonical_entities(self, raw_entities: list[dict[str, Any]], source_name: str) -> list[dict[str, Any]]:
        entities = []
        for item in raw_entities:
            canonical_id = "RDC-{zone}-LOC-{territory}-{parent}-{name}-{code}".format(
                zone=item["zone_fdsu"] or "INCONNU",
                territory=self._normalize_token(item["territoire"] or "TERRITOIRE_INCONNU"),
                parent=self._normalize_token(item["groupement"] or item["collectivite"] or "PARENT_INCONNU"),
                name=self._normalize_token(item["name"]),
                code=item["code_officiel"] or "SANS_CODE",
            )
            entity = {
                "canonical_id": canonical_id,
                "nom": item["name"],
                "niveau": "Localité",
                "type_localite": item["type_localite"],
                "groupement": item["groupement"],
                "collectivité": item["collectivite"],
                "territoire": item["territoire"],
                "province": item["province"],
                "zone_fdsu": item["zone_fdsu"] or "INCONNU",
                "geometry": item["geometry"],
                "source": source_name,
                "statut": "official_candidate",
                "qualité": self._compute_entity_quality(item),
                "metadata": item["metadata"],
                "future_profile": dict(self.FUTURE_PROFILE),
            }
            entities.append(entity)
        entities.sort(key=lambda x: (x["zone_fdsu"], x["province"], x["territoire"], x["collectivité"], x["groupement"], x["nom"]))
        return entities

    def _build_fact_sheets(self, entities: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [
            {
                "canonical_id": item["canonical_id"],
                "nom": item["nom"],
                "type_localite": item["type_localite"],
                "groupement": item["groupement"],
                "collectivité": item["collectivité"],
                "territoire": item["territoire"],
                "province": item["province"],
                "zone_fdsu": item["zone_fdsu"],
                "geometry_type": (item["geometry"] or {}).get("type") if item.get("geometry") else None,
                "source": item["source"],
                "quality_flags": self._quality_flags(item),
                "metadata": {
                    "statut": item["statut"],
                    "qualité": item["qualité"],
                    "kmz_path": item["metadata"].get("kmz_path", []),
                    "parent_resolution": item["metadata"].get("parent_resolution"),
                    "best_parent_level": item["metadata"].get("best_parent_level"),
                },
            }
            for item in entities
        ]

    def _build_quality(self, source_file: str, entities: list[dict[str, Any]], generated_at: datetime) -> dict[str, Any]:
        duplicate_keys = self._duplicate_keys(entities)
        anomalies = []
        for item in entities:
            for flag in self._quality_flags(item):
                anomalies.append(
                    {
                        "entite": item["nom"],
                        "type": item["type_localite"],
                        "province": item["province"],
                        "territoire": item["territoire"],
                        "collectivité": item["collectivité"],
                        "groupement": item["groupement"],
                        "probleme": flag,
                        "parent_resolution": item["metadata"].get("parent_resolution"),
                        "suggestion": "Verifier les attributs source Localites.kmz et le rattachement parent.",
                    }
                )
        for key in duplicate_keys:
            anomalies.append({"entite": key, "type": "doublon", "probleme": "doublon referentiel", "suggestion": "Verifier les localites homonymes/code identique."})

        type_distribution = dict(sorted(Counter(item["type_localite"] for item in entities).items()))
        orphan_count = sum(1 for item in entities if item["metadata"].get("best_parent_level") == "Aucun")
        impossible_attachment_count = sum(1 for item in entities if not item["province"] or item["zone_fdsu"] == "INCONNU")
        invalid_geometry_count = sum(1 for item in entities if not self._is_valid_geometry(item.get("geometry")))
        missing_coordinates_count = sum(1 for item in entities if self._missing_coordinates(item))
        unknown_type_count = type_distribution.get("Autre", 0)
        duplicate_count = len(duplicate_keys)
        attached_groupement = sum(1 for item in entities if item["metadata"].get("best_parent_level") == "Groupement")
        attached_collectivity = sum(1 for item in entities if item["metadata"].get("best_parent_level") == "Collectivité")
        attached_territory = sum(1 for item in entities if item["metadata"].get("best_parent_level") == "Territoire")
        penalties = (
            orphan_count * 25.0
            + impossible_attachment_count * 20.0
            + invalid_geometry_count * 15.0
            + missing_coordinates_count * 15.0
            + unknown_type_count * 8.0
            + duplicate_count * 10.0
        )
        return {
            "source_file": source_file,
            "generated_at": generated_at.isoformat(timespec="seconds"),
            "locality_count": len(entities),
            "type_distribution": type_distribution,
            "attached_groupement_count": attached_groupement,
            "attached_collectivity_count": attached_collectivity,
            "attached_territory_count": attached_territory,
            "orphan_count": orphan_count,
            "duplicate_count": duplicate_count,
            "invalid_geometry_count": invalid_geometry_count,
            "missing_coordinates_count": missing_coordinates_count,
            "unknown_type_count": unknown_type_count,
            "impossible_attachment_count": impossible_attachment_count,
            "coverage_nationale": self._coverage(entities),
            "duplicate_keys": duplicate_keys,
            "anomalies": anomalies,
            "global_score": round(max(0.0, 100.0 - penalties / max(len(entities), 1)), 2),
        }

    def _build_groupement_index(self, entities: list[dict[str, Any]]) -> dict[str, Any]:
        return self._group_index(entities, ["zone_fdsu", "province", "territoire", "collectivité", "groupement"], "groupements")

    def _build_collectivity_index(self, entities: list[dict[str, Any]]) -> dict[str, Any]:
        return self._group_index(entities, ["zone_fdsu", "province", "territoire", "collectivité"], "collectivites")

    def _build_territory_index(self, entities: list[dict[str, Any]]) -> dict[str, Any]:
        return self._group_index(entities, ["zone_fdsu", "province", "territoire"], "territories")

    def _build_province_index(self, entities: list[dict[str, Any]]) -> dict[str, Any]:
        return self._group_index(entities, ["zone_fdsu", "province"], "provinces")

    def _group_index(self, entities: list[dict[str, Any]], keys: list[str], label: str) -> dict[str, Any]:
        grouped: dict[tuple[str, ...], list[dict[str, Any]]] = defaultdict(list)
        for item in entities:
            grouped[tuple(item[key] for key in keys)].append(item)
        rows = []
        for values, items in sorted(grouped.items()):
            row = dict(zip(keys, values))
            row["localites"] = [self._index_item(item) for item in sorted(items, key=lambda x: x["nom"])]
            row["nombre_localites"] = len(items)
            rows.append(row)
        return {label: rows, "count": len(rows)}

    def _index_item(self, item: dict[str, Any]) -> dict[str, Any]:
        return {"nom": item["nom"], "canonical_id": item["canonical_id"], "type_localite": item["type_localite"]}

    def _classify_type(self, source_type: str, name: str, data: dict[str, str], description: str, path: list[str]) -> tuple[str, str]:
        haystack = self._normalize_key(" ".join([name, description, " ".join(path), *data.values()]))
        if "quartier" in haystack:
            return "Quartier", "mot-cle quartier"
        if "camp" in haystack:
            return "Camp", "mot-cle camp"
        if "cite" in haystack:
            return "Cité", "mot-cle cite"
        if "village" in haystack:
            return "Village", "mot-cle village"
        if source_type in self.TYPE_CODE_MAP:
            return self.TYPE_CODE_MAP[source_type], f"code TYPE={source_type}"
        if source_type and all(char in self.TYPE_CODE_MAP for char in source_type):
            priority = ["Cité", "Quartier", "Camp", "Localité", "Village"]
            labels = {self.TYPE_CODE_MAP[char] for char in source_type}
            for label in priority:
                if label in labels:
                    return label, f"code TYPE composite={source_type}"
        return "Autre", f"code TYPE non documente={source_type or 'vide'}"

    def _quality_flags(self, item: dict[str, Any]) -> list[str]:
        flags = []
        if item["metadata"].get("best_parent_level") == "Aucun":
            flags.append("localite_orpheline")
        if not item["province"] or item["zone_fdsu"] == "INCONNU":
            flags.append("rattachement_impossible")
        if not self._is_valid_geometry(item.get("geometry")):
            flags.append("geometrie_invalide")
        if self._missing_coordinates(item):
            flags.append("coordonnees_manquantes")
        if item["type_localite"] == "Autre":
            flags.append("type_inconnu")
        return flags

    def _extract_extended_data(self, placemark: ET.Element) -> dict[str, str]:
        data = {}
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
        if point is None:
            return None
        coords = (point.findtext(".//kml:coordinates", default="", namespaces=KML_NAMESPACE) or "").strip().split()
        if not coords:
            return {"type": "Point", "coordinates": []}
        parts = [part for part in coords[0].split(",") if part]
        if len(parts) < 2:
            return {"type": "Point", "coordinates": []}
        out = [float(parts[0]), float(parts[1])]
        if len(parts) > 2:
            out.append(float(parts[2]))
        return {"type": "Point", "coordinates": out}

    def _is_valid_geometry(self, geometry: dict[str, Any] | None) -> bool:
        if not geometry or geometry.get("type") != "Point":
            return False
        coords = geometry.get("coordinates") or []
        return len(coords) >= 2 and isinstance(coords[0], (int, float)) and isinstance(coords[1], (int, float))

    def _missing_coordinates(self, item: dict[str, Any]) -> bool:
        coords = (item.get("geometry") or {}).get("coordinates") or []
        return len(coords) < 2

    def _compute_entity_quality(self, item: dict[str, Any]) -> float:
        score = 100.0
        if item["metadata"].get("best_parent_level") == "Aucun":
            score -= 25.0
        if not item["province"] or not item["zone_fdsu"]:
            score -= 20.0
        if not self._is_valid_geometry(item.get("geometry")):
            score -= 15.0
        if item["type_localite"] == "Autre":
            score -= 8.0
        return round(max(0.0, score), 2)

    def _duplicate_keys(self, entities: list[dict[str, Any]]) -> list[str]:
        counter = Counter(
            "|".join(
                [
                    self._normalize_token(item["province"]),
                    self._normalize_token(item["territoire"]),
                    self._normalize_token(item["collectivité"]),
                    self._normalize_token(item["groupement"]),
                    self._normalize_token(item["nom"]),
                ]
            )
            for item in entities
        )
        return sorted(key for key, count in counter.items() if count > 1)

    def _coverage(self, entities: list[dict[str, Any]]) -> dict[str, Any]:
        provinces = {item["province"] for item in entities if item["province"]}
        territories = {item["territoire"] for item in entities if item["territoire"]}
        collectivities = {(item["territoire"], item["collectivité"]) for item in entities if item["collectivité"]}
        groupements = {(item["collectivité"], item["groupement"]) for item in entities if item["groupement"]}
        return {
            "provinces_couvertes": len(provinces),
            "territoires_couverts": len(territories),
            "collectivites_couvertes": len(collectivities),
            "groupements_couverts": len(groupements),
            "reference_nationale_localites": None,
            "comparaison_reference": "reference nationale localites non disponible dans le registre",
        }

    def _build_conclusion(self, quality: dict[str, Any]) -> dict[str, str]:
        statut = "partiel"
        if quality["orphan_count"] == 0 and quality["unknown_type_count"] == 0 and quality["coverage_nationale"]["reference_nationale_localites"]:
            statut = "complet"
        return {
            "statut": statut,
            "motif": "Reference nationale localites absente et rattachements groupements limites par la source groupements partielle.",
            "publication": "non publié",
        }

    def _update_registry(self, report: dict[str, Any], path: Path) -> dict[str, Any]:
        registry = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {"registre_national_des_compteurs": {}}
        counters = registry.setdefault("registre_national_des_compteurs", {})
        q = report["quality"]
        counters["localites"] = {
            "nombre": q["locality_count"],
            "repartition_par_type": q["type_distribution"],
            "statut": report["conclusion"]["statut"],
            "validation": "non publié",
            "score_qualite": q["global_score"],
            "reference_nationale": None,
            "comparaison_reference": q["coverage_nationale"]["comparaison_reference"],
            "anomalies": len(q["anomalies"]),
        }
        counters["anomalies_localites"] = {
            "nombre": len(q["anomalies"]),
            "orphelins": q["orphan_count"],
            "types_inconnus": q["unknown_type_count"],
            "rattachements_impossibles": q["impossible_attachment_count"],
        }
        registry["generated_at"] = report["generated_at"]
        registry["source_localites"] = report["source_file"]
        return registry

    def _to_markdown(self, report: dict[str, Any]) -> str:
        q = report["quality"]
        lines = [
            "# Referentiel Officiel des Localites",
            "",
            f"- Source: {report['source_file']}",
            f"- Date: {report['generated_at']}",
            f"- Localites: {q['locality_count']}",
            f"- Score global: {q['global_score']}",
            f"- Conclusion: referentiel {report['conclusion']['statut']}",
            "",
            "## Repartition par type",
            "",
        ]
        lines.extend(f"- {key}: {value}" for key, value in q["type_distribution"].items())
        lines.extend(
            [
                "",
                "## Couverture nationale",
                "",
                f"- Provinces couvertes: {q['coverage_nationale']['provinces_couvertes']}",
                f"- Territoires couverts: {q['coverage_nationale']['territoires_couverts']}",
                f"- Collectivites couvertes: {q['coverage_nationale']['collectivites_couvertes']}",
                f"- Groupements couverts: {q['coverage_nationale']['groupements_couverts']}",
                f"- Reference nationale: {q['coverage_nationale']['comparaison_reference']}",
                "",
                "## Anomalies",
                "",
                f"- Localites orphelines: {q['orphan_count']}",
                f"- Doublons: {q['duplicate_count']}",
                f"- Geometries invalides: {q['invalid_geometry_count']}",
                f"- Coordonnees manquantes: {q['missing_coordinates_count']}",
                f"- Types inconnus: {q['unknown_type_count']}",
                f"- Rattachements impossibles: {q['impossible_attachment_count']}",
                "",
                "## Typage automatique",
                "",
                "- Les codes TYPE numeriques de Localites.kmz ne sont pas libelles dans la source.",
                "- Mapping applique: 0/8=Village, 4=Cite, 5=Quartier, 6/9=Localite, 7=Camp.",
                "- Les codes composites et codes non documentes sont conserves dans metadata.source_type_code.",
            ]
        )
        return "\n".join(lines)

    def _write_json(self, data: dict[str, Any], path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def _write_text(self, data: str, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(data, encoding="utf-8")

    def _clean_code(self, value: Any) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        if not text:
            return None
        if "." in text:
            text = text.split(".", 1)[0]
        text = re.sub(r"\D", "", text)
        return text or None

    def _normalize_key(self, value: Any) -> str:
        text = unicodedata.normalize("NFKD", str(value or "")).encode("ascii", "ignore").decode("ascii")
        return re.sub(r"\s+", " ", text).strip().lower()

    def _normalize_token(self, value: Any) -> str:
        text = unicodedata.normalize("NFKD", str(value or "")).encode("ascii", "ignore").decode("ascii")
        text = re.sub(r"[^A-Za-z0-9]+", "_", text).strip("_").upper()
        return text or "INCONNU"
