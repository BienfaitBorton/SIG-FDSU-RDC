"""Lecture fichier du Référentiel National CENI v1.0."""

from __future__ import annotations

import json
from functools import lru_cache
from typing import Any

from app.referentials.ceni_official.models import CeniCategory
from app.referentials.ceni_official.service import ANOMALY_PATH, BATCH_PATH, CeniRegistryService
from api.services.national_semantic_classification_engine import DEFAULT_RULES_PATH


@lru_cache(maxsize=1)
def registry() -> dict[str, Any]:
    return CeniRegistryService.load()


def list_sites(*, q: str | None = None, category: str | None = None, province: str | None = None, territory: str | None = None, quality: str | None = None, limit: int = 100, offset: int = 0) -> dict[str, Any]:
    rows = registry().get("assets", [])
    if q:
        needle = q.casefold()
        rows = [row for row in rows if needle in str(row.get("name") or "").casefold() or needle in row["asset_uid"].casefold()]
    if category:
        rows = [row for row in rows if row.get("normalized_category") == category]
    if province:
        rows = [row for row in rows if row.get("administrative_attachment", {}).get("province") == province]
    if territory:
        rows = [row for row in rows if row.get("administrative_attachment", {}).get("territory") == territory]
    if quality:
        rows = [row for row in rows if row.get("geometry_status") == quality]
    total = len(rows)
    return {"total": total, "offset": offset, "limit": limit, "sites": rows[offset : offset + limit], "source_sha256": registry().get("_meta", {}).get("source_sha256")}


def get_site(asset_uid: str) -> dict[str, Any] | None:
    return next((row for row in registry().get("assets", []) if row.get("asset_uid") == asset_uid or row.get("source_record_id") == asset_uid), None)


def statistics() -> dict[str, Any]:
    return {"_meta": registry().get("_meta", {}), **registry().get("statistics", {}), "contract": registry().get("contract", {})}


def data_quality(limit: int = 500, offset: int = 0) -> dict[str, Any]:
    if not ANOMALY_PATH.exists():
        CeniRegistryService().write(registry())
    doc = json.loads(ANOMALY_PATH.read_text(encoding="utf-8"))
    return {"_meta": doc.get("_meta", {}), "total": doc.get("count", 0), "offset": offset, "limit": limit, "anomalies": doc.get("anomalies", [])[offset : offset + limit]}


def categories() -> dict[str, Any]:
    counts = registry().get("statistics", {}).get("categories", {})
    labels = json.loads(DEFAULT_RULES_PATH.read_text(encoding="utf-8"))["categories_fr"]
    return {"categories": [{"id": item.value, "label_fr": labels[item.value], "count": counts.get(item.value, 0)} for item in CeniCategory]}


def classification_statistics() -> dict[str, Any]:
    return {"_meta": registry().get("_meta", {}), **registry().get("statistics", {}).get("classification", {}), "categories": registry().get("statistics", {}).get("categories", {})}


def classification_rules() -> dict[str, Any]:
    return json.loads(DEFAULT_RULES_PATH.read_text(encoding="utf-8"))


def classification_review(limit: int = 100, offset: int = 0) -> dict[str, Any]:
    rows = [row for row in registry().get("assets", []) if row.get("review_status") == "À vérifier"]
    return {"total": len(rows), "offset": offset, "limit": limit, "sites": rows[offset:offset + limit]}


def site_classification(asset_uid: str) -> dict[str, Any] | None:
    row = get_site(asset_uid)
    if row is None:
        return None
    keys = ("source_name", "normalized_name", "source_category", "normalized_category", "normalized_category_label_fr", "classification_method", "matched_rule_id", "matched_keyword", "classification_confidence", "confidence_label_fr", "classification_justification", "engine_version", "classification_date", "review_status", "raw_properties")
    payload = {key: row.get(key) for key in keys}
    payload["source_name"] = row.get("name")
    payload["normalized_category_code"] = payload.pop("normalized_category")
    payload["confidence"] = payload.pop("classification_confidence")
    payload["justification_fr"] = payload.pop("classification_justification")
    return payload


def map_features(*, category: str | None = None, province: str | None = None, limit: int = 5000) -> dict[str, Any]:
    rows = list_sites(category=category, province=province, limit=limit)["sites"]
    features = [{"type": "Feature", "id": row["asset_uid"], "geometry": {"type": "Point", "coordinates": [row["longitude"], row["latitude"]]}, "properties": {"asset_uid": row["asset_uid"], "name": row["name"], "category": row["normalized_category"], "quality": row["geometry_status"], "province": row["administrative_attachment"].get("province"), "institution": "CENI"}} for row in rows if row.get("longitude") is not None and row.get("latitude") is not None]
    return {"type": "FeatureCollection", "features": features, "returned": len(features), "limit": limit}


def import_batches() -> dict[str, Any]:
    return json.loads(BATCH_PATH.read_text(encoding="utf-8")) if BATCH_PATH.exists() else {"batches": []}
