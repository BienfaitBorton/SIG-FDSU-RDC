"""Tableau de Synthèse Territoriale (TST) — agrégations réelles uniquement.

Aucune valeur inventée. Si une métrique est absente → status insufficient.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from psycopg2.extras import RealDictCursor

from api.config import connect_db
from api.services import (
    ccn_operational_service,
    coverage_intelligence_service,
    health_service,
    territorial_intelligence_service,
)

ENGINE_VERSION = "tst-1.1.0"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _norm(value: Any) -> str:
    return " ".join(str(value or "").strip().lower().split())


def _admin_key(value: Any) -> str:
    """Clé administrative stricte (pas de sous-chaîne) — évite Haut-Lomami ↔ Lomami."""
    return " ".join(str(value or "").strip().upper().replace("-", " ").replace("_", " ").split())


def _admin_eq(a: Any, b: Any) -> bool:
    ka, kb = _admin_key(a), _admin_key(b)
    return bool(ka and kb and ka == kb)


def _safe(fn, default=None):
    try:
        return fn()
    except Exception:
        return default


def _map_layer_fc(layer_name: str) -> dict[str, Any]:
    """Source géométrique unique : même pipeline que /map/layers/{layer} (PostGIS ou rapports)."""
    try:
        from api import main as api_main

        payload = api_main.read_map_layer(layer_name, skip=0, limit=5000)
        if isinstance(payload, dict) and payload.get("type") == "FeatureCollection":
            return payload
    except Exception:
        pass
    return {"type": "FeatureCollection", "features": []}


def _geometry_status(expected: int, with_geom: int) -> str:
    if with_geom <= 0:
        return "unavailable"
    if expected > 0 and with_geom < expected:
        return "partial"
    return "complete"


def _insufficient_metric(metric: dict[str, Any]) -> dict[str, Any]:
    return {
        "value": None,
        "display": "Données insuffisantes",
        "class_id": "insufficient",
        "class_label": "Données insuffisantes",
        "objects_count": 0,
        "status": "insufficient",
        "source": metric.get("source"),
    }


def _territory_metric(metric_id: str, crow: dict | None, metric: dict[str, Any]) -> dict[str, Any]:
    if metric_id in ("needs", "coverage") and crow:
        return {
            **_metric_value(
                metric_id,
                None,
                {
                    **crow,
                    "coverage_ratio": (
                        int(crow.get("localities_covered") or 0)
                        / max(
                            1,
                            int(crow.get("localities_covered") or 0) + int(crow.get("localities_uncovered") or 0),
                        )
                    )
                    if (
                        crow.get("localities_covered") is not None
                        or crow.get("localities_uncovered") is not None
                    )
                    else None,
                },
                None,
                None,
            ),
            "source": metric.get("source"),
        }
    ndci = (crow or {}).get("ndci") or {}
    if metric_id == "priority" and ndci.get("index") is not None:
        score = float(ndci["index"])
        return {
            "value": score,
            "display": str(score),
            "class_id": _priority_class(score),
            "class_label": f"NDCI {ndci.get('label') or score}",
            "objects_count": 1,
            "status": "ok",
            "source": "coverage aggregates / ndci",
        }
    return _insufficient_metric(metric)


def _find_parent_feature(
    layer_name: str,
    name: str,
    *,
    province: str | None = None,
    level: str,
    administrative_level: str,
    name_keys: tuple[str, ...] = ("nom", "name"),
) -> dict[str, Any] | None:
    for feature in (_map_layer_fc(layer_name).get("features") or []):
        props = feature.get("properties") or {}
        fname = next((props.get(k) for k in name_keys if props.get(k)), None)
        if not _admin_eq(fname, name):
            continue
        if province and props.get("province") and not _admin_eq(props.get("province"), province):
            continue
        if not feature.get("geometry"):
            continue
        return {
            "type": "Feature",
            "id": props.get("id") or _norm(fname),
            "properties": {
                "id": props.get("id") or _norm(fname),
                "name": fname,
                "level": level,
                "administrative_level": administrative_level,
                "province": props.get("province") or province,
                "territoire": props.get("territoire"),
            },
            "geometry": feature["geometry"],
        }
    return None


METRICS: list[dict[str, Any]] = [
    {
        "id": "priority",
        "label": "Niveau de priorité territoriale",
        "unit": "score",
        "description": "Score 0–100 dérivé du ratio sites prioritaires (critical+high) / sites scorés par province.",
        "source": "decision.fdsu_site_scores + programs.fdsu_sites",
        "aggregation": "GROUP BY province — (critical+high)/scored * 100",
        "primary": True,
    },
    {
        "id": "sites_fdsu",
        "label": "Sites FDSU",
        "unit": "count",
        "description": "Nombre de sites FDSU géoréférencés par province.",
        "source": "programs.fdsu_sites",
        "aggregation": "COUNT(*) GROUP BY province",
    },
    {
        "id": "sites_priority",
        "label": "Sites prioritaires",
        "unit": "count",
        "description": "Sites critical + high par province.",
        "source": "decision.fdsu_site_scores",
        "aggregation": "COUNT(*) WHERE priority_level IN ('critical','high') GROUP BY province",
    },
    {
        "id": "needs",
        "label": "Besoins de connectivité",
        "unit": "population",
        "description": "Population non couverte (NCI) par province.",
        "source": "data/coverage/aggregates.json (by_province.population_uncovered)",
        "aggregation": "Lecture agrégats NCI pré-calculés",
    },
    {
        "id": "coverage",
        "label": "Couverture",
        "unit": "ratio",
        "description": "Part de localités couvertes = covered / (covered+uncovered).",
        "source": "data/coverage/aggregates.json",
        "aggregation": "localities_covered / (covered+uncovered)",
    },
    {
        "id": "health",
        "label": "Santé",
        "unit": "count",
        "description": "Établissements de santé par province.",
        "source": "health.health_facilities (statistics.by_province)",
        "aggregation": "COUNT(*) GROUP BY province_name",
    },
    {
        "id": "ccn",
        "label": "CCN",
        "unit": "count",
        "description": "Centres communautaires numériques par province (jeu DEMO si applicable).",
        "source": "/api/ccn/statistics by_province",
        "aggregation": "COUNT CCN GROUP BY province",
    },
    {
        "id": "accessibility",
        "label": "Accessibilité",
        "unit": "score",
        "description": "Score moyen d'accessibilité routière des sites FDSU (distance + type de route — formule documentée).",
        "source": "transport.routes + programs.fdsu_sites via /api/transport",
        "aggregation": "AVG(accessibility_score) GROUP BY province — sites géoréférencés uniquement",
    },
    {
        "id": "data_quality",
        "label": "Qualité des données",
        "unit": "score",
        "description": "Proxy : part de localités NCI avec population renseignée vs total (si disponible).",
        "source": "coverage aggregates + reference quality (si présent)",
        "aggregation": "Heuristique documentée — insuffisante si source absente",
    },
]


def list_metrics() -> dict[str, Any]:
    return {
        "_meta": {
            "title": "Métriques TST",
            "version": ENGINE_VERSION,
            "updated_at": _now(),
            "rule": "Aucune métrique inventée — valeurs absentes → Données insuffisantes",
        },
        "metrics": METRICS,
        "default_metric": "priority",
    }


def _sites_by_province() -> dict[str, dict[str, Any]]:
    """Agrège sites FDSU et scores de priorité par province (DB)."""
    out: dict[str, dict[str, Any]] = {}
    try:
        with connect_db() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT COALESCE(NULLIF(TRIM(s.province), ''), 'Non renseigné') AS province,
                           COUNT(*)::int AS sites_fdsu
                    FROM programs.fdsu_sites s
                    GROUP BY 1
                    """
                )
                for row in cur.fetchall() or []:
                    key = str(row["province"])
                    out[_norm(key)] = {
                        "province": key,
                        "sites_fdsu": int(row["sites_fdsu"] or 0),
                        "sites_scored": 0,
                        "sites_priority": 0,
                        "sites_critical": 0,
                        "sites_high": 0,
                    }
                cur.execute(
                    """
                    SELECT COALESCE(NULLIF(TRIM(s.province), ''), 'Non renseigné') AS province,
                           COUNT(*)::int AS scored,
                           COUNT(*) FILTER (WHERE sc.priority_level = 'critical')::int AS critical,
                           COUNT(*) FILTER (WHERE sc.priority_level = 'high')::int AS high,
                           COUNT(*) FILTER (
                             WHERE sc.priority_level IN ('critical', 'high')
                           )::int AS priority
                    FROM decision.fdsu_site_scores sc
                    JOIN programs.fdsu_sites s ON s.id = sc.site_id
                    GROUP BY 1
                    """
                )
                for row in cur.fetchall() or []:
                    key = str(row["province"])
                    bucket = out.setdefault(
                        _norm(key),
                        {
                            "province": key,
                            "sites_fdsu": 0,
                            "sites_scored": 0,
                            "sites_priority": 0,
                            "sites_critical": 0,
                            "sites_high": 0,
                        },
                    )
                    bucket["sites_scored"] = int(row["scored"] or 0)
                    bucket["sites_critical"] = int(row["critical"] or 0)
                    bucket["sites_high"] = int(row["high"] or 0)
                    bucket["sites_priority"] = int(row["priority"] or 0)
    except Exception:
        return out
    return out


