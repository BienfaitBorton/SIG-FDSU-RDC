"""National Data Fabric (NDF) — gouvernance et inventaire des référentiels nationaux.

Socle d'organisation des données SIG-FDSU RDC.
Ne duplique pas Master Registry, Knowledge Hub, NCI, TST, etc. :
il catalogue leurs métadonnées et expose un contrat commun d'intégration.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
NDF_DIR = PROJECT_ROOT / "data" / "ndf"
REGISTRIES_PATH = NDF_DIR / "registries.json"
EXTENSIONS_PATH = NDF_DIR / "registries_extensions.json"
RELATIONS_PATH = NDF_DIR / "relations.json"

ENGINE_VERSION = "ndf-1.0.0"

REQUIRED_FIELDS = (
    "id",
    "name",
    "category",
    "description",
    "owner",
    "official_source",
    "update_frequency",
    "version",
    "confidence_level",
    "geographic_coverage",
    "geometry_type",
    "crs",
)

QUALITY_DIMENSIONS = ("completeness", "freshness", "coherence", "geometry", "precision")

CONSUMERS = {
    "territorial_summary": {
        "name": "Tableau de Synthèse Territoriale (TST)",
        "api": "/api/territorial-summary",
        "uses": ["administrative", "prioritization", "population", "health", "ccn", "fdsu_sites"],
    },
    "decision_engine": {
        "name": "Explainable Decision Engine",
        "api": "/api/decision",
        "uses": ["prioritization", "fdsu_sites", "population", "knowledge_hub"],
    },
    "knowledge_hub": {
        "name": "Knowledge Hub / NIF",
        "api": "/api/knowledge",
        "uses": ["knowledge_hub", "telecom", "health", "population", "administrative"],
    },
    "spatial_matching": {
        "name": "National Spatial Matching Engine (NSME)",
        "api": "/api/spatial-matching",
        "uses": ["administrative", "fdsu_sites", "telecom", "health"],
    },
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _core_registries() -> list[dict[str, Any]]:
    return list((_load_json(REGISTRIES_PATH).get("registries") or []))


def _extension_registries() -> list[dict[str, Any]]:
    return list((_load_json(EXTENSIONS_PATH).get("registries") or []))


def _all_registries() -> list[dict[str, Any]]:
    by_id: dict[str, dict[str, Any]] = {}
    for item in _core_registries():
        rid = str(item.get("id") or "").strip()
        if rid:
            by_id[rid] = {**item, "_origin": "core"}
    for item in _extension_registries():
        rid = str(item.get("id") or "").strip()
        if rid:
            by_id[rid] = {**item, "_origin": "extension"}
    return list(by_id.values())


def _find(registry_id: str) -> dict[str, Any] | None:
    needle = str(registry_id or "").strip().lower()
    for item in _all_registries():
        if str(item.get("id") or "").lower() == needle:
            return item
    return None


def _insufficient(dimension: str, note: str | None = None) -> dict[str, Any]:
    return {
        "dimension": dimension,
        "value": None,
        "display": "Données insuffisantes",
        "status": "not_measured",
        "note": note,
    }


def _measured(dimension: str, value: float | int | None, display: str, source: str) -> dict[str, Any]:
    return {
        "dimension": dimension,
        "value": value,
        "display": display,
        "status": "ok" if value is not None else "not_measured",
        "source": source,
    }


def fabric_manifest() -> dict[str, Any]:
    regs = _all_registries()
    active = [r for r in regs if r.get("status") == "active"]
    planned = [r for r in regs if r.get("status") == "planned"]
    return {
        "_meta": {
            "title": "National Data Fabric",
            "version": ENGINE_VERSION,
            "updated_at": _now(),
            "role": "Couche d'organisation et de gouvernance des référentiels nationaux",
            "ui": "Aucune interface utilisateur principale — API + métadonnées uniquement",
        },
        "counts": {
            "registries_total": len(regs),
            "active": len(active),
            "planned": len(planned),
            "extensions": len(_extension_registries()),
        },
        "quality_dimensions": list(QUALITY_DIMENSIONS),
        "consumers": list(CONSUMERS.keys()),
        "paths": {
            "registries": str(REGISTRIES_PATH.relative_to(PROJECT_ROOT)).replace("\\", "/"),
            "extensions": str(EXTENSIONS_PATH.relative_to(PROJECT_ROOT)).replace("\\", "/"),
            "relations": str(RELATIONS_PATH.relative_to(PROJECT_ROOT)).replace("\\", "/"),
        },
    }


def list_registries(
    category: str | None = None,
    status: str | None = None,
) -> dict[str, Any]:
    items = _all_registries()
    if category:
        cat = category.strip().lower()
        items = [r for r in items if str(r.get("category") or "").lower() == cat]
    if status:
        st = status.strip().lower()
        items = [r for r in items if str(r.get("status") or "").lower() == st]
    items = sorted(items, key=lambda r: (str(r.get("status") or ""), str(r.get("name") or "")))
    return {
        "_meta": {
            "version": ENGINE_VERSION,
            "count": len(items),
            "updated_at": _now(),
        },
        "registries": [
            {
                "id": r.get("id"),
                "name": r.get("name"),
                "category": r.get("category"),
                "status": r.get("status"),
                "owner": r.get("owner"),
                "version": r.get("version"),
                "confidence_level": r.get("confidence_level"),
                "apis": r.get("apis") or [],
                "origin": r.get("_origin"),
            }
            for r in items
        ],
    }


def get_registry(registry_id: str) -> dict[str, Any] | None:
    item = _find(registry_id)
    if not item:
        return None
    detail = {k: v for k, v in item.items() if k != "_origin"}
    detail["origin"] = item.get("_origin")
    detail["quality"] = compute_quality(registry_id)["indicators"]
    rels = [
        r
        for r in (_load_json(RELATIONS_PATH).get("relations") or [])
        if r.get("from") == registry_id or r.get("to") == registry_id
    ]
    return {
        "_meta": {"version": ENGINE_VERSION, "updated_at": _now()},
        "registry": detail,
        "relations": rels,
    }


def search_registries(query: str) -> dict[str, Any]:
    q = str(query or "").strip().lower()
    if not q:
        return list_registries()
    hits = []
    for item in _all_registries():
        blob = " ".join(
            str(item.get(k) or "")
            for k in ("id", "name", "category", "description", "owner", "official_source")
        ).lower()
        apis = " ".join(item.get("apis") or []).lower()
        if q in blob or q in apis:
            hits.append(item)
    return {
        "_meta": {"version": ENGINE_VERSION, "query": query, "count": len(hits), "updated_at": _now()},
        "registries": [
            {
                "id": r.get("id"),
                "name": r.get("name"),
                "category": r.get("category"),
                "status": r.get("status"),
                "description": r.get("description"),
                "apis": r.get("apis") or [],
            }
            for r in hits
        ],
    }


def list_relations(registry_id: str | None = None) -> dict[str, Any]:
    relations = list(_load_json(RELATIONS_PATH).get("relations") or [])
    known = {str(r.get("id")) for r in _all_registries()}
    if registry_id:
        relations = [r for r in relations if r.get("from") == registry_id or r.get("to") == registry_id]
    # Cohérence : extrémités connues ou planifiées
    coherent = []
    issues = []
    for rel in relations:
        frm, to = rel.get("from"), rel.get("to")
        ok = frm in known and to in known
        coherent.append({**rel, "endpoints_known": ok})
        if not ok:
            issues.append({"from": frm, "to": to, "issue": "endpoint_unknown"})
    return {
        "_meta": {
            "version": ENGINE_VERSION,
            "count": len(coherent),
            "coherence_issues": len(issues),
            "updated_at": _now(),
        },
        "relations": coherent,
        "issues": issues,
    }


def register_registry(payload: dict[str, Any], *, allow_overwrite_extension: bool = False) -> dict[str, Any]:
    """Enregistre un référentiel dans registries_extensions.json — sans modifier le cœur."""
    data = dict(payload or {})
    missing = [f for f in REQUIRED_FIELDS if not data.get(f)]
    if missing:
        raise ValueError(f"Champs obligatoires manquants : {', '.join(missing)}")

    rid = str(data["id"]).strip()
    if not rid:
        raise ValueError("id invalide")

    core_ids = {str(r.get("id")) for r in _core_registries()}
    if rid in core_ids:
        raise ValueError(f"Le référentiel « {rid} » appartient au catalogue cœur — pas de doublon.")

    extensions = _load_json(EXTENSIONS_PATH) or {
        "_meta": {"title": "NDF extensions", "version": ENGINE_VERSION},
        "registries": [],
    }
    existing = list(extensions.get("registries") or [])
    idx = next((i for i, r in enumerate(existing) if r.get("id") == rid), None)
    if idx is not None and not allow_overwrite_extension:
        raise ValueError(f"Référentiel extension « {rid} » déjà enregistré.")

    record = {
        "id": rid,
        "name": data["name"],
        "category": data["category"],
        "status": data.get("status") or "registered",
        "description": data["description"],
        "owner": data["owner"],
        "official_source": data["official_source"],
        "update_frequency": data["update_frequency"],
        "version": data["version"],
        "quality_baseline": data.get("quality_baseline") or "not_measured",
        "confidence_level": data["confidence_level"],
        "geographic_coverage": data["geographic_coverage"],
        "geometry_type": data["geometry_type"],
        "crs": data["crs"],
        "related_registry_ids": list(data.get("related_registry_ids") or []),
        "apis": list(data.get("apis") or []),
        "metrics_exposed": list(data.get("metrics_exposed") or []),
        "aggregation_rules": data.get("aggregation_rules") or "À documenter",
        "update_history": list(data.get("update_history") or [])
        + [{"at": _now()[:10], "note": "Enregistrement NDF"}],
        "integration_module": data.get("integration_module"),
        "data_path": data.get("data_path"),
        "registered_at": _now(),
    }

    if idx is None:
        existing.append(record)
    else:
        existing[idx] = record

    extensions["registries"] = existing
    extensions["_meta"] = {
        **(extensions.get("_meta") or {}),
        "version": ENGINE_VERSION,
        "updated_at": _now(),
        "count": len(existing),
    }
    _save_json(EXTENSIONS_PATH, extensions)
    return {
        "_meta": {"version": ENGINE_VERSION, "action": "registered", "updated_at": _now()},
        "registry": record,
    }


def compute_quality(registry_id: str) -> dict[str, Any]:
    """Indicateurs qualité communs — valeurs réelles si source connue, sinon insuffisant."""
    item = _find(registry_id)
    if not item:
        return {
            "_meta": {"version": ENGINE_VERSION, "registry_id": registry_id},
            "indicators": [_insufficient(d) for d in QUALITY_DIMENSIONS],
            "status": "unknown_registry",
        }

    baseline = item.get("quality_baseline")
    indicators: list[dict[str, Any]] = []

    if baseline == "nci_quality_report":
        indicators = _quality_from_nci()
    elif baseline == "master_registry":
        indicators = _quality_from_master()
    elif baseline == "official_referentials":
        indicators = _quality_administrative()
    elif item.get("status") == "planned" or baseline in {"not_measured", None}:
        indicators = [
            _insufficient(d, "Référentiel planifié ou sans mesure qualité branchée")
            for d in QUALITY_DIMENSIONS
        ]
    else:
        # Actifs composés : fraîcheur via update_history, reste non inventé
        history = item.get("update_history") or []
        last = history[-1]["at"] if history else None
        indicators = [
            _insufficient("completeness", f"baseline={baseline} — pas de score inventé"),
            _measured("freshness", None if not last else 1, f"Dernière note : {last}", "update_history")
            if last
            else _insufficient("freshness"),
            _insufficient("coherence", f"baseline={baseline}"),
            _insufficient("geometry", f"baseline={baseline}"),
            _insufficient("precision", f"baseline={baseline}"),
        ]

    measured = sum(1 for i in indicators if i.get("status") == "ok")
    return {
        "_meta": {
            "version": ENGINE_VERSION,
            "registry_id": registry_id,
            "baseline": baseline,
            "updated_at": _now(),
            "rule": "Aucune note inventée",
        },
        "registry": {"id": item.get("id"), "name": item.get("name"), "status": item.get("status")},
        "indicators": indicators,
        "summary": {
            "dimensions": len(QUALITY_DIMENSIONS),
            "measured": measured,
            "insufficient": len(QUALITY_DIMENSIONS) - measured,
        },
    }


def _quality_from_nci() -> list[dict[str, Any]]:
    try:
        from api.services import coverage_intelligence_service

        report = coverage_intelligence_service.get_quality_report() or {}
        national = report.get("national_avg_quality") or {}
        uncovered = report.get("uncovered") or {}
        covered = report.get("covered") or {}
        avg_u = national.get("uncovered")
        avg_c = national.get("covered")
        generated = (report.get("_meta") or {}).get("generated_at")
        rows_u = uncovered.get("unique_keys")
        rows_c = covered.get("unique_keys")
        issues = (uncovered.get("issues") or {})
        dup = issues.get("duplicates")

        indicators = [
            _measured(
                "completeness",
                rows_u if rows_u is not None else None,
                f"Localités non couvertes uniques : {rows_u}; couvertes : {rows_c}",
                "data/coverage/quality_report.json",
            )
            if rows_u is not None
            else _insufficient("completeness"),
            _measured(
                "freshness",
                1 if generated else None,
                f"Rapport généré : {generated}" if generated else "Données insuffisantes",
                "quality_report._meta.generated_at",
            ),
            _measured(
                "coherence",
                dup if dup is not None else None,
                f"Doublons non couverts signalés : {dup}" if dup is not None else "Données insuffisantes",
                "quality_report.uncovered.issues",
            )
            if dup is not None
            else _insufficient("coherence"),
            _measured(
                "geometry",
                avg_u if avg_u is not None else None,
                f"Qualité moyenne NCI (uncovered) : {avg_u}",
                "national_avg_quality.uncovered",
            )
            if avg_u is not None
            else _insufficient("geometry"),
            _measured(
                "precision",
                avg_c if avg_c is not None else None,
                f"Qualité moyenne NCI (covered) : {avg_c}",
                "national_avg_quality.covered",
            )
            if avg_c is not None
            else _insufficient("precision"),
        ]
        return indicators
    except Exception:
        return [_insufficient(d, "NCI quality_report indisponible") for d in QUALITY_DIMENSIONS]


def _quality_from_master() -> list[dict[str, Any]]:
    try:
        from api.services import master_registry_service

        stats = master_registry_service.statistics() or {}
        total = stats.get("total") or stats.get("entities") or (stats.get("_meta") or {}).get("count")
        # Structure variable selon versions
        if total is None and isinstance(stats.get("by_type"), dict):
            total = sum(int(v or 0) for v in stats["by_type"].values())
        return [
            _measured("completeness", total, f"Entités Master Registry : {total}", "/api/master/statistics")
            if total is not None
            else _insufficient("completeness"),
            _insufficient("freshness", "Pas d'horloge globale MR exposée ici"),
            _insufficient("coherence", "Utiliser /api/master pour contrôles doublons"),
            _insufficient("geometry", "Géométries site-par-site dans MR"),
            _insufficient("precision", "confidence_level par entité"),
        ]
    except Exception:
        return [_insufficient(d, "Master Registry stats indisponibles") for d in QUALITY_DIMENSIONS]


def _quality_administrative() -> list[dict[str, Any]]:
    """Complétude géométrique via couches map — compte réel, pas de score inventé."""
    try:
        from api import main as api_main

        layers = {
            "provinces": "provinces",
            "territoires": "territoires",
            "collectivites": "collectivites",
        }
        counts = {}
        for key, layer in layers.items():
            fc = api_main.read_map_layer(layer, skip=0, limit=5000)
            feats = (fc or {}).get("features") or []
            with_geom = sum(1 for f in feats if f.get("geometry"))
            counts[key] = {"features": len(feats), "with_geometry": with_geom}
        prov = counts.get("provinces", {})
        return [
            _measured(
                "completeness",
                prov.get("features"),
                f"Provinces : {prov.get('features')}; territoires : {counts.get('territoires', {}).get('features')}; "
                f"collectivités : {counts.get('collectivites', {}).get('features')}",
                "/map/layers/*",
            ),
            _insufficient("freshness", "Horodatage import KMZ — voir manifests reports"),
            _insufficient("coherence", "Contrôles officiels via tests referential"),
            _measured(
                "geometry",
                prov.get("with_geometry"),
                f"Provinces avec géométrie : {prov.get('with_geometry')}/{prov.get('features')}",
                "/map/layers/provinces",
            ),
            _measured(
                "precision",
                None,
                "CRS EPSG:4326 documenté — précision source-dépendante",
                "crs",
            ),
        ]
    except Exception:
        return [_insufficient(d, "Couches administratives indisponibles") for d in QUALITY_DIMENSIONS]


def quality_overview() -> dict[str, Any]:
    rows = []
    for item in _all_registries():
        q = compute_quality(str(item["id"]))
        rows.append(
            {
                "id": item.get("id"),
                "name": item.get("name"),
                "status": item.get("status"),
                "measured": q.get("summary", {}).get("measured"),
                "insufficient": q.get("summary", {}).get("insufficient"),
                "indicators": q.get("indicators"),
            }
        )
    return {
        "_meta": {
            "version": ENGINE_VERSION,
            "count": len(rows),
            "dimensions": list(QUALITY_DIMENSIONS),
            "updated_at": _now(),
        },
        "registries": rows,
    }


def statistics() -> dict[str, Any]:
    regs = _all_registries()
    by_category: dict[str, int] = {}
    by_status: dict[str, int] = {}
    with_api = 0
    for r in regs:
        cat = str(r.get("category") or "unknown")
        st = str(r.get("status") or "unknown")
        by_category[cat] = by_category.get(cat, 0) + 1
        by_status[st] = by_status.get(st, 0) + 1
        if r.get("apis"):
            with_api += 1
    rel = list_relations()
    return {
        "_meta": {"version": ENGINE_VERSION, "updated_at": _now()},
        "registries_total": len(regs),
        "by_category": by_category,
        "by_status": by_status,
        "with_api": with_api,
        "relations_total": rel["_meta"]["count"],
        "relation_coherence_issues": rel["_meta"]["coherence_issues"],
        "extensions": len(_extension_registries()),
        "quality_dimensions": list(QUALITY_DIMENSIONS),
        "consumers": CONSUMERS,
    }


def consumers_compatibility() -> dict[str, Any]:
    """Compatibilité TST / Decision Engine / Knowledge Hub / NSME avec le NDF."""
    known = {str(r.get("id")) for r in _all_registries()}
    payload = []
    for key, info in CONSUMERS.items():
        missing = [u for u in info["uses"] if u not in known]
        payload.append(
            {
                "consumer_id": key,
                "name": info["name"],
                "api": info["api"],
                "uses": info["uses"],
                "missing_registries": missing,
                "compatible": len(missing) == 0,
            }
        )
    return {
        "_meta": {
            "version": ENGINE_VERSION,
            "updated_at": _now(),
            "note": "Les moteurs interrogent /api/national-data-fabric pour métadonnées et qualité",
        },
        "consumers": payload,
    }
