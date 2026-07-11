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

ENGINE_VERSION = "tst-1.0.0"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _norm(value: Any) -> str:
    return " ".join(str(value or "").strip().lower().split())


def _safe(fn, default=None):
    try:
        return fn()
    except Exception:
        return default


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


def _metric_value(metric_id: str, site_row: dict | None, cov_row: dict | None, health: int | None, ccn: int | None) -> dict[str, Any]:
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

        measured = _metric_value(metric["id"], site_row, cov_row, h, c)
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
            "rule": "Joindre properties.id / name aux features GeoJSON provinces",
        },
        "legend": _legend_for(metric["id"]),
        "features": features,
        "type": "FeatureCollection",
    }


def build_territory_layer(province_name: str, metric_id: str = "priority") -> dict[str, Any]:
    metric = next((m for m in METRICS if m["id"] == metric_id), METRICS[0])
    ti = _safe(
        lambda: territorial_intelligence_service.list_territories(province=province_name, limit=500),
        {},
    ) or {}
    cov = _safe(
        lambda: coverage_intelligence_service.list_territories(province=province_name, limit=500),
        {},
    ) or {}
    cov_by_name = {_norm(t.get("territoire") or t.get("territory_name") or t.get("name")): t for t in (cov.get("territories") or [])}

    features = []
    items = ti.get("items") or ti.get("territories") or []
    for item in items:
        name = item.get("territory_name") or item.get("name")
        tid = item.get("territory_id") or name
        crow = cov_by_name.get(_norm(name))
        # Territoire : métriques limitées aux sources TI/NCI — pas de score inventé
        if metric_id in ("needs", "coverage") and crow:
            measured = _metric_value(metric_id, None, {
                **crow,
                "coverage_ratio": (
                    int(crow.get("localities_covered") or 0)
                    / max(1, int(crow.get("localities_covered") or 0) + int(crow.get("localities_uncovered") or 0))
                ) if (crow.get("localities_covered") is not None or crow.get("localities_uncovered") is not None) else None,
            }, None, None)
        else:
            # Sites / priorité / santé / CCN non agrégés au territoire ici → insuffisant sauf NDCI
            ndci = (crow or {}).get("ndci") or {}
            if metric_id == "priority" and ndci.get("index") is not None:
                score = float(ndci["index"])
                measured = {
                    "value": score,
                    "display": str(score),
                    "class_id": _priority_class(score),
                    "class_label": f"NDCI {ndci.get('label') or score}",
                    "objects_count": 1,
                    "status": "ok",
                }
            else:
                measured = {
                    "value": None,
                    "display": "Données insuffisantes",
                    "class_id": "insufficient",
                    "class_label": "Données insuffisantes",
                    "objects_count": 0,
                    "status": "insufficient",
                }
        features.append(
            {
                "type": "Feature",
                "id": tid,
                "properties": {
                    "id": tid,
                    "name": name,
                    "level": "territoire",
                    "administrative_level": "Territoire",
                    "parent_id": province_name,
                    "province": item.get("province") or province_name,
                    "metric_id": metric["id"],
                    "metric_label": metric["label"],
                    **{k: measured[k] for k in ("value", "display", "class_id", "class_label", "objects_count", "status")},
                    "source": metric["source"],
                    "updated_at": _now(),
                    "hint": "Cliquer pour explorer",
                },
                "geometry": None,
            }
        )

    return {
        "_meta": {
            "version": ENGINE_VERSION,
            "level": "territoire",
            "parent_id": province_name,
            "metric": metric,
            "count": len(features),
            "updated_at": _now(),
            "geometry_note": "Limites territoire via /api/territorial-intelligence/territories/{id}/map si disponible",
        },
        "legend": _legend_for(metric["id"]),
        "features": features,
        "type": "FeatureCollection",
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