def _coverage_by_province() -> dict[str, dict[str, Any]]:
    payload = _safe(lambda: coverage_intelligence_service.list_provinces(limit=100), {}) or {}
    out: dict[str, dict[str, Any]] = {}
    for row in payload.get("provinces") or []:
        name = row.get("province")
        if not name:
            continue
        covered = int(row.get("localities_covered") or 0)
        uncovered = int(row.get("localities_uncovered") or 0)
        total = covered + uncovered
        out[_norm(name)] = {
            **row,
            "coverage_ratio": (covered / total) if total else None,
        }
    return out


def _health_by_province() -> dict[str, int]:
    stats = _safe(health_service.get_statistics, {}) or {}
    by_p = stats.get("by_province") or (stats.get("details") or {}).get("by_province") or {}
    if isinstance(by_p, list):
        out = {}
        for item in by_p:
            if isinstance(item, dict):
                out[_norm(item.get("province") or item.get("name"))] = int(item.get("count") or item.get("value") or 0)
        return out
    return {_norm(k): int(v or 0) for k, v in by_p.items()}


def _ccn_by_province() -> dict[str, int]:
    stats = _safe(ccn_operational_service.statistics, {}) or {}
    by_p = stats.get("by_province") or {}
    return {_norm(k): int(v or 0) for k, v in by_p.items()}


