"""National Coverage Intelligence (NCI) — Référentiel National des Besoins Numériques.

Patrimoine de connaissance distinct du Référentiel National des Actifs.
Lecture seule, cache mémoire, agrégats précalculés.
"""

from __future__ import annotations

import json
import time
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterator

PROJECT_ROOT = Path(__file__).resolve().parents[2]
COVERAGE_DIR = PROJECT_ROOT / "data" / "coverage"
ENGINE_VERSION = "nci-1.0.0"

_CACHE: dict[str, Any] = {"mtime": None, "aggregates": None, "config": None, "manifest": None, "quality": None}
_LOCALITY_CACHE: dict[str, Any] = {"mtime": None, "uncovered": None, "covered": None}


def _now_ms() -> float:
    return time.time() * 1000


def _file_mtime(path: Path) -> float | None:
    return path.stat().st_mtime if path.exists() else None


def _load_json(path: Path) -> Any:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _invalidate_if_stale() -> None:
    agg = COVERAGE_DIR / "aggregates.json"
    mtime = _file_mtime(agg)
    if _CACHE["mtime"] != mtime:
        _CACHE.clear()
        _CACHE.update({"mtime": mtime, "aggregates": None, "config": None, "manifest": None, "quality": None})
        _LOCALITY_CACHE.clear()
        _LOCALITY_CACHE.update({"mtime": None, "uncovered": None, "covered": None})


def get_config() -> dict[str, Any]:
    _invalidate_if_stale()
    if _CACHE["config"] is None:
        _CACHE["config"] = _load_json(COVERAGE_DIR / "nci_config.json") or {}
    return _CACHE["config"]


def get_manifest() -> dict[str, Any]:
    _invalidate_if_stale()
    if _CACHE["manifest"] is None:
        _CACHE["manifest"] = _load_json(COVERAGE_DIR / "manifest.json") or {
            "_meta": {"status": "not_imported"},
            "counts": {},
        }
    return _CACHE["manifest"]


def get_aggregates() -> dict[str, Any]:
    _invalidate_if_stale()
    if _CACHE["aggregates"] is None:
        _CACHE["aggregates"] = _load_json(COVERAGE_DIR / "aggregates.json") or {}
    return _CACHE["aggregates"]


def get_quality_report() -> dict[str, Any]:
    _invalidate_if_stale()
    if _CACHE["quality"] is None:
        _CACHE["quality"] = _load_json(COVERAGE_DIR / "quality_report.json") or {}
    return _CACHE["quality"]


def _iter_jsonl(path: Path) -> Iterator[dict[str, Any]]:
    if not path.exists():
        return
        yield  # pragma: no cover
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


_UNCOVERED_DISK_CACHE = PROJECT_ROOT / "data" / "cache" / "nci_localities_uncovered_v1.json"
_LOCALITY_LOAD_LOCK = __import__("threading").RLock()


