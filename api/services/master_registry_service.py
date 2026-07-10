"""Référentiel National des Actifs FDSU — Master Data & Business Registry.

Source de vérité officielle pour toutes les entités métier FDSU.
Les sites utilisent exclusivement le code FDSU officiel comme business_id.
"""

from __future__ import annotations

import json
import re
import uuid
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from api.config import DATA_MODE, connect_db
from api.services import fdsu_code_service
from app.fdsu_nomenclature import OFFICIAL_STRUCTURE_RELATIVE, load_nomenclature

PROJECT_ROOT = Path(__file__).resolve().parents[2]
MASTER_DIR = PROJECT_ROOT / "data" / "master"
REGISTRY_PATH = MASTER_DIR / "registry.json"
SCHEMA_EXAMPLE = PROJECT_ROOT / "docs" / "master_registry_schema.sql.example"

ENTITY_TYPES = (
    "PROGRAM",
    "BATCH",
    "PROJECT",
    "SITE",
    "CCN",
    "ZONE",
    "PROVINCE",
    "TERRITOIRE",
    "COLLECTIVITE",
    "GROUPEMENT",
    "LOCALITE",
    "VILLAGE",
    "TELCO",
    "HEALTH",
    "SCHOOL",
    "MARKET",
    "ROAD",
    "FIBER",
    "MISSION",
    "DECISION",
    "SCORING",
)

BUSINESS_ID_PREFIXES = {
    "PROGRAM": "PROGRAM",
    "BATCH": "BATCH",
    "PROJECT": "PROJECT",
    "CCN": "CCN",
    "ZONE": "ZONE",
    "PROVINCE": "PROVINCE",
    "TERRITOIRE": "TERRITOIRE",
    "COLLECTIVITE": "COLLECTIVITE",
    "GROUPEMENT": "GROUPEMENT",
    "LOCALITE": "LOCALITE",
    "VILLAGE": "VILLAGE",
    "TELCO": "TELCO",
    "HEALTH": "HEALTH",
    "SCHOOL": "SCHOOL",
    "MARKET": "MARKET",
    "ROAD": "ROAD",
    "FIBER": "FIBER",
    "MISSION": "MISSION",
    "DECISION": "DECISION",
    "SCORING": "SCORING",
}

STATUS_VALUES = ("draft", "active", "archived", "merged", "deprecated")
VALIDATION_VALUES = ("pending", "validated", "rejected", "needs_review")
CONFIDENCE_VALUES = ("high", "medium", "low", "unknown")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _empty_registry() -> dict[str, Any]:
    return {
        "_meta": {
            "title": "Référentiel National des Actifs FDSU",
            "version": "1.0.0",
            "nomenclature_source": OFFICIAL_STRUCTURE_RELATIVE,
            "nomenclature_note": (
                "La nomenclature officielle FDSU est issue du fichier "
                f"{OFFICIAL_STRUCTURE_RELATIVE} et constitue la référence unique "
                "pour la génération et la validation des codes FDSU."
            ),
            "updated_at": _now(),
        },
        "entities": [],
        "aliases": [],
        "sources": [],
        "links": [],
        "validation_log": [],
        "counters": {},
    }


def _ensure_store() -> dict[str, Any]:
    MASTER_DIR.mkdir(parents=True, exist_ok=True)
    if not REGISTRY_PATH.exists():
        payload = _empty_registry()
        _bootstrap_from_nomenclature(payload)
        _save_registry(payload)
        return payload
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


def _save_registry(payload: dict[str, Any]) -> None:
    MASTER_DIR.mkdir(parents=True, exist_ok=True)
    payload.setdefault("_meta", {})["updated_at"] = _now()
    REGISTRY_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _next_generic_business_id(entity_type: str, payload: dict[str, Any]) -> str:
    prefix = BUSINESS_ID_PREFIXES.get(entity_type.upper(), entity_type.upper())
    counters = payload.setdefault("counters", {})
    current = int(counters.get(prefix, 0)) + 1
    counters[prefix] = current
    return f"{prefix}-{current:06d}"


def _append_version(entity: dict[str, Any], change_type: str, note: str | None = None) -> None:
    versions = entity.setdefault("versions", [])
    versions.append(
        {
            "version": entity.get("version", 1),
            "changed_at": _now(),
            "change_type": change_type,
            "note": note,
            "snapshot": {
                "business_id": entity.get("business_id"),
                "name": entity.get("name"),
                "status": entity.get("status"),
                "validation_status": entity.get("validation_status"),
                "attributes": deepcopy(entity.get("attributes") or {}),
            },
        }
    )