def _metric_value(
    metric_id: str,
    site_row: dict | None,
    cov_row: dict | None,
    health: int | None,
    ccn: int | None,
    access: dict | None = None,
) -> dict[str, Any]:
    """Retourne value, class, status, objects_count."""
    insufficient = {
        "value": None,
        "display": "Données insuffisantes",
        "class_id": "insufficient",
        "class_label": "Données insuffisantes",
        "objects_count": 0,
        "status": "insufficient",
    }
    mid = metric_id or "priority"

    if mid == "sites_fdsu":
        if not site_row:
            return insufficient
        v = int(site_row.get("sites_fdsu") or 0)
        return {
            "value": v,
            "display": str(v),
            "class_id": _count_class(v, [1, 10, 40]),
            "class_label": _count_class_label(v, [1, 10, 40]),
            "objects_count": v,
            "status": "ok",
        }
    if mid == "sites_priority":
        if not site_row:
            return insufficient
        v = int(site_row.get("sites_priority") or 0)
        return {
            "value": v,
            "display": str(v),
            "class_id": _count_class(v, [1, 5, 20]),
            "class_label": _count_class_label(v, [1, 5, 20]),
            "objects_count": v,
            "status": "ok",
        }
    if mid == "priority":
        if not site_row or not int(site_row.get("sites_scored") or 0):
            return insufficient
        scored = int(site_row["sites_scored"])
        priority = int(site_row.get("sites_priority") or 0)
        score = round(100.0 * priority / scored, 1)
        return {
            "value": score,
            "display": f"{score}",
            "class_id": _priority_class(score),
            "class_label": _priority_label(score),
            "objects_count": scored,
            "status": "ok",
        }
    if mid == "needs":
        if not cov_row or cov_row.get("population_uncovered") is None:
            return insufficient
        v = int(cov_row.get("population_uncovered") or 0)
        return {
            "value": v,
            "display": f"{v:,}".replace(",", " "),
            "class_id": _count_class(v, [100_000, 1_000_000, 3_000_000]),
            "class_label": _count_class_label(v, [100_000, 1_000_000, 3_000_000]),
            "objects_count": int(cov_row.get("localities_uncovered") or 0),
            "status": "ok",
        }
    if mid == "coverage":
        if not cov_row or cov_row.get("coverage_ratio") is None:
            return insufficient
        ratio = float(cov_row["coverage_ratio"])
        pct = round(ratio * 100, 1)
        return {
            "value": pct,
            "display": f"{pct} %",
            "class_id": _coverage_class(pct),
            "class_label": _coverage_label(pct),
            "objects_count": int(cov_row.get("localities_covered") or 0) + int(cov_row.get("localities_uncovered") or 0),
            "status": "ok",
        }
    if mid == "health":
        if health is None:
            return insufficient
        return {
            "value": health,
            "display": str(health),
            "class_id": _count_class(health, [100, 1000, 5000]),
            "class_label": _count_class_label(health, [100, 1000, 5000]),
            "objects_count": health,
            "status": "ok",
        }
    if mid == "ccn":
        if ccn is None:
            return insufficient
        return {
            "value": ccn,
            "display": str(ccn),
            "class_id": _count_class(ccn, [1, 3, 10]),
            "class_label": _count_class_label(ccn, [1, 3, 10]),
            "objects_count": ccn,
            "status": "ok" if ccn else "partial",
        }
    if mid == "accessibility":
        if not access or access.get("avg_score") is None:
            return insufficient
        score = float(access["avg_score"])
        # Réutilise classes priorité (score 0-100) — plus haut = meilleure accessibilité
        return {
            "value": score,
            "display": str(score),
            "class_id": _priority_class(score),
            "class_label": f"Accessibilité {score}",
            "objects_count": int(access.get("sites_scored") or 0),
            "status": "ok",
        }
    if mid == "data_quality":
        if not cov_row:
            return insufficient
        has_pop = cov_row.get("population_uncovered") is not None or cov_row.get("population_covered") is not None
        if not has_pop:
            return insufficient
        objects = int(cov_row.get("localities_uncovered") or 0) + int(cov_row.get("localities_covered") or 0)
        return {
            "value": 1,
            "display": "Agrégats disponibles",
            "class_id": "medium",
            "class_label": "Partiel (agrégats NCI présents)",
            "objects_count": objects,
            "status": "partial",
            "note": "Indicateur binaire de disponibilité des agrégats — pas un score inventé.",
        }
    return insufficient


