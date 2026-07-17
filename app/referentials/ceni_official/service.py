from __future__ import annotations

import hashlib
import json
import math
import re
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
from xml.etree import ElementTree as ET
from zipfile import ZipFile

from api.services.national_semantic_classification_engine import default_engine

from .models import CeniAsset, CeniCategory

ROOT = Path(__file__).resolve().parents[3]
SOURCE_PATH = ROOT / "data" / "raw" / "ceni" / "KMZ File Sites CENI.kmz"
REPORT_DIR = ROOT / "data" / "reports" / "ceni_official"
REGISTRY_PATH = REPORT_DIR / "ceni_registry_v1.json"
AUDIT_PATH = REPORT_DIR / "ceni_kmz_audit_v1.json"
ANOMALY_PATH = REPORT_DIR / "ceni_anomalies_v1.json"
BATCH_PATH = REPORT_DIR / "ceni_import_batches_v1.json"
PROVINCES_PATH = ROOT / "data" / "reports" / "province_official" / "province_referential_official.json"
COLLECTIVITIES_PATH = ROOT / "data" / "reports" / "collectivity_official" / "collectivity_referential_official.json"
KML_NS = {"k": "http://www.opengis.net/kml/2.2"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest().upper()


def _normalize(value: Any) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(ch for ch in text if not unicodedata.combining(ch)).upper()
    return re.sub(r"[^A-Z0-9]+", " ", text).strip()


def _rings(geometry: dict[str, Any]) -> Iterable[list[list[float]]]:
    coords = geometry.get("coordinates") or []
    if geometry.get("type") == "Polygon":
        for ring in coords:
            yield ring
    elif geometry.get("type") == "MultiPolygon":
        for polygon in coords:
            for ring in polygon:
                yield ring


def _bbox(geometry: dict[str, Any]) -> tuple[float, float, float, float]:
    points = [(float(p[0]), float(p[1])) for ring in _rings(geometry) for p in ring if len(p) >= 2]
    if not points:
        return (math.inf, math.inf, -math.inf, -math.inf)
    xs, ys = zip(*points)
    return min(xs), min(ys), max(xs), max(ys)


def _point_in_ring(x: float, y: float, ring: list[list[float]]) -> bool:
    inside = False
    j = len(ring) - 1
    for i in range(len(ring)):
        xi, yi = float(ring[i][0]), float(ring[i][1])
        xj, yj = float(ring[j][0]), float(ring[j][1])
        if (yi > y) != (yj > y):
            cross = (xj - xi) * (y - yi) / ((yj - yi) or 1e-15) + xi
            if x < cross:
                inside = not inside
        j = i
    return inside


def _contains(geometry: dict[str, Any], x: float, y: float) -> bool:
    return any(_point_in_ring(x, y, ring) for ring in _rings(geometry))


def classify(name: str) -> tuple[str, str, float]:
    """Compatibilité historique; le moteur transversal reste la source métier."""
    result = default_engine().classify(name)
    return result.normalized_category_code, result.justification_fr, result.confidence


def apply_duplicate_analysis(rows: list[dict[str, Any]]) -> None:
    """Classe les ressemblances sans fusion ni suppression automatique."""
    groups: list[tuple[str, defaultdict[str, list[dict[str, Any]]]]] = []
    exact: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
    same_geometry: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
    probable: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
    same_name: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        exact[row["fingerprint"]].append(row)
        lon, lat = row.get("longitude"), row.get("latitude")
        if lon is not None and lat is not None:
            same_geometry[f"{float(lon):.6f}|{float(lat):.6f}"].append(row)
            probable[f"{_normalize(row.get('name'))}|{float(lon):.3f}|{float(lat):.3f}"].append(row)
        same_name[_normalize(row.get("name"))].append(row)
    groups.extend((("exact", exact), ("same_geometry", same_geometry), ("probable", probable), ("same_name", same_name)))
    assigned: set[str] = set()
    for status, index in groups:
        for key, group in index.items():
            if not key or len(group) < 2:
                continue
            eligible = [row for row in group if row["asset_uid"] not in assigned]
            if len(eligible) < 2:
                continue
            ids = [row["asset_uid"] for row in eligible]
            categories = {row["normalized_category"] for row in eligible}
            names = {_normalize(row.get("name")) for row in eligible}
            for row in eligible:
                row["duplicate"] = {
                    "status": status,
                    "group_size": len(eligible),
                    "related_asset_uids": [uid for uid in ids if uid != row["asset_uid"]],
                    "same_infrastructure_multiple_functions": len(categories) > 1 or (status == "same_geometry" and len(names) > 1),
                    "automatic_action": "none",
                }
                assigned.add(row["asset_uid"])
    for row in rows:
        if row["asset_uid"] not in assigned:
            row["duplicate"] = {"status": "none", "group_size": 1, "related_asset_uids": [], "same_infrastructure_multiple_functions": False, "automatic_action": "none"}


class CeniRegistryService:
    def __init__(self, source_path: Path = SOURCE_PATH) -> None:
        self.source_path = Path(source_path)
        self.source_hash = hashlib.sha256(self.source_path.read_bytes()).hexdigest().upper()
        self.source_size = self.source_path.stat().st_size

    def _kml(self) -> tuple[str, bytes, ET.Element]:
        with ZipFile(self.source_path) as archive:
            names = [name for name in archive.namelist() if name.lower().endswith(".kml")]
            if len(names) != 1:
                raise ValueError(f"Un fichier KML unique est attendu, obtenu: {names}")
            raw = archive.read(names[0])
        return names[0], raw, ET.fromstring(raw)

    def audit(self) -> dict[str, Any]:
        member, raw, root = self._kml()
        placemarks = root.findall(".//k:Placemark", KML_NS)
        fields = Counter()
        geometries = Counter()
        names = Counter()
        folders = root.findall(".//k:Folder", KML_NS)
        for placemark in placemarks:
            names[placemark.findtext("k:name", default="", namespaces=KML_NS).strip()] += 1
            for simple in placemark.findall(".//k:SimpleData", KML_NS):
                fields[simple.attrib.get("name", "")] += 1
            for geometry in ("Point", "LineString", "Polygon", "MultiGeometry"):
                if placemark.find(f".//k:{geometry}", KML_NS) is not None:
                    geometries[geometry] += 1
        schemas = []
        for schema in root.findall(".//k:Schema", KML_NS):
            schemas.append({
                "id": schema.attrib.get("id"),
                "name": schema.attrib.get("name"),
                "fields": [{"name": f.attrib.get("name"), "type": f.attrib.get("type")} for f in schema.findall("k:SimpleField", KML_NS)],
            })
        return {
            "_meta": {"version": "ceni-kmz-audit-1.0.0", "generated_at": _now(), "data_first": True},
            "source": {"path": str(self.source_path.relative_to(ROOT)).replace("\\", "/"), "sha256": self.source_hash, "size_bytes": self.source_size, "kml_member": member, "kml_size_bytes": len(raw), "encoding": "UTF-8"},
            "structure": {"placemarks": len(placemarks), "folders": len(folders), "styles": len(root.findall(".//k:Style", KML_NS)), "style_maps": len(root.findall(".//k:StyleMap", KML_NS)), "schemas": schemas, "geometries": dict(geometries), "extended_data_fields": dict(fields), "descriptions": len(root.findall(".//k:description", KML_NS))},
            "names": {"non_empty": sum(v for k, v in names.items() if k), "empty": names.get("", 0), "distinct": len([k for k in names if k]), "repeated_name_values": sum(1 for k, v in names.items() if k and v > 1), "most_common": names.most_common(25)},
            "limitations": ["Aucun code administratif dans le schéma.", "Aucune catégorie source explicite.", "Aucune description de Placemark.", "La nature institutionnelle ne peut pas être déduite automatiquement de la seule présence dans le KMZ."],
        }

    def _admin_polygons(self) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        province_doc = json.loads(PROVINCES_PATH.read_text(encoding="utf-8"))
        collectivity_doc = json.loads(COLLECTIVITIES_PATH.read_text(encoding="utf-8"))
        provinces = province_doc["province_referential"]
        collectivities = collectivity_doc["collectivity_referential"]
        for item in provinces + collectivities:
            item["_bbox"] = _bbox(item.get("geometry") or {})
        return provinces, collectivities

    @staticmethod
    def _attach(x: float | None, y: float | None, provinces: list[dict[str, Any]], collectivities: list[dict[str, Any]]) -> dict[str, Any]:
        empty = {"province": None, "territory": None, "collectivity": None, "groupement": None, "locality": None, "status": "unresolved", "method": None, "confidence": 0.0}
        if x is None or y is None:
            return empty
        province = next((p for p in provinces if p["_bbox"][0] <= x <= p["_bbox"][2] and p["_bbox"][1] <= y <= p["_bbox"][3] and _contains(p["geometry"], x, y)), None)
        candidates = [c for c in collectivities if (not province or c.get("province") == province.get("nom")) and c["_bbox"][0] <= x <= c["_bbox"][2] and c["_bbox"][1] <= y <= c["_bbox"][3]]
        collectivity = next((c for c in candidates if _contains(c["geometry"], x, y)), None)
        if collectivity:
            return {"province": collectivity.get("province"), "territory": collectivity.get("territoire"), "collectivity": collectivity.get("nom"), "collectivity_code": collectivity.get("code_officiel"), "groupement": None, "locality": None, "status": "resolved", "method": "ST_Contains_equivalent", "confidence": 0.95}
        if province:
            return {**empty, "province": province.get("nom"), "status": "partial", "method": "ST_Contains_equivalent", "confidence": 0.8}
        return empty

    def build(self, *, limit: int | None = None) -> dict[str, Any]:
        member, _, root = self._kml()
        provinces, collectivities = self._admin_polygons()
        assets: list[CeniAsset] = []
        occurrences: Counter[str] = Counter()
        for placemark in root.findall(".//k:Placemark", KML_NS)[:limit]:
            raw_properties = {simple.attrib.get("name", ""): (simple.text or "").strip() for simple in placemark.findall(".//k:SimpleData", KML_NS)}
            name = (placemark.findtext("k:name", default="", namespaces=KML_NS) or raw_properties.get("Name") or "").strip()
            coord_text = placemark.findtext(".//k:Point/k:coordinates", default="", namespaces=KML_NS).strip()
            longitude = latitude = None
            geometry_status = "missing"
            try:
                lon_text, lat_text, *_ = coord_text.split(",")
                longitude, latitude = float(lon_text), float(lat_text)
                if not (-180 <= longitude <= 180 and -90 <= latitude <= 90):
                    geometry_status = "invalid"
                elif not (11.0 <= longitude <= 32.0 and -14.5 <= latitude <= 6.0):
                    geometry_status = "outside_country"
                else:
                    geometry_status = "valid"
            except (ValueError, TypeError):
                geometry_status = "invalid" if coord_text else "missing"
            fingerprint_payload = f"{_normalize(name)}|{longitude!r}|{latitude!r}"
            fingerprint = hashlib.sha256(fingerprint_payload.encode("utf-8")).hexdigest().upper()
            occurrences[fingerprint] += 1
            occurrence = occurrences[fingerprint]
            source_record_id = f"{fingerprint[:20]}:{occurrence}"
            asset_uid = "CENI-" + hashlib.sha256(f"{self.source_hash}|{source_record_id}".encode()).hexdigest()[:24].upper()
            classification = default_engine().classify(
                name,
                source_category=None,
                raw_properties={**raw_properties, "kml_name": name, "coordinates": coord_text},
            )
            category = classification.normalized_category_code
            reason = classification.justification_fr
            confidence = classification.confidence
            attachment = self._attach(longitude, latitude, provinces, collectivities)
            if geometry_status == "valid" and attachment["status"] == "unresolved":
                geometry_status = "suspect"
            assets.append(CeniAsset(
                asset_uid=asset_uid, source_record_id=source_record_id, name=name, source_category=None,
                normalized_category=category, classification_justification=reason, classification_confidence=confidence,
                longitude=longitude, latitude=latitude, geometry_status=geometry_status,
                administrative_attachment=attachment,
                source={"file": str(self.source_path.relative_to(ROOT)).replace("\\", "/"), "sha256": self.source_hash, "kml_member": member, "schema": "KMZ File Election"},
                raw_properties={**raw_properties, "kml_name": name, "coordinates": coord_text},
                fingerprint=fingerprint,
                normalized_name=classification.normalized_name,
                normalized_category_label_fr=classification.normalized_category_label_fr,
                classification_method=classification.classification_method,
                matched_rule_id=classification.matched_rule_id,
                matched_keyword=classification.matched_keyword,
                confidence_label_fr=classification.confidence_label_fr,
                engine_version=classification.engine_version,
                classification_date=classification.classification_date,
                review_status=classification.review_status,
            ))
        rows = [asset.as_dict() for asset in assets]
        apply_duplicate_analysis(rows)
        categories = Counter(row["normalized_category"] for row in rows)
        geometries = Counter(row["geometry_status"] for row in rows)
        attachments = Counter(row["administrative_attachment"]["status"] for row in rows)
        duplicates = Counter(row["duplicate"]["status"] for row in rows)
        provinces_count = Counter(row["administrative_attachment"].get("province") or "unresolved" for row in rows)
        territories_count = Counter(row["administrative_attachment"].get("territory") or "unresolved" for row in rows)
        confidence_counts = Counter(row["confidence_label_fr"] for row in rows)
        rules_count = Counter(row["matched_rule_id"] or "Aucune règle" for row in rows)
        review_count = Counter(row["review_status"] for row in rows)
        baseline_categories = default_engine().registry.get("integration_baselines", {}).get("CENI_V1", {})
        unclassified_before = int(baseline_categories.get("UNCLASSIFIED", len(rows)))
        unclassified_after = categories[CeniCategory.UNCLASSIFIED.value]
        return {
            "_meta": {"version": "national-ceni-registry-1.0.0", "generated_at": _now(), "data_first": True, "source_sha256": self.source_hash, "source_size_bytes": self.source_size, "record_count": len(rows)},
            "contract": {"asset_domain": "INSTITUTIONAL", "institution": "CENI", "forbidden_asset_type": "FDSU", "sdg_relations_active": False, "ntie_scores_added": False},
            "statistics": {"total_raw": len(rows), "integrated": sum(1 for r in rows if r["geometry_status"] in {"valid", "suspect"}), "rejected": sum(1 for r in rows if r["geometry_status"] in {"invalid", "missing", "outside_country"}), "suspect": geometries["suspect"], "categories": dict(categories), "geometry_quality": dict(geometries), "administrative_attachments": dict(attachments), "duplicates": dict(duplicates), "provinces": dict(provinces_count), "territories": dict(territories_count), "classification": {"unclassified_before": unclassified_before, "unclassified_after": unclassified_after, "reduction_count": unclassified_before - unclassified_after, "reduction_rate": round((unclassified_before - unclassified_after) / unclassified_before, 6) if unclassified_before else 0, "categories_before": baseline_categories, "categories_after": dict(categories), "confidence": dict(confidence_counts), "top_rules": dict(rules_count.most_common()), "review_status": dict(review_count)}},
            "assets": rows,
        }

    def write(self, registry: dict[str, Any] | None = None) -> dict[str, Any]:
        REPORT_DIR.mkdir(parents=True, exist_ok=True)
        registry = registry or self.build()
        audit = self.audit()
        anomalies = [{
            "asset_uid": asset["asset_uid"], "source_record_id": asset["source_record_id"], "name": asset["name"],
            "geometry_status": asset["geometry_status"], "duplicate": asset["duplicate"],
            "administrative_attachment": asset["administrative_attachment"], "source": asset["source"],
        } for asset in registry["assets"] if asset["geometry_status"] != "valid" or asset["duplicate"]["status"] != "none" or asset["administrative_attachment"]["status"] != "resolved"]
        batch = {"batch_id": f"CENI-{self.source_hash[:12]}", "source_sha256": self.source_hash, "created_at": _now(), "status": "validated_file_registry", "record_count": len(registry["assets"]), "rollback": {"mode": "delete generated artifacts for this batch only", "source_untouched": True}}
        REGISTRY_PATH.write_text(json.dumps(registry, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        AUDIT_PATH.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
        ANOMALY_PATH.write_text(json.dumps({"_meta": registry["_meta"], "count": len(anomalies), "anomalies": anomalies}, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        BATCH_PATH.write_text(json.dumps({"batches": [batch]}, ensure_ascii=False, indent=2), encoding="utf-8")
        return registry

    def enrich_classification(self) -> dict[str, Any]:
        """Enrichit l'artefact généré sans relire ni modifier la source officielle."""
        registry = self.load()
        engine = default_engine()
        for row in registry.get("assets", []):
            result = engine.classify(row.get("name", ""), row.get("source_category"), row.get("raw_properties"))
            row.update({
                "normalized_name": result.normalized_name,
                "normalized_category": result.normalized_category_code,
                "normalized_category_label_fr": result.normalized_category_label_fr,
                "classification_method": result.classification_method,
                "matched_rule_id": result.matched_rule_id,
                "matched_keyword": result.matched_keyword,
                "classification_confidence": result.confidence,
                "confidence_label_fr": result.confidence_label_fr,
                "classification_justification": result.justification_fr,
                "engine_version": result.engine_version,
                "classification_date": result.classification_date,
                "review_status": result.review_status,
            })
        rows = registry.get("assets", [])
        categories = Counter(row["normalized_category"] for row in rows)
        confidence = Counter(row["confidence_label_fr"] for row in rows)
        rules = Counter(row["matched_rule_id"] or "Aucune règle" for row in rows)
        reviews = Counter(row["review_status"] for row in rows)
        baseline_categories = engine.registry.get("integration_baselines", {}).get("CENI_V1", {})
        before = int(baseline_categories.get("UNCLASSIFIED", len(rows)))
        after = categories[CeniCategory.UNCLASSIFIED.value]
        registry["statistics"]["categories"] = dict(categories)
        registry["statistics"]["classification"] = {"unclassified_before": before, "unclassified_after": after, "reduction_count": before - after, "reduction_rate": round((before - after) / before, 6) if before else 0, "categories_before": baseline_categories, "categories_after": dict(categories), "confidence": dict(confidence), "top_rules": dict(rules.most_common()), "review_status": dict(reviews)}
        registry["_meta"]["classification_engine_version"] = engine.registry["engine_version"]
        REGISTRY_PATH.write_text(json.dumps(registry, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        return registry

    @staticmethod
    def load() -> dict[str, Any]:
        if not REGISTRY_PATH.exists():
            return CeniRegistryService().write()
        return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))