def _log_validation(payload: dict[str, Any], entity_uuid: str, result: dict[str, Any]) -> None:
    payload.setdefault("validation_log", []).append(
        {
            "id": str(uuid.uuid4()),
            "entity_uuid": entity_uuid,
            "validated_at": _now(),
            "result": result,
        }
    )


def _bootstrap_from_nomenclature(payload: dict[str, Any]) -> None:
    """Initialise zones / provinces / territoires / programmes depuis la nomenclature officielle."""
    nomenclature = load_nomenclature()
    source = {
        "id": str(uuid.uuid4()),
        "code": "FDSU_STRUCTURE_ZONES",
        "label": "FDSU Structure code Territoire zones",
        "path": nomenclature.get("source") or OFFICIAL_STRUCTURE_RELATIVE,
        "imported_at": _now(),
        "confidence_level": "high",
    }
    payload["sources"].append(source)

    for zone in nomenclature.get("zones", []):
        create_entity(
            {
                "entity_type": "ZONE",
                "business_id": f"ZONE-{zone.get('code')}",
                "name": zone.get("nom") or zone.get("code"),
                "status": "active",
                "validation_status": "validated",
                "confidence_level": "high",
                "source": source["code"],
                "attributes": {
                    "zone_code": zone.get("code"),
                    "province_count": zone.get("province_count"),
                    "provinces": zone.get("provinces"),
                },
            },
            payload=payload,
            persist=False,
            skip_duplicate_check=True,
        )

    for province in nomenclature.get("provinces", []):
        create_entity(
            {
                "entity_type": "PROVINCE",
                "business_id": f"PROVINCE-{str(province.get('code')).zfill(2)}",
                "name": province.get("nom"),
                "status": "active",
                "validation_status": "validated",
                "confidence_level": "high",
                "source": source["code"],
                "attributes": {
                    "province_code": str(province.get("code")).zfill(2),
                    "zone_fdsu": province.get("zone_fdsu"),
                    "nb_sites_reference": province.get("nb_sites_reference"),
                },
            },
            payload=payload,
            persist=False,
            skip_duplicate_check=True,
        )

    for territoire in nomenclature.get("territoires", []):
        prov = str(territoire.get("province_code")).zfill(2)
        terr = str(territoire.get("code")).zfill(3)
        create_entity(
            {
                "entity_type": "TERRITOIRE",
                "business_id": f"TERRITOIRE-{prov}-{terr}",
                "name": territoire.get("nom"),
                "status": "active",
                "validation_status": "validated",
                "confidence_level": "high",
                "source": source["code"],
                "attributes": {
                    "province_code": prov,
                    "territoire_code": terr,
                    "province_name": territoire.get("province"),
                    "zone_fdsu": territoire.get("zone_fdsu"),
                    "nb_sites_reference": territoire.get("nb_sites_reference"),
                },
            },
            payload=payload,
            persist=False,
            skip_duplicate_check=True,
        )

    for program in (
        ("PROGRAM-SITES-40", "Sites 40", "sites_40", "pilot"),
        ("PROGRAM-SITES-300", "Sites 300", "sites_300", "first_wave"),
        ("PROGRAM-SITES-20476", "Sites 20 476", "sites_20476", "national"),
    ):
        create_entity(
            {
                "entity_type": "PROGRAM",
                "business_id": program[0],
                "name": program[1],
                "status": "active",
                "validation_status": "validated",
                "confidence_level": "high",
                "source": "FDSU_PROGRAM_CATALOG",
                "attributes": {"program_code": program[2], "phase": program[3]},
            },
            payload=payload,
            persist=False,
            skip_duplicate_check=True,
        )