def _count_class(v: float, breaks: list[int]) -> str:
    if v <= 0:
        return "none"
    if v < breaks[0]:
        return "low"
    if v < breaks[1]:
        return "medium"
    if v < breaks[2]:
        return "high"
    return "critical"


def _count_class_label(v: float, breaks: list[int]) -> str:
    return {
        "none": "Aucun",
        "low": "Faible",
        "medium": "Moyen",
        "high": "Élevé",
        "critical": "Très élevé",
    }.get(_count_class(v, breaks), "—")


def _priority_class(score: float) -> str:
    if score >= 60:
        return "critical"
    if score >= 40:
        return "high"
    if score >= 20:
        return "medium"
    if score > 0:
        return "low"
    return "none"


def _priority_label(score: float) -> str:
    return {
        "critical": "Priorité critique",
        "high": "Priorité élevée",
        "medium": "Priorité moyenne",
        "low": "Priorité faible",
        "none": "Sans priorité",
    }.get(_priority_class(score), "—")


def _coverage_class(pct: float) -> str:
    if pct >= 70:
        return "low"  # bien couvert → faible besoin
    if pct >= 40:
        return "medium"
    if pct >= 20:
        return "high"
    return "critical"


def _coverage_label(pct: float) -> str:
    return {
        "low": "Couverture satisfaisante",
        "medium": "Couverture partielle",
        "high": "Faible couverture",
        "critical": "Couverture critique",
    }.get(_coverage_class(pct), "—")


def _legend_for(metric_id: str) -> list[dict[str, str]]:
    if metric_id in ("priority",):
        return [
            {"class_id": "critical", "label": "Priorité critique (≥60)", "color": "#ef4444"},
            {"class_id": "high", "label": "Priorité élevée (40–59)", "color": "#f97316"},
            {"class_id": "medium", "label": "Priorité moyenne (20–39)", "color": "#ca8a04"},
            {"class_id": "low", "label": "Priorité faible (>0–19)", "color": "#4ade80"},
            {"class_id": "insufficient", "label": "Données insuffisantes", "color": "#64748b"},
        ]
    if metric_id == "coverage":
        return [
            {"class_id": "low", "label": "≥70 % couvert", "color": "#4ade80"},
            {"class_id": "medium", "label": "40–69 %", "color": "#ca8a04"},
            {"class_id": "high", "label": "20–39 %", "color": "#f97316"},
            {"class_id": "critical", "label": "<20 %", "color": "#ef4444"},
            {"class_id": "insufficient", "label": "Données insuffisantes", "color": "#64748b"},
        ]
    return [
        {"class_id": "none", "label": "Aucun", "color": "#94a3b8"},
        {"class_id": "low", "label": "Faible", "color": "#4ade80"},
        {"class_id": "medium", "label": "Moyen", "color": "#ca8a04"},
        {"class_id": "high", "label": "Élevé", "color": "#f97316"},
        {"class_id": "critical", "label": "Très élevé", "color": "#ef4444"},
        {"class_id": "insufficient", "label": "Données insuffisantes", "color": "#64748b"},
    ]