def _load_localities(dataset: str) -> list[dict[str, Any]]:
    """Charge localités covered/uncovered — cache mémoire + slim disque (uncovered)."""
    _invalidate_if_stale()
    key = "uncovered" if dataset == "uncovered" else "covered"
    path = COVERAGE_DIR / ("localities_uncovered.jsonl" if key == "uncovered" else "localities_covered.jsonl")
    mtime = _file_mtime(path)
    size = int(path.stat().st_size) if path.exists() else 0

    with _LOCALITY_LOAD_LOCK:
        if _LOCALITY_CACHE.get(key) is not None and _LOCALITY_CACHE.get(f"mtime_{key}") == mtime:
            return _LOCALITY_CACHE[key] or []

        # Projection slim disque pour uncovered (évite reparse JSONL ~22 Mo)
        if key == "uncovered" and _UNCOVERED_DISK_CACHE.exists():
            try:
                doc = json.loads(_UNCOVERED_DISK_CACHE.read_text(encoding="utf-8"))
                meta = doc.get("_meta") or {}
                if float(meta.get("mtime") or -1) == float(mtime or -2) and int(meta.get("size") or -1) == size:
                    rows = list(doc.get("localities") or [])
                    _LOCALITY_CACHE[key] = rows
                    _LOCALITY_CACHE[f"mtime_{key}"] = mtime
                    _LOCALITY_CACHE["mtime"] = mtime
                    return rows
            except Exception:
                pass

        rows = list(_iter_jsonl(path))
        _LOCALITY_CACHE[key] = rows
        _LOCALITY_CACHE[f"mtime_{key}"] = mtime
        _LOCALITY_CACHE["mtime"] = mtime

        if key == "uncovered" and rows:
            try:
                _UNCOVERED_DISK_CACHE.parent.mkdir(parents=True, exist_ok=True)
                payload = {
                    "_meta": {
                        "engine": "nci-uncovered-projection-v1",
                        "source": str(path),
                        "mtime": mtime,
                        "size": size,
                        "count": len(rows),
                    },
                    "localities": rows,
                }
                tmp = _UNCOVERED_DISK_CACHE.with_suffix(".tmp")
                tmp.write_text(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
                tmp.replace(_UNCOVERED_DISK_CACHE)
            except Exception:
                pass
        return rows


def _norm(text: str | None) -> str:
    return (text or "").strip().lower()


def overview() -> dict[str, Any]:
    agg = get_aggregates()
    manifest = get_manifest()
    national = agg.get("national") or {}
    return {
        "_meta": {
            "engine": ENGINE_VERSION,
            "heritage": "Référentiel National des Besoins Numériques",
            "assets_counterpart": "Référentiel National des Actifs",
            "generated_at": (agg.get("_meta") or {}).get("generated_at"),
        },
        "manifest": {
            "sources": manifest.get("sources"),
            "counts": manifest.get("counts"),
        },
        "national": national,
        "config": {
            "ndci": (get_config().get("national_digital_coverage_index") or {}).get("id"),
            "cdqs": (get_config().get("data_quality") or {}).get("id"),
        },
        "endpoints": [
            "/api/coverage",
            "/api/coverage/statistics",
            "/api/coverage/provinces",
            "/api/coverage/territories",
            "/api/coverage/localities",
            "/api/coverage/population",
            "/api/coverage/priority",
            "/api/coverage/categories",
            "/api/coverage/infrastructure",
            "/api/coverage/map",
            "/api/coverage/explain",
        ],
    }


def statistics() -> dict[str, Any]:
    agg = get_aggregates()
    national = agg.get("national") or {}
    quality = get_quality_report()
    return {
        "_meta": {"engine": ENGINE_VERSION},
        "kpis": {
            "localities_uncovered": national.get("localities_uncovered"),
            "localities_covered": national.get("localities_covered"),
            "population_uncovered": national.get("population_uncovered"),
            "population_covered": national.get("population_covered"),
            "population_remaining": national.get("population_remaining"),
            "population_total_observed": national.get("population_total_observed"),
            "avg_distance_km_uncovered": national.get("avg_distance_km_uncovered"),
            "coverage_ratio_localities": national.get("coverage_ratio_localities"),
            "coverage_ratio_population": national.get("coverage_ratio_population"),
            "avg_data_quality_uncovered": national.get("avg_data_quality_uncovered"),
        },
        "priorities": national.get("priorities_uncovered") or {},
        "categories": national.get("categories_uncovered") or {},
        "quality": quality.get("national_avg_quality") or {},
        "ndci_top": (agg.get("ndci_top_territories") or [])[:10],
    }


def list_provinces(limit: int = 100) -> dict[str, Any]:
    by_p = (get_aggregates().get("by_province") or {})
    items = sorted(
        by_p.values(),
        key=lambda x: int(x.get("population_uncovered") or 0),
        reverse=True,
    )[:limit]
    return {"_meta": {"engine": ENGINE_VERSION, "count": len(items)}, "provinces": items}


def list_territories(
    province: str | None = None,
    q: str | None = None,
    limit: int = 500,
) -> dict[str, Any]:
    by_t = get_aggregates().get("by_territory") or {}
    items = []
    for name, row in by_t.items():
        if province and _norm(row.get("province")) != _norm(province):
            continue
        if q and q.lower() not in _norm(name) and q.lower() not in _norm(row.get("province")):
            continue
        items.append(row)
    items.sort(key=lambda x: float(((x.get("ndci") or {}).get("index")) or 0), reverse=True)
    items = items[:limit]
    return {"_meta": {"engine": ENGINE_VERSION, "count": len(items)}, "territories": items}


def get_territory_coverage(territory_name: str) -> dict[str, Any] | None:
    by_t = get_aggregates().get("by_territory") or {}
    # Exact then fuzzy
    if territory_name in by_t:
        row = by_t[territory_name]
    else:
        row = None
        for name, candidate in by_t.items():
            if _norm(name) == _norm(territory_name):
                row = candidate
                break
    if not row:
        return None
    return {
        "_meta": {"engine": ENGINE_VERSION, "source": "data/coverage/aggregates.json"},
        "territory": row,
        "explain": explain_territory_index(row.get("territoire") or territory_name),
    }


def list_localities(
    *,
    status: str | None = None,
    province: str | None = None,
    territoire: str | None = None,
    priority: str | None = None,
    categorie: str | None = None,
    q: str | None = None,
    limit: int = 200,
    offset: int = 0,
) -> dict[str, Any]:
    datasets: list[str] = []
    if status in (None, "all"):
        datasets = ["uncovered", "covered"]
    elif status == "uncovered":
        datasets = ["uncovered"]
    elif status == "covered":
        datasets = ["covered"]
    else:
        datasets = ["uncovered", "covered"]

    matched: list[dict[str, Any]] = []
    total_scanned = 0
    for ds in datasets:
        for row in _load_localities(ds):
            if row.get("duplicate"):
                continue
            total_scanned += 1
            if province and _norm(row.get("province")) != _norm(province):
                continue
            if territoire and _norm(row.get("territoire")) != _norm(territoire):
                continue
            if priority and _norm(row.get("priority")) != _norm(priority):
                continue
            if categorie and _norm(row.get("categorie")) != _norm(categorie):
                continue
            if q:
                blob = " ".join(
                    str(row.get(k) or "")
                    for k in ("name", "province", "territoire", "destination", "infra_name")
                ).lower()
                if q.lower() not in blob:
                    continue
            matched.append(row)

    total = len(matched)
    page = matched[offset : offset + limit]
    return {
        "_meta": {
            "engine": ENGINE_VERSION,
            "total": total,
            "offset": offset,
            "limit": limit,
            "scanned": total_scanned,
            "progressive": True,
        },
        "localities": page,
    }


def population_payload() -> dict[str, Any]:
    national = (get_aggregates().get("national") or {})
    top_prov = sorted(
        (get_aggregates().get("by_province") or {}).values(),
        key=lambda x: int(x.get("population_uncovered") or 0),
        reverse=True,
    )[:15]
    return {
        "_meta": {"engine": ENGINE_VERSION},
        "national": {
            "population_covered": national.get("population_covered"),
            "population_remaining": national.get("population_remaining"),
            "population_uncovered": national.get("population_uncovered"),
            "population_total_observed": national.get("population_total_observed"),
            "coverage_ratio_population": national.get("coverage_ratio_population"),
        },
        "top_provinces_remaining": [
            {
                "province": p.get("province"),
                "population_remaining": p.get("population_uncovered"),
                "population_covered": p.get("population_covered"),
            }
            for p in top_prov
        ],
    }


def priority_payload() -> dict[str, Any]:
    national = get_aggregates().get("national") or {}
    return {
        "_meta": {"engine": ENGINE_VERSION},
        "uncovered": national.get("priorities_uncovered") or {},
        "covered": national.get("priorities_covered") or {},
        "valid_priorities": get_config().get("valid_priorities") or ["High", "Medium", "Low"],
    }


def categories_payload() -> dict[str, Any]:
    national = get_aggregates().get("national") or {}
    return {
        "_meta": {"engine": ENGINE_VERSION},
        "categories": national.get("categories_uncovered") or {},
        "note": "Catégories issues du fichier Localités non couvertes (A–E, >10000).",
    }


def infrastructure_payload() -> dict[str, Any]:
    national = get_aggregates().get("national") or {}
    return {
        "_meta": {"engine": ENGINE_VERSION},
        "infra_types": national.get("infra_types_uncovered") or {},
        "note": "Types d'infrastructures essentielles associées aux localités non couvertes.",
    }


def map_payload(
    *,
    status: str = "uncovered",
    province: str | None = None,
    territoire: str | None = None,
    priority: str | None = None,
    limit: int = 5000,
) -> dict[str, Any]:
    result = list_localities(
        status=status,
        province=province,
        territoire=territoire,
        priority=priority,
        limit=limit,
        offset=0,
    )
    features = []
    for row in result["localities"]:
        lat, lon = row.get("latitude"), row.get("longitude")
        if lat is None or lon is None or not row.get("coords_valid"):
            continue
        features.append(
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [lon, lat]},
                "properties": {
                    "id": row.get("id"),
                    "name": row.get("name"),
                    "coverage_status": row.get("coverage_status"),
                    "priority": row.get("priority"),
                    "categorie": row.get("categorie"),
                    "population": row.get("population"),
                    "province": row.get("province"),
                    "territoire": row.get("territoire"),
                    "distance_km": row.get("distance_km"),
                    "infra_type": row.get("infra_type"),
                },
            }
        )
    return {
        "type": "FeatureCollection",
        "features": features,
        "_meta": {
            "engine": ENGINE_VERSION,
            "count": len(features),
            "status": status,
            "limit": limit,
            "note": "Chargement progressif — utiliser province/territoire pour affiner.",
        },
    }