def create_entity(
    data: dict[str, Any],
    *,
    payload: dict[str, Any] | None = None,
    persist: bool = True,
    skip_duplicate_check: bool = False,
) -> dict[str, Any]:
    store = payload or _ensure_store()
    entity_type = str(data.get("entity_type") or "").upper().strip()
    if entity_type not in ENTITY_TYPES:
        raise ValueError(f"Type d'entité non supporté: {entity_type}. Autorisés: {ENTITY_TYPES}")

    business_id = str(data.get("business_id") or "").strip()
    fdsu_validation = None

    if entity_type == "SITE":
        if not business_id:
            raise ValueError(
                "Un site FDSU exige un business_id = code officiel "
                "(ex. FDSU_ND_18_003_10100). SITE-FDSU-###### est interdit."
            )
        if fdsu_code_service.is_artificial_site_id(business_id):
            raise ValueError("Identifiant artificiel de site interdit.")
        fdsu_validation = fdsu_code_service.validate_fdsu_code(business_id)
        if not fdsu_validation.is_valid:
            raise ValueError("; ".join(fdsu_validation.errors) or "Code FDSU invalide.")
        business_id = fdsu_validation.business_id
    elif not business_id:
        business_id = _next_generic_business_id(entity_type, store)

    if not skip_duplicate_check:
        duplicates = detect_duplicates(business_id=business_id, name=data.get("name"), entity_type=entity_type, payload=store)
        blocking = [item for item in duplicates if item.get("severity") == "exact_business_id"]
        if blocking:
            raise ValueError(f"Doublon business_id détecté: {business_id}")

    now = _now()
    entity = {
        "uuid": str(uuid.uuid4()),
        "business_id": business_id,
        "entity_type": entity_type,
        "name": data.get("name") or business_id,
        "status": data.get("status") or "draft",
        "validation_status": data.get("validation_status") or "pending",
        "confidence_level": data.get("confidence_level") or "unknown",
        "source": data.get("source") or "manual",
        "version": 1,
        "created_at": now,
        "updated_at": now,
        "attributes": data.get("attributes") or {},
        "geometry": data.get("geometry"),
        "versions": [],
        "merged_into": None,
    }
    if fdsu_validation:
        entity["attributes"] = {
            **entity["attributes"],
            "fdsu_code": fdsu_validation.as_dict(),
        }
        entity["validation_status"] = "validated" if fdsu_validation.is_valid else "needs_review"
        entity["confidence_level"] = "high" if fdsu_validation.nomenclature_match else "medium"

    _append_version(entity, "create", note="Création entité master")
    store.setdefault("entities", []).append(entity)
    if fdsu_validation:
        _log_validation(store, entity["uuid"], fdsu_validation.as_dict())
    if persist:
        _save_registry(store)
    return entity


def update_entity(entity_id: str, patch: dict[str, Any]) -> dict[str, Any] | None:
    store = _ensure_store()
    entity = get_entity(entity_id, payload=store)
    if not entity:
        return None

    protected = {"uuid", "created_at", "versions"}
    for key, value in patch.items():
        if key in protected:
            continue
        if key == "business_id" and entity["entity_type"] == "SITE":
            validation = fdsu_code_service.validate_fdsu_code(value)
            if not validation.is_valid:
                raise ValueError("; ".join(validation.errors))
            entity["business_id"] = validation.business_id
            entity.setdefault("attributes", {})["fdsu_code"] = validation.as_dict()
            continue
        if key == "entity_type":
            continue
        entity[key] = value

    entity["version"] = int(entity.get("version") or 1) + 1
    entity["updated_at"] = _now()
    _append_version(entity, "update", note=patch.get("change_note"))
    _save_registry(store)
    return entity


def get_entity(entity_id: str, *, payload: dict[str, Any] | None = None) -> dict[str, Any] | None:
    store = payload or _ensure_store()
    needle = str(entity_id).strip()
    for entity in store.get("entities", []):
        if entity.get("uuid") == needle or entity.get("business_id") == needle:
            return entity
    return None