def build_province_layer(metric_id: str = "priority") -> dict[str, Any]:
    metric = next((m for m in METRICS if m["id"] == metric_id), METRICS[0])
    sites = _sites_by_province()
    coverage = _coverage_by_province()
    health = _health_by_province()
    ccn = _ccn_by_province()
    access = {}
    if metric["id"] == "accessibility":
        access = _safe(lambda: __import__("api.services.transport_service", fromlist=["accessibility_by_province"]).accessibility_by_province(), {}) or {}

    # Union of province names from real sources
    names: dict[str, str] = {}
    for bucket in (sites, coverage):
        for _k, row in bucket.items():
            pname = row.get("province")
            if not pname or _norm(pname) in {"#n/a", "n/a", "non renseigné", "null"}:
                continue
            names[_norm(pname)] = pname
    for key, _v in health.items():
        if key and key not in {"#n/a", "n/a", "non renseigné"} and key not in names:
            names[key] = key.title()
    for key, _v in ccn.items():
        if key and key not in {"#n/a", "n/a", "non renseigné"} and key not in names:
            names[key] = key.title()
    for key, _v in access.items():
        if key and key not in {"#n/a", "n/a", "non renseigné"} and key not in names:
            names[key] = key.title()

    features = []
    for key, display_name in sorted(names.items(), key=lambda x: x[1]):
        site_row = sites.get(key)
        cov_row = coverage.get(key)
        h = health.get(key)
        c = ccn.get(key) if key in ccn else (None if not ccn else 0)
        # CCN: if by_province exists but province missing → 0 is real (demo has subset)
        if ccn and key not in ccn:
            c = 0
        elif not ccn:
            c = None
        acc = access.get(key)

        measured = _metric_value(metric["id"], site_row, cov_row, h, c, access=acc)
        features.append(
            {
                "type": "Feature",
                "id": key,
                "properties": {
                    "id": key,
                    "name": display_name,
                    "level": "province",
                    "administrative_level": "Province",
                    "metric_id": metric["id"],
                    "metric_label": metric["label"],
                    "value": measured["value"],
                    "display": measured["display"],
                    "class_id": measured["class_id"],
                    "class_label": measured["class_label"],
                    "objects_count": measured["objects_count"],
                    "status": measured["status"],
                    "source": metric["source"],
                    "updated_at": _now(),
                    "sites_fdsu": (site_row or {}).get("sites_fdsu"),
                    "sites_priority": (site_row or {}).get("sites_priority"),
                    "population_uncovered": (cov_row or {}).get("population_uncovered"),
                    "population_covered": (cov_row or {}).get("population_covered"),
                    "localities_uncovered": (cov_row or {}).get("localities_uncovered"),
                    "localities_covered": (cov_row or {}).get("localities_covered"),
                    "health_facilities": h,
                    "ccn": c,
                    "accessibility_avg": (acc or {}).get("avg_score"),
                    "hint": "Cliquer pour explorer",
                },
                "geometry": None,  # géométrie fournie côté client via /map/layers/provinces
            }
        )

    return {
        "_meta": {
            "version": ENGINE_VERSION,
            "level": "province",
            "metric": metric,
            "count": len(features),
            "updated_at": _now(),
            "geometry_endpoint": "/map/layers/provinces?limit=5000",
            "geometry_source": "/map/layers/provinces (PostGIS provinces.geom ou Province26)",
            "rule": "Joindre properties.id / name aux features GeoJSON provinces côté client",
        },
        "level": "province",
        "parent": None,
        "legend": _legend_for(metric["id"]),
        "features": features,
        "type": "FeatureCollection",
        "expected_count": len(features),
        "geometry_count": None,
        "geometry_status": "complete",
        "message": None,
    }