def explain_territory_index(territory_name: str) -> dict[str, Any]:
    by_t = get_aggregates().get("by_territory") or {}
    row = None
    for name, candidate in by_t.items():
        if _norm(name) == _norm(territory_name):
            row = candidate
            break
    if not row:
        return {
            "available": False,
            "why": "Territoire absent du Référentiel National des Besoins.",
            "confidence_level": "low",
        }
    ndci = row.get("ndci") or {}
    components = ndci.get("components") or {}
    return {
        "available": True,
        "territoire": row.get("territoire"),
        "province": row.get("province"),
        "ndci": ndci.get("index"),
        "ndci_id": ndci.get("id"),
        "ndci_version": ndci.get("version"),
        "why": (
            f"Indice NDCI {ndci.get('index')}/100 calculé sur population restante, "
            f"priorités, catégories, distance moyenne et infrastructures essentielles."
        ),
        "population": {
            "covered": row.get("population_covered"),
            "remaining": row.get("population_remaining"),
            "uncovered": row.get("population_uncovered"),
        },
        "priority": row.get("priorities"),
        "distance_km_avg": row.get("avg_distance_km"),
        "categories": row.get("categories"),
        "infrastructure": row.get("infra_types"),
        "components": components,
        "weights": ndci.get("weights"),
        "data_quality_avg": row.get("data_quality_avg"),
        "doctrine_note": "L'indice NCI alimente le Decision Engine en complément doctrine/matrice/sites/CCN.",
        "confidence_level": (
            "high"
            if (row.get("data_quality_avg") or 0) >= 80
            else "medium"
            if (row.get("data_quality_avg") or 0) >= 55
            else "low"
        ),
        "sources": [
            "data/coverage/aggregates.json",
            "data/coverage/nci_config.json",
            "data/raw/Localités non couvertes_*.xlsx",
            "data/raw/Population coverage-*.xlsx",
        ],
    }