def list_entities(
    *,
    entity_type: str | None = None,
    status: str | None = None,
    validation_status: str | None = None,
    q: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> dict[str, Any]:
    store = _ensure_store()
    items = list(store.get("entities") or [])
    if entity_type:
        items = [item for item in items if item.get("entity_type") == entity_type.upper()]
    if status:
        items = [item for item in items if item.get("status") == status]
    if validation_status:
        items = [item for item in items if item.get("validation_status") == validation_status]
    if q:
        query = q.strip().lower()
        items = [
            item
            for item in items
            if query in str(item.get("business_id") or "").lower()
            or query in str(item.get("name") or "").lower()
            or query in str(item.get("entity_type") or "").lower()
        ]
    total = len(items)
    page = items[offset : offset + limit]
    return {
        "_meta": {
            "title": "Référentiel National des Actifs FDSU",
            "total": total,
            "count": len(page),
            "offset": offset,
            "limit": limit,
        },
        "entities": page,
    }


def search_entities(query: str, *, limit: int = 50) -> dict[str, Any]:
    return list_entities(q=query, limit=limit, offset=0)


def get_history(entity_id: str) -> dict[str, Any] | None:
    entity = get_entity(entity_id)
    if not entity:
        return None
    return {
        "uuid": entity["uuid"],
        "business_id": entity["business_id"],
        "version": entity.get("version"),
        "versions": entity.get("versions") or [],
    }


def detect_duplicates(
    *,
    business_id: str | None = None,
    name: str | None = None,
    entity_type: str | None = None,
    payload: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    store = payload or _ensure_store()
    results: list[dict[str, Any]] = []
    name_norm = re.sub(r"\s+", " ", str(name or "").strip().lower())
    bid = str(business_id or "").strip().upper()

    for entity in store.get("entities") or []:
        if entity.get("status") == "merged":
            continue
        if entity_type and entity.get("entity_type") != entity_type.upper():
            continue
        entity_bid = str(entity.get("business_id") or "").upper()
        entity_name = re.sub(r"\s+", " ", str(entity.get("name") or "").strip().lower())
        if bid and entity_bid == bid:
            results.append(
                {
                    "severity": "exact_business_id",
                    "entity": {
                        "uuid": entity["uuid"],
                        "business_id": entity["business_id"],
                        "name": entity["name"],
                        "entity_type": entity["entity_type"],
                    },
                }
            )
        elif name_norm and entity_name == name_norm:
            results.append(
                {
                    "severity": "exact_name",
                    "entity": {
                        "uuid": entity["uuid"],
                        "business_id": entity["business_id"],
                        "name": entity["name"],
                        "entity_type": entity["entity_type"],
                    },
                }
            )
    return results


def merge_entities(source_id: str, target_id: str, *, note: str | None = None) -> dict[str, Any]:
    store = _ensure_store()
    source = get_entity(source_id, payload=store)
    target = get_entity(target_id, payload=store)
    if not source or not target:
        raise ValueError("Source ou cible introuvable pour fusion.")
    if source["uuid"] == target["uuid"]:
        raise ValueError("Impossible de fusionner une entité avec elle-même.")

    store.setdefault("aliases", []).append(
        {
            "id": str(uuid.uuid4()),
            "entity_uuid": target["uuid"],
            "alias": source["business_id"],
            "alias_type": "merged_business_id",
            "created_at": _now(),
        }
    )
    store.setdefault("links", []).append(
        {
            "id": str(uuid.uuid4()),
            "from_uuid": source["uuid"],
            "to_uuid": target["uuid"],
            "link_type": "merged_into",
            "created_at": _now(),
            "note": note,
        }
    )
    source["status"] = "merged"
    source["merged_into"] = target["uuid"]
    source["version"] = int(source.get("version") or 1) + 1
    source["updated_at"] = _now()
    _append_version(source, "merge", note=note or f"Fusionné dans {target['business_id']}")
    target["version"] = int(target.get("version") or 1) + 1
    target["updated_at"] = _now()
    _append_version(target, "absorb", note=note or f"A absorbé {source['business_id']}")
    _save_registry(store)
    return {"source": source, "target": target}


def validate_entity(entity_id: str) -> dict[str, Any]:
    store = _ensure_store()
    entity = get_entity(entity_id, payload=store)
    if not entity:
        raise ValueError("Entité introuvable.")

    result: dict[str, Any] = {
        "uuid": entity["uuid"],
        "business_id": entity["business_id"],
        "entity_type": entity["entity_type"],
        "is_valid": True,
        "errors": [],
        "warnings": [],
    }

    if entity["entity_type"] == "SITE":
        validation = fdsu_code_service.validate_fdsu_code(entity["business_id"])
        result.update(
            {
                "is_valid": validation.is_valid,
                "errors": validation.errors,
                "warnings": validation.warnings,
                "fdsu": validation.as_dict(),
            }
        )
        entity["validation_status"] = "validated" if validation.is_valid else "needs_review"
        entity["attributes"]["fdsu_code"] = validation.as_dict()
    else:
        if not entity.get("name"):
            result["is_valid"] = False
            result["errors"].append("Nom manquant.")
        if entity.get("status") not in STATUS_VALUES:
            result["warnings"].append(f"Statut atypique: {entity.get('status')}")
        entity["validation_status"] = "validated" if result["is_valid"] else "needs_review"

    entity["updated_at"] = _now()
    _log_validation(store, entity["uuid"], result)
    _save_registry(store)
    return result


def get_fdsu_code_details(business_id: str) -> dict[str, Any]:
    validation = fdsu_code_service.validate_fdsu_code(business_id)
    entity = get_entity(validation.business_id) if validation.business_id else None
    duplicates = detect_duplicates(business_id=validation.business_id, entity_type="SITE")
    return {
        "business_id": validation.business_id or business_id,
        "validation": validation.as_dict(),
        "registry_entity": entity,
        "duplicates": duplicates,
    }


def statistics() -> dict[str, Any]:
    store = _ensure_store()
    entities = [item for item in store.get("entities") or [] if item.get("status") != "merged"]
    by_type: dict[str, int] = {}
    for entity in entities:
        by_type[entity["entity_type"]] = by_type.get(entity["entity_type"], 0) + 1

    sites = [item for item in entities if item.get("entity_type") == "SITE"]
    valid_codes = 0
    invalid_codes = 0
    for site in sites:
        validation = fdsu_code_service.validate_fdsu_code(site.get("business_id"))
        if validation.is_valid:
            valid_codes += 1
        else:
            invalid_codes += 1

    # Doublons potentiels (même nom, types identiques)
    name_map: dict[tuple[str, str], list[str]] = {}
    for entity in entities:
        key = (entity.get("entity_type") or "", re.sub(r"\s+", " ", str(entity.get("name") or "").lower()))
        name_map.setdefault(key, []).append(entity["business_id"])
    duplicate_groups = sum(1 for values in name_map.values() if len(values) > 1)

    sources = {}
    for entity in entities:
        src = entity.get("source") or "unknown"
        sources[src] = sources.get(src, 0) + 1

    validation_counts = {}
    confidence_counts = {}
    for entity in entities:
        validation_counts[entity.get("validation_status") or "unknown"] = (
            validation_counts.get(entity.get("validation_status") or "unknown", 0) + 1
        )
        confidence_counts[entity.get("confidence_level") or "unknown"] = (
            confidence_counts.get(entity.get("confidence_level") or "unknown", 0) + 1
        )

    return {
        "_meta": {
            "title": "Qualité du Référentiel National FDSU",
            "updated_at": store.get("_meta", {}).get("updated_at"),
            "nomenclature_source": store.get("_meta", {}).get("nomenclature_source"),
        },
        "totals": {
            "entities": len(entities),
            "sites": len(sites),
            "duplicate_groups": duplicate_groups,
            "fdsu_codes_valid": valid_codes,
            "fdsu_codes_invalid": invalid_codes,
            "sources": len(sources),
            "versions_events": sum(len(item.get("versions") or []) for item in entities),
        },
        "by_type": by_type,
        "sources": sources,
        "validation_status": validation_counts,
        "confidence_level": confidence_counts,
        "quality_score": _quality_score(len(entities), duplicate_groups, valid_codes, invalid_codes),
    }


def _quality_score(total: int, duplicates: int, valid: int, invalid: int) -> float:
    if total <= 0:
        return 0.0
    base = 100.0
    base -= min(40.0, duplicates * 5.0)
    site_total = valid + invalid
    if site_total:
        base -= (invalid / site_total) * 40.0
    return round(max(0.0, min(100.0, base)), 1)


def ensure_postgis_schema() -> dict[str, Any]:
    """Crée le schéma master.* si la base est disponible."""
    if DATA_MODE != "db":
        return {"applied": False, "reason": "DATA_MODE != db"}
    sql_path = SCHEMA_EXAMPLE
    if not sql_path.exists():
        return {"applied": False, "reason": "schema example missing"}
    sql = sql_path.read_text(encoding="utf-8")
    # Exécuter uniquement les CREATE (fichier .example versionnable)
    try:
        with connect_db() as conn:
            with conn.cursor() as cur:
                cur.execute(sql)
            conn.commit()
        return {"applied": True, "schema": "master"}
    except Exception as exc:  # noqa: BLE001
        return {"applied": False, "error": str(exc)}


def panel_payload() -> dict[str, Any]:
    stats = statistics()
    store = _ensure_store()
    return {
        "_meta": {
            "title": "Référentiel National des Actifs FDSU",
            "subtitle": "Source officielle de vérité — nomenclature FDSU prioritaire",
        },
        "statistics": stats,
        "entity_types": list(ENTITY_TYPES),
        "nomenclature": {
            "format": "FDSU_<ZONE>_<PROVINCE>_<TERRITOIRE>_<SITE>",
            "example": "FDSU_ND_18_003_10100",
            "source": store.get("_meta", {}).get("nomenclature_source"),
            "note": store.get("_meta", {}).get("nomenclature_note"),
            "zones": sorted(fdsu_code_service.OFFICIAL_ZONES),
        },
        "recent_validation": list(reversed(store.get("validation_log") or []))[:10],
    }