def build_territory_layer(province_name: str, metric_id: str = "priority") -> dict[str, Any]:
    """Province → territoires : métriques TI/NCI + polygones /map/layers/territoires."""
    metric = next((m for m in METRICS if m["id"] == metric_id), METRICS[0])
    ti = _safe(
        lambda: territorial_intelligence_service.list_territories(province=province_name, limit=500),
        {},
    ) or {}
    cov = _safe(
        lambda: coverage_intelligence_service.list_territories(province=province_name, limit=500),
        {},
    ) or {}
    cov_rows = [
        t
        for t in (cov.get("territories") or [])
        if _admin_eq(t.get("province") or t.get("province_name"), province_name)
        or not (t.get("province") or t.get("province_name"))
    ]
    cov_by_name = {
        _admin_key(t.get("territoire") or t.get("territory_name") or t.get("name")): t for t in cov_rows
    }

    # Référentiel métrique : filtre province STRICT (évite fuite Lomami via sous-chaîne TI)
    metric_by_name: dict[str, dict[str, Any]] = {}
    for item in ti.get("items") or ti.get("territories") or []:
        if not _admin_eq(item.get("province"), province_name):
            continue
        name = item.get("territory_name") or item.get("name")
        if not name:
            continue
        metric_by_name[_admin_key(name)] = item

    # Géométries officielles (même source que Cartographie nationale)
    geom_features = []
    for feature in (_map_layer_fc("territoires").get("features") or []):
        props = feature.get("properties") or {}
        type_val = str(props.get("type") or props.get("TYPE") or "").lower()
        # Couche map déjà filtrée TYPE=territoire ; tolérer absence de type
        if type_val and type_val not in {"territoire", "territory"}:
            continue
        if not _admin_eq(props.get("province"), province_name):
            continue
        if not feature.get("geometry"):
            continue
        geom_features.append(feature)

    # Union des noms : référentiel + géométries (pas de territoire inventé)
    names: dict[str, str] = {}
    ids: dict[str, Any] = {}
    provinces: dict[str, str] = {}
    for key, item in metric_by_name.items():
        names[key] = item.get("territory_name") or item.get("name")
        ids[key] = item.get("territory_id") or names[key]
        provinces[key] = item.get("province") or province_name
    for feature in geom_features:
        props = feature.get("properties") or {}
        name = props.get("nom") or props.get("name")
        key = _admin_key(name)
        names.setdefault(key, name)
        ids.setdefault(key, props.get("id") or name)
        provinces.setdefault(key, props.get("province") or province_name)

    geom_by_name = {
        _admin_key((f.get("properties") or {}).get("nom") or (f.get("properties") or {}).get("name")): f
        for f in geom_features
    }

    features = []
    for key, name in sorted(names.items(), key=lambda x: str(x[1] or "")):
        crow = cov_by_name.get(key)
        measured = _territory_metric(metric_id, crow, metric)
        geom_feat = geom_by_name.get(key)
        features.append(
            {
                "type": "Feature",
                "id": ids.get(key) or name,
                "properties": {
                    "id": ids.get(key) or name,
                    "name": name,
                    "level": "territoire",
                    "administrative_level": "Territoire",
                    "parent_id": province_name,
                    "province": provinces.get(key) or province_name,
                    "metric_id": metric["id"],
                    "metric_label": metric["label"],
                    **{
                        k: measured[k]
                        for k in ("value", "display", "class_id", "class_label", "objects_count", "status", "source")
                    },
                    "updated_at": _now(),
                    "has_geometry": bool(geom_feat and geom_feat.get("geometry")),
                    "hint": "Cliquer pour explorer",
                },
                "geometry": (geom_feat or {}).get("geometry"),
            }
        )

    expected = len(features)
    geometry_count = sum(1 for f in features if f.get("geometry"))
    status = _geometry_status(expected, geometry_count)
    parent = _find_parent_feature(
        "provinces",
        province_name,
        level="province",
        administrative_level="Province",
    )

    return {
        "_meta": {
            "version": ENGINE_VERSION,
            "level": "territoire",
            "parent_id": province_name,
            "metric": metric,
            "count": expected,
            "updated_at": _now(),
            "geometry_source": "/map/layers/territoires (PostGIS territoires.geom ou territoires_hierarchie_kmz)",
            "parent_geometry_source": "/map/layers/provinces",
        },
        "level": "territoire",
        "parent": parent,
        "legend": _legend_for(metric["id"]),
        "features": {"type": "FeatureCollection", "features": features},
        "type": "FeatureCollection",  # compat frontend v1
        "expected_count": expected,
        "geometry_count": geometry_count,
        "geometry_status": status,
        "message": None
        if status != "unavailable"
        else "Les limites détaillées de ce niveau ne sont pas encore disponibles.",
    }