def knowledge_domain_payload() -> dict[str, Any]:
    stats = statistics()
    return {
        "id": "national_coverage",
        "name": "National Coverage",
        "heritage": "Référentiel National des Besoins",
        "kpis": stats.get("kpis"),
        "priorities": stats.get("priorities"),
        "categories": stats.get("categories"),
        "infra_types": (get_aggregates().get("national") or {}).get("infra_types_uncovered"),
        "avg_distance_km": (get_aggregates().get("national") or {}).get("avg_distance_km_uncovered"),
        "sources": (get_manifest().get("sources") or []),
    }


def edvs_charts() -> dict[str, Any]:
    """Payloads graphiques exécutifs alimentés par NCI."""
    national = get_aggregates().get("national") or {}
    pri = national.get("priorities_uncovered") or {}
    cats = national.get("categories_uncovered") or {}
    top_prov = sorted(
        (get_aggregates().get("by_province") or {}).values(),
        key=lambda x: int(x.get("population_uncovered") or 0),
        reverse=True,
    )[:8]
    top_terr = (get_aggregates().get("ndci_top_territories") or [])[:8]

    return {
        "kpis": [
            {
                "id": "pop_covered",
                "label": "Population nationale couverte",
                "value": national.get("population_covered"),
                "icon": "people",
                "color": "green",
                "confidence": "high",
            },
            {
                "id": "pop_remaining",
                "label": "Population restante",
                "value": national.get("population_remaining"),
                "icon": "people",
                "color": "orange",
                "confidence": "high",
            },
            {
                "id": "loc_covered",
                "label": "Localités couvertes",
                "value": national.get("localities_covered"),
                "icon": "map",
                "color": "green",
                "confidence": "high",
            },
            {
                "id": "loc_uncovered",
                "label": "Localités non couvertes",
                "value": national.get("localities_uncovered"),
                "icon": "map",
                "color": "red",
                "confidence": "high",
            },
        ],
        "bars": {
            "title": "Top provinces — population restante",
            "items": [
                {
                    "label": p.get("province"),
                    "value": p.get("population_uncovered"),
                    "color": "orange",
                }
                for p in top_prov
            ],
        },
        "priority_split": {
            "title": "Répartition High / Medium / Low",
            "items": [
                {"label": "High", "value": pri.get("High") or 0, "color": "red"},
                {"label": "Medium", "value": pri.get("Medium") or 0, "color": "orange"},
                {"label": "Low", "value": pri.get("Low") or 0, "color": "yellow"},
            ],
        },
        "categories": {
            "title": "Répartition catégories",
            "items": [
                {"label": k, "value": v, "color": "blue"}
                for k, v in sorted(cats.items(), key=lambda x: -x[1])
            ],
        },
        "treemap": {
            "title": "Besoins par province (population restante)",
            "items": [
                {
                    "label": p.get("province"),
                    "value": p.get("population_uncovered"),
                    "color": "orange",
                }
                for p in top_prov
            ],
        },
        "heatmap": {
            "title": "Carte thermique des besoins (NDCI territoires)",
            "rows": [t.get("territoire", "")[:18] for t in top_terr],
            "cols": ["NDCI"],
            "matrix": [[int((t.get("index") or 0))] for t in top_terr],
        },
        "radar": {
            "title": "Profil national des besoins",
            "axes": [
                {
                    "label": "Priorité High",
                    "value": min(100, int(100 * (pri.get("High") or 0) / max(sum(pri.values()) or 1, 1))),
                },
                {
                    "label": "Pop. restante",
                    "value": min(
                        100,
                        int(
                            100
                            * (national.get("population_remaining") or 0)
                            / max(national.get("population_total_observed") or 1, 1)
                        ),
                    ),
                },
                {
                    "label": "Localités non couvertes",
                    "value": min(
                        100,
                        int(
                            100
                            * (national.get("localities_uncovered") or 0)
                            / max(
                                (national.get("localities_uncovered") or 0)
                                + (national.get("localities_covered") or 0),
                                1,
                            )
                        ),
                    ),
                },
                {
                    "label": "Qualité données",
                    "value": int(national.get("avg_data_quality_uncovered") or 0),
                },
            ],
            "note": "Axes dérivés des agrégats NCI officiels.",
        },
        "waterfall": {
            "title": "Évolution couverture (stock observé)",
            "steps": [
                {
                    "label": "Population observée",
                    "value": national.get("population_total_observed"),
                    "color": "blue",
                },
                {
                    "label": "Population couverte",
                    "value": national.get("population_covered"),
                    "color": "green",
                },
                {
                    "label": "Population restante",
                    "value": national.get("population_remaining"),
                    "color": "orange",
                },
            ],
        },
        "sparkline_coverage_ratio": [
            0,
            round(float(national.get("coverage_ratio_population") or 0) * 50, 2),
            round(float(national.get("coverage_ratio_population") or 0) * 100, 2),
        ],
        "top_territories": top_terr,
    }


@lru_cache(maxsize=1)
def _warm() -> str:
    get_aggregates()
    return ENGINE_VERSION