def build_subdivision_layer(
    territory_name: str,
    metric_id: str = "priority",
    province_name: str | None = None,
) -> dict[str, Any]:
    """Territoire → secteurs/chefferies/collectivités/cités (couche collectivites)."""
    metric = next((m for m in METRICS if m["id"] == metric_id), METRICS[0])
    parent = _find_parent_feature(
        "territoires",
        territory_name,
        province=province_name,
        level="territoire",
        administrative_level="Territoire",
    )

    features = []
    for feature in (_map_layer_fc("collectivites").get("features") or []):
        props = feature.get("properties") or {}
        if not _admin_eq(props.get("territoire"), territory_name):
            continue
        if province_name and props.get("province") and not _admin_eq(props.get("province"), province_name):
            continue
        name = props.get("nom") or props.get("name")
        admin_type = (
            props.get("type_collectivite")
            or props.get("type")
            or props.get("administrative_type")
            or "Collectivité"
        )
        measured = _insufficient_metric(metric)
        # Pas d’agrégat métrique officiel au niveau collectivité → Données insuffisantes (honnête)
        features.append(
            {
                "type": "Feature",
                "id": props.get("id") or name,
                "properties": {
                    "id": props.get("id") or name,
                    "name": name,
                    "level": "collectivite",
                    "administrative_level": str(admin_type),
                    "administrative_type": str(admin_type),
                    "parent_id": territory_name,
                    "territoire": territory_name,
                    "province": props.get("province") or province_name,
                    "metric_id": metric["id"],
                    "metric_label": metric["label"],
                    **{
                        k: measured[k]
                        for k in ("value", "display", "class_id", "class_label", "objects_count", "status", "source")
                    },
                    "updated_at": _now(),
                    "has_geometry": bool(feature.get("geometry")),
                    "hint": "Cliquer pour explorer",
                },
                "geometry": feature.get("geometry"),
            }
        )

    expected = len(features)
    geometry_count = sum(1 for f in features if f.get("geometry"))
    status = _geometry_status(expected, geometry_count)
    return {
        "_meta": {
            "version": ENGINE_VERSION,
            "level": "collectivite",
            "parent_id": territory_name,
            "metric": metric,
            "count": expected,
            "updated_at": _now(),
            "geometry_source": "/map/layers/collectivites",
            "note": "Métriques chiffrées non agrégées à ce niveau — classes « Données insuffisantes » si absentes",
        },
        "level": "collectivite",
        "parent": parent,
        "legend": _legend_for(metric["id"]),
        "features": {"type": "FeatureCollection", "features": features},
        "type": "FeatureCollection",
        "expected_count": expected,
        "geometry_count": geometry_count,
        "geometry_status": status,
        "message": None
        if status != "unavailable"
        else "Les limites détaillées de ce niveau ne sont pas encore disponibles.",
    }


def build_points_layer(
    level: str,
    parent_name: str,
    metric_id: str = "priority",
    province_name: str | None = None,
    territory_name: str | None = None,
) -> dict[str, Any]:
    """Groupements / localités : points réels si présents — jamais de géométrie fictive."""
    metric = next((m for m in METRICS if m["id"] == metric_id), METRICS[0])
    layer_name = "groupements" if level == "groupement" else "localites"
    parent_layer = "collectivites" if level == "groupement" else "groupements"
    parent_level = "collectivite" if level == "groupement" else "groupement"
    parent_admin = "Collectivité" if level == "groupement" else "Groupement"
    filter_key = "collectivite" if level == "groupement" else "groupement"

    parent = _find_parent_feature(
        parent_layer,
        parent_name,
        province=province_name,
        level=parent_level,
        administrative_level=parent_admin,
    )
    # Si parent collectivité sans polygone, tenter contour territoire
    if not parent and territory_name:
        parent = _find_parent_feature(
            "territoires",
            territory_name,
            province=province_name,
            level="territoire",
            administrative_level="Territoire",
        )

    features = []
    for feature in (_map_layer_fc(layer_name).get("features") or []):
        props = feature.get("properties") or {}
        if not _admin_eq(props.get(filter_key), parent_name):
            continue
        geom = feature.get("geometry")
        # Points uniquement — ignorer absences
        name = props.get("nom") or props.get("name")
        measured = _insufficient_metric(metric)
        features.append(
            {
                "type": "Feature",
                "id": props.get("id") or name,
                "properties": {
                    "id": props.get("id") or name,
                    "name": name,
                    "level": level,
                    "administrative_level": "Groupement" if level == "groupement" else "Localité",
                    "parent_id": parent_name,
                    "province": props.get("province") or province_name,
                    "territoire": props.get("territoire") or territory_name,
                    "metric_id": metric["id"],
                    "metric_label": metric["label"],
                    **{
                        k: measured[k]
                        for k in ("value", "display", "class_id", "class_label", "objects_count", "status", "source")
                    },
                    "updated_at": _now(),
                    "has_geometry": bool(geom),
                    "geometry_kind": (geom or {}).get("type") if isinstance(geom, dict) else None,
                    "hint": "Cliquer pour explorer",
                },
                "geometry": geom,
            }
        )

    expected = len(features)
    geometry_count = sum(1 for f in features if f.get("geometry"))
    status = _geometry_status(expected, geometry_count)
    return {
        "_meta": {
            "version": ENGINE_VERSION,
            "level": level,
            "parent_id": parent_name,
            "metric": metric,
            "count": expected,
            "updated_at": _now(),
            "geometry_source": f"/map/layers/{layer_name}",
        },
        "level": level,
        "parent": parent,
        "legend": _legend_for(metric["id"]),
        "features": {"type": "FeatureCollection", "features": features},
        "type": "FeatureCollection",
        "expected_count": expected,
        "geometry_count": geometry_count,
        "geometry_status": status,
        "message": None
        if status != "unavailable"
        else "Les limites détaillées de ce niveau ne sont pas encore disponibles.",
    }


def build_entity_summary(level: str, entity_id: str, name: str | None = None) -> dict[str, Any]:
    """Panneau de synthèse pour une entité — champs absents → Données insuffisantes."""
    display_name = name or entity_id
    sites = _sites_by_province()
    coverage = _coverage_by_province()
    health = _health_by_province()
    ccn = _ccn_by_province()
    key = _norm(display_name)

    def field(label: str, value: Any, source: str) -> dict[str, Any]:
        if value is None or value == "":
            return {"label": label, "value": None, "display": "Données insuffisantes", "source": source}
        return {"label": label, "value": value, "display": str(value), "source": source}

    if level == "province":
        s = sites.get(key) or {}
        c = coverage.get(key) or {}
        fields = [
            field("Sites FDSU", s.get("sites_fdsu"), "programs.fdsu_sites"),
            field("Sites prioritaires", s.get("sites_priority"), "decision.fdsu_site_scores"),
            field("Sites scorés", s.get("sites_scored"), "decision.fdsu_site_scores"),
            field("Population non couverte", c.get("population_uncovered"), "coverage aggregates"),
            field("Population couverte", c.get("population_covered"), "coverage aggregates"),
            field("Localités non couvertes", c.get("localities_uncovered"), "coverage aggregates"),
            field("Établissements de santé", health.get(key), "health statistics"),
            field("CCN", ccn.get(key) if ccn else None, "ccn statistics"),
            field("Qualité des données", "Agrégats NCI" if c else None, "coverage aggregates"),
        ]
        return {
            "_meta": {"version": ENGINE_VERSION, "updated_at": _now()},
            "entity": {
                "id": entity_id,
                "name": display_name,
                "level": "province",
                "administrative_level": "Province",
            },
            "fields": fields,
            "actions": [
                {"id": "open_ti", "label": "Ouvrir l’analyse territoriale", "hash": "territorial-intelligence"},
                {"id": "open_decision", "label": "Ouvrir le Centre de Décision", "hash": "decision-view"},
                {"id": "open_sites", "label": "Voir les sites", "hash": "decision-detail/sites-prioritaires"},
            ],
            "source": "PostgreSQL/PostGIS + NCI + Health + CCN",
            "updated_at": _now(),
        }

    # Territoire
    profile = _safe(lambda: territorial_intelligence_service.build_territorial_profile(entity_id), {}) or {}
    p = profile.get("profile") or profile
    fields = [
        field("Nom", p.get("territory_name") or display_name, "Master Registry / TI"),
        field("Province", p.get("province"), "Master Registry"),
        field("Qualité des données", p.get("data_quality"), "TI profile"),
        field("Confiance", p.get("confidence_level"), "TI profile"),
        field("Population", (p.get("population") or {}).get("value") if isinstance(p.get("population"), dict) else p.get("population"), "TI profile"),
    ]
    return {
        "_meta": {"version": ENGINE_VERSION, "updated_at": _now()},
        "entity": {
            "id": entity_id,
            "name": p.get("territory_name") or display_name,
            "level": "territoire",
            "administrative_level": "Territoire",
            "province": p.get("province"),
        },
        "fields": fields,
        "actions": [
            {"id": "open_ti", "label": "Ouvrir l’analyse territoriale", "hash": f"territorial-intelligence/{entity_id}"},
            {"id": "open_decision", "label": "Ouvrir le Centre de Décision", "hash": "decision-view"},
            {"id": "open_sites", "label": "Voir les sites", "hash": "decision-detail/sites-prioritaires"},
        ],
        "source": "Territorial Intelligence / Master Registry",
        "updated_at": _now(),
    }
