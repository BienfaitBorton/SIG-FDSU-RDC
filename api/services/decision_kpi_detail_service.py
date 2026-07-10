"""Decision Detail Workspace — vues détaillées KPI du Centre de Décision.

Piloté par data/business/decision_kpi_details.json.
"""

from __future__ import annotations

import csv
import io
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CATALOG_PATH = PROJECT_ROOT / "data" / "business" / "decision_kpi_details.json"
ENGINE_VERSION = "decision-detail-1.0.0"

_CACHE: dict[str, Any] = {"mtime": None, "catalog": None}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _norm(text: str | None) -> str:
    return (text or "").strip().lower()


def load_catalog() -> dict[str, Any]:
    mtime = CATALOG_PATH.stat().st_mtime if CATALOG_PATH.exists() else None
    if _CACHE["catalog"] is None or _CACHE["mtime"] != mtime:
        _CACHE["catalog"] = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
        _CACHE["mtime"] = mtime
    return _CACHE["catalog"]


def resolve_kpi_code(raw: str) -> str | None:
    catalog = load_catalog()
    key = (raw or "").strip()
    if not key:
        return None
    kpis = catalog.get("kpis") or {}
    if key in kpis:
        return key
    aliases = catalog.get("aliases") or {}
    if key in aliases:
        return aliases[key]
    # kebab / snake normalize
    snake = key.replace("-", "_")
    if snake in kpis:
        return snake
    if snake in aliases:
        return aliases[snake]
    kebab = key.replace("_", "-")
    if kebab in aliases:
        return aliases[kebab]
    return None


def get_kpi_config(kpi_code: str) -> dict[str, Any] | None:
    code = resolve_kpi_code(kpi_code)
    if not code:
        return None
    cfg = (load_catalog().get("kpis") or {}).get(code)
    if not cfg:
        return None
    return {**cfg, "kpi_code": code}


def list_kpi_catalog() -> dict[str, Any]:
    catalog = load_catalog()
    items = []
    for code, cfg in (catalog.get("kpis") or {}).items():
        items.append(
            {
                "kpi_code": code,
                "route_slug": cfg.get("route_slug"),
                "title": cfg.get("title"),
                "item_kind": cfg.get("item_kind"),
                "route": f"#decision-detail/{cfg.get('route_slug') or code.replace('_', '-')}",
            }
        )
    return {
        "_meta": {"engine": ENGINE_VERSION, "count": len(items)},
        "kpis": items,
        "aliases": catalog.get("aliases") or {},
    }


def _site_matches(
    site: dict[str, Any],
    *,
    province: str | None,
    territoire: str | None,
    priority_level: str | None,
    q: str | None,
) -> bool:
    if province and _norm(site.get("province")) != _norm(province):
        return False
    if territoire and _norm(site.get("territoire")) != _norm(territoire):
        return False
    if priority_level:
        levels = {p.strip().lower() for p in priority_level.split(",") if p.strip()}
        if _norm(site.get("priority_level")) not in levels:
            return False
    if q:
        blob = " ".join(
            str(site.get(k) or "")
            for k in ("site_name", "site_code", "province", "territoire", "program_code")
        ).lower()
        if q.lower() not in blob:
            return False
    return True


def _collect_sites(
    cfg: dict[str, Any],
    *,
    program: str | None = None,
    province: str | None = None,
    territoire: str | None = None,
    priority_level: str | None = None,
    q: str | None = None,
) -> list[dict[str, Any]]:
    from api.services import fdsu_site_priority_service, fdsu_sites_import_service

    programs = []
    if program:
        programs = [fdsu_sites_import_service.normalize_program_code(program)]
    else:
        programs = list(cfg.get("default_programs") or [])

    allowed_levels = cfg.get("priority_levels")
    effective_level = priority_level
    if allowed_levels and not priority_level:
        effective_level = ",".join(allowed_levels)

    collected: list[dict[str, Any]] = []
    seen: set[str] = set()
    for code in programs:
        try:
            payload = fdsu_site_priority_service.list_priorities(code, limit=50000, offset=0)
        except Exception:  # noqa: BLE001
            continue
        for site in payload.get("sites") or []:
            sid = f"{site.get('program_code')}:{site.get('site_id') or site.get('site_code')}"
            if sid in seen:
                continue
            if not _site_matches(
                site,
                province=province,
                territoire=territoire,
                priority_level=effective_level,
                q=q,
            ):
                continue
            seen.add(sid)
            collected.append(site)
    collected.sort(
        key=lambda s: (-float(s.get("priority_score") or 0), str(s.get("site_name") or ""))
    )
    return collected


def _collect_referentials(
    cfg: dict[str, Any],
    *,
    status: str | None = None,
    category: str | None = None,
    q: str | None = None,
) -> list[dict[str, Any]]:
    wanted = set(cfg.get("referential_status") or [])
    if status:
        wanted = {s.strip() for s in status.split(",") if s.strip()} or wanted

    items: list[dict[str, Any]] = []
    try:
        from api.services import reference_service

        for st in wanted or [None]:
            rows = reference_service.list_catalog(status=st) if st else reference_service.list_catalog()
            items.extend(rows)
    except Exception:  # noqa: BLE001
        fallback = load_catalog().get("fallback_referentials") or []
        items = [dict(r) for r in fallback if not wanted or r.get("status") in wanted]

    # Deduplicate by code
    by_code: dict[str, dict[str, Any]] = {}
    for row in items:
        code = str(row.get("code") or row.get("name") or id(row))
        by_code[code] = row
    out = list(by_code.values())

    filtered = []
    for row in out:
        if wanted and row.get("status") not in wanted:
            continue
        if category and _norm(row.get("category")) != _norm(category):
            continue
        if q:
            blob = " ".join(str(row.get(k) or "") for k in ("name", "code", "category", "source_name")).lower()
            if q.lower() not in blob:
                continue
        if not row.get("recommended_action") and row.get("status") == "planned":
            row = {**row, "recommended_action": "Planifier l’intégration opérationnelle du référentiel"}
        filtered.append(row)
    return filtered


def _collect_coverage(
    cfg: dict[str, Any],
    *,
    province: str | None = None,
    territoire: str | None = None,
    priority: str | None = None,
    q: str | None = None,
    limit: int = 500,
) -> list[dict[str, Any]]:
    from api.services import coverage_intelligence_service as nci

    metric = cfg.get("coverage_metric") or "population_uncovered"
    status = "covered" if "covered" in metric and "uncovered" not in metric else "uncovered"
    payload = nci.list_localities(
        status=status,
        province=province,
        territoire=territoire,
        priority=priority,
        q=q,
        limit=limit,
        offset=0,
    )
    return payload.get("localities") or []


def _collect_ccn(
    *,
    province: str | None = None,
    territoire: str | None = None,
    status: str | None = None,
    q: str | None = None,
) -> list[dict[str, Any]]:
    try:
        from api.services import ccn_operational_service

        payload = ccn_operational_service.list_ccn(
            province=province,
            territoire=territoire,
            status=status,
            limit=500,
        )
        items = payload.get("ccn") or payload.get("items") or []
        if q:
            items = [
                i
                for i in items
                if q.lower()
                in " ".join(str(i.get(k) or "") for k in ("name", "ccn_code", "province", "territoire")).lower()
            ]
        return items
    except Exception:  # noqa: BLE001
        return []


def _collect_health(
    *,
    province: str | None = None,
    territoire: str | None = None,
    q: str | None = None,
    limit: int = 200,
) -> list[dict[str, Any]]:
    try:
        from api.services import health_service

        # Prefer lightweight list if available
        if hasattr(health_service, "list_facilities"):
            payload = health_service.list_facilities(province=province, limit=limit)
            items = payload.get("facilities") or payload.get("items") or []
        else:
            stats = health_service.get_statistics()
            items = []
            # sample from stats if present
            for sample in stats.get("sample") or stats.get("by_province") or []:
                if isinstance(sample, dict):
                    items.append(sample)
        if territoire:
            items = [i for i in items if _norm(i.get("territoire") or i.get("territory")) == _norm(territoire)]
        if q:
            items = [
                i
                for i in items
                if q.lower() in " ".join(str(i.get(k) or "") for k in ("name", "facility_name", "province")).lower()
            ]
        return items[:limit]
    except Exception:  # noqa: BLE001
        return []


def _collect_items(
    cfg: dict[str, Any],
    filters: dict[str, Any],
) -> list[dict[str, Any]]:
    kind = cfg.get("item_kind")
    if kind == "site":
        return _collect_sites(
            cfg,
            program=filters.get("programme") or filters.get("program"),
            province=filters.get("province"),
            territoire=filters.get("territoire"),
            priority_level=filters.get("priority_level") or filters.get("niveau"),
            q=filters.get("q"),
        )
    if kind == "referential":
        return _collect_referentials(
            cfg,
            status=filters.get("status"),
            category=filters.get("category"),
            q=filters.get("q"),
        )
    if kind == "coverage":
        return _collect_coverage(
            cfg,
            province=filters.get("province"),
            territoire=filters.get("territoire"),
            priority=filters.get("priority") or filters.get("priority_level"),
            q=filters.get("q"),
            limit=int(filters.get("limit") or 500),
        )
    if kind == "ccn":
        return _collect_ccn(
            province=filters.get("province"),
            territoire=filters.get("territoire"),
            status=filters.get("status"),
            q=filters.get("q"),
        )
    if kind == "health":
        return _collect_health(
            province=filters.get("province"),
            territoire=filters.get("territoire"),
            q=filters.get("q"),
        )
    if kind == "telecom":
        try:
            from api.services import telecom_service

            if hasattr(telecom_service, "list_infrastructure"):
                payload = telecom_service.list_infrastructure(limit=200)
                return payload.get("items") or payload.get("infrastructure") or []
        except Exception:  # noqa: BLE001
            return []
        return []
    if kind == "admin":
        try:
            from api.services import master_registry_service

            entity = "PROVINCE" if cfg.get("admin_level") == "province" else "TERRITOIRE"
            payload = master_registry_service.list_entities(entity_type=entity, limit=500)
            items = payload.get("entities") or []
            q = filters.get("q")
            province = filters.get("province")
            if province:
                items = [i for i in items if _norm(i.get("province") or i.get("parent_name")) == _norm(province)]
            if q:
                items = [i for i in items if q.lower() in str(i.get("name") or i.get("label") or "").lower()]
            return items
        except Exception:  # noqa: BLE001
            return []
    if kind == "pending":
        return []
    return []


def _secondary_kpis(cfg: dict[str, Any], items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    kind = cfg.get("item_kind")
    if kind == "site":
        by_level = Counter(str(i.get("priority_level") or "unknown") for i in items)
        by_program = Counter(str(i.get("program_code") or "unknown") for i in items)
        return [
            {"id": "total", "label": "Total filtré", "value": len(items)},
            {"id": "critical", "label": "Critiques", "value": by_level.get("critical", 0)},
            {"id": "high", "label": "Priorité élevée", "value": by_level.get("high", 0)},
            {"id": "medium", "label": "Moyenne", "value": by_level.get("medium", 0)},
            {"id": "programs", "label": "Programmes", "value": len(by_program)},
        ]
    if kind == "referential":
        by_status = Counter(str(i.get("status") or "unknown") for i in items)
        return [
            {"id": "total", "label": "Total", "value": len(items)},
            *[{"id": k, "label": k, "value": v} for k, v in by_status.items()],
        ]
    if kind == "coverage":
        pop = sum(int(i.get("population") or 0) for i in items)
        return [
            {"id": "localities", "label": "Localités", "value": len(items)},
            {"id": "population", "label": "Population", "value": pop},
        ]
    return [{"id": "total", "label": "Total", "value": len(items)}]


def _charts(cfg: dict[str, Any], items: list[dict[str, Any]]) -> dict[str, Any]:
    charts: dict[str, Any] = {}
    kind = cfg.get("item_kind")
    types = set(cfg.get("chart_types") or [])

    if kind == "site" or (kind == "coverage" and "bars_province" in types):
        key_prov = "province"
        by_prov = Counter(str(i.get(key_prov) or "INCONNU") for i in items)
        top = by_prov.most_common(10)
        charts["bars_province"] = {
            "title": "Classement provinces",
            "items": [{"label": k, "value": v, "color": "orange"} for k, v in top],
        }
    if kind == "site" and "bars_territory" in types:
        by_t = Counter(str(i.get("territoire") or "INCONNU") for i in items)
        charts["bars_territory"] = {
            "title": "Classement territoires",
            "items": [{"label": k, "value": v, "color": "blue"} for k, v in by_t.most_common(10)],
        }
    if kind == "site" and "priority_split" in types:
        by_level = Counter(str(i.get("priority_level") or "unknown") for i in items)
        color = {"critical": "red", "high": "orange", "medium": "yellow", "low": "green"}
        charts["priority_split"] = {
            "title": "Répartition par priorité",
            "items": [
                {"label": k, "value": v, "color": color.get(k, "blue")}
                for k, v in by_level.most_common()
            ],
        }
    if kind == "site" and "bars_program" in types:
        by_p = Counter(str(i.get("program_code") or "unknown") for i in items)
        charts["bars_program"] = {
            "title": "Répartition par programme",
            "items": [{"label": k, "value": v, "color": "blue"} for k, v in by_p.most_common()],
        }
    if kind == "referential":
        by_status = Counter(str(i.get("status") or "unknown") for i in items)
        charts["bars_status"] = {
            "title": "Répartition par statut",
            "items": [{"label": k, "value": v, "color": "green"} for k, v in by_status.most_common()],
        }
        by_cat = Counter(str(i.get("category") or "unknown") for i in items)
        charts["bars_category"] = {
            "title": "Répartition par catégorie",
            "items": [{"label": k, "value": v, "color": "blue"} for k, v in by_cat.most_common()],
        }
    if kind == "coverage" and "priority_split" in types:
        by_pri = Counter(str(i.get("priority") or "unknown") for i in items)
        charts["priority_split"] = {
            "title": "Répartition priorités besoins",
            "items": [{"label": k, "value": v, "color": "orange"} for k, v in by_pri.most_common()],
        }
    return charts


def _map_geojson(cfg: dict[str, Any], items: list[dict[str, Any]], *, limit: int = 3000) -> dict[str, Any]:
    features = []
    kind = cfg.get("item_kind")
    for item in items[:limit]:
        lat = item.get("latitude") or item.get("lat")
        lon = item.get("longitude") or item.get("lon") or item.get("lng")
        if lat is None or lon is None:
            continue
        try:
            lat_f, lon_f = float(lat), float(lon)
        except (TypeError, ValueError):
            continue
        props = {
            "id": item.get("site_id") or item.get("id") or item.get("code"),
            "name": item.get("site_name") or item.get("name"),
            "province": item.get("province"),
            "territoire": item.get("territoire"),
            "priority_level": item.get("priority_level") or item.get("priority"),
            "program_code": item.get("program_code"),
            "kind": kind,
        }
        features.append(
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [lon_f, lat_f]},
                "properties": props,
            }
        )
    return {
        "type": "FeatureCollection",
        "features": features,
        "_meta": {
            "engine": ENGINE_VERSION,
            "count": len(features),
            "kpi_code": cfg.get("kpi_code"),
            "map_layer": cfg.get("map_layer"),
            "legend": {
                "critical": "Critique",
                "high": "Priorité élevée",
                "medium": "Moyenne",
                "low": "Faible",
            },
            "center": [-2.8, 23.5],
            "zoom": 5,
        },
    }


def _explain(cfg: dict[str, Any], items: list[dict[str, Any]], value: Any) -> dict[str, Any]:
    mode = cfg.get("explain_mode")
    missing = []
    doctrine = None
    matrix = None
    try:
        from api.services import explainable_decision_service

        if mode in {"sites_doctrine", "ccn_doctrine"}:
            doctrine_id = "DOCTRINE_CCN_FDSU" if mode == "ccn_doctrine" else "DOCTRINE_SITES_FDSU"
            doctrine = explainable_decision_service.get_doctrine_payload(doctrine_id)
            matrix = {
                "ref": "data/business/priority_matrix.json",
                "note": "Seuils critical / high / medium / low",
            }
    except Exception:  # noqa: BLE001
        pass

    why = (
        f"Les {len(items)} éléments affichés correspondent au KPI « {cfg.get('title')} » "
        f"({cfg.get('definition')}). Valeur consolidée : {value}."
    )
    if cfg.get("priority_levels"):
        why += f" Filtre de niveau : {', '.join(cfg['priority_levels'])}."
    if cfg.get("default_programs"):
        why += f" Programmes sources : {', '.join(cfg['default_programs'])}."
    if cfg.get("pending"):
        why = (
            "Cet indicateur est en attente d’un référentiel Budget officiel. "
            "Aucune valeur n’est inventée."
        )
        missing.append("referentiel_budget")

    criteria = []
    if doctrine:
        for c in ((doctrine.get("doctrine") or {}).get("selection_criteria") or [])[:6]:
            criteria.append({"id": c.get("id"), "label": c.get("label"), "weight_percent": c.get("weight_percent")})

    return {
        "why": why,
        "definition": cfg.get("definition"),
        "doctrine": {
            "id": ((doctrine or {}).get("doctrine") or {}).get("_meta", {}).get("doctrine_id") if doctrine else None,
            "version": ((doctrine or {}).get("doctrine") or {}).get("_meta", {}).get("version") if doctrine else None,
        },
        "matrix": matrix,
        "criteria": criteria,
        "missing_data": missing,
        "confidence": cfg.get("confidence"),
        "source_label": cfg.get("source_label"),
        "recommended_action": (
            "Analyser les sites critiques et préparer une mission terrain"
            if cfg.get("kpi_code") == "sites_critical"
            else cfg.get("executive_objective")
        ),
    }


def _header(cfg: dict[str, Any], value: Any) -> dict[str, Any]:
    return {
        "kpi_code": cfg.get("kpi_code"),
        "route_slug": cfg.get("route_slug"),
        "title": cfg.get("title"),
        "value": value,
        "definition": cfg.get("definition"),
        "description": cfg.get("description"),
        "source": cfg.get("source_label"),
        "source_technical": cfg.get("source_technical"),
        "confidence": cfg.get("confidence"),
        "trend": "flat",
        "objective": cfg.get("executive_objective"),
        "last_updated": _now(),
        "pending": bool(cfg.get("pending")),
    }


def build_detail(
    kpi_code: str,
    *,
    province: str | None = None,
    territoire: str | None = None,
    programme: str | None = None,
    priority_level: str | None = None,
    status: str | None = None,
    category: str | None = None,
    q: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> dict[str, Any] | None:
    cfg = get_kpi_config(kpi_code)
    if not cfg:
        return None

    filters = {
        "province": province,
        "territoire": territoire,
        "programme": programme,
        "priority_level": priority_level,
        "status": status,
        "category": category,
        "q": q,
        "limit": max(limit, 500),
    }
    items = _collect_items(cfg, filters)

    # Primary value: for sites_fdsu without extra filters use full count; else filtered
    if cfg.get("item_kind") == "coverage":
        try:
            from api.services import coverage_intelligence_service as nci

            national = (nci.get_aggregates().get("national") or {})
            metric = cfg.get("coverage_metric") or "population_uncovered"
            value = national.get(metric)
        except Exception:  # noqa: BLE001
            value = len(items)
    elif cfg.get("pending"):
        value = None
    else:
        value = len(items)

    page = items[offset : offset + limit]
    return {
        "_meta": {
            "engine": ENGINE_VERSION,
            "kpi_code": cfg["kpi_code"],
            "generated_at": _now(),
            "back_route": "#decision-view",
        },
        "config": {
            "filters": cfg.get("filters"),
            "actions": cfg.get("actions"),
            "list_columns": cfg.get("list_columns"),
            "chart_types": cfg.get("chart_types"),
            "map_layer": cfg.get("map_layer"),
            "item_kind": cfg.get("item_kind"),
            "optional_programs": cfg.get("optional_programs"),
            "default_programs": cfg.get("default_programs"),
        },
        "header": _header(cfg, value),
        "secondary_kpis": _secondary_kpis(cfg, items),
        "charts": _charts(cfg, items),
        "items": {
            "total": len(items),
            "offset": offset,
            "limit": limit,
            "rows": page,
        },
        "explain": _explain(cfg, items, value),
        "actions": [
            {"id": a, "label": _action_label(a)} for a in (cfg.get("actions") or [])
        ],
    }


def _action_label(action_id: str) -> str:
    labels = {
        "export_excel": "Exporter Excel",
        "export_geojson": "Exporter GeoJSON",
        "open_cartography": "Ouvrir dans Cartographie",
        "open_ti": "Ouvrir Territorial Intelligence",
        "explain": "Expliquer",
        "prepare_mission": "Préparer une mission",
        "simulate_investment": "Simuler un investissement",
    }
    return labels.get(action_id, action_id)


def build_map(kpi_code: str, **filters: Any) -> dict[str, Any] | None:
    cfg = get_kpi_config(kpi_code)
    if not cfg:
        return None
    items = _collect_items(cfg, filters)
    return _map_geojson(cfg, items)


def build_charts(kpi_code: str, **filters: Any) -> dict[str, Any] | None:
    cfg = get_kpi_config(kpi_code)
    if not cfg:
        return None
    items = _collect_items(cfg, filters)
    return {
        "_meta": {"engine": ENGINE_VERSION, "kpi_code": cfg["kpi_code"]},
        "charts": _charts(cfg, items),
        "secondary_kpis": _secondary_kpis(cfg, items),
    }


def build_items(
    kpi_code: str,
    *,
    limit: int = 100,
    offset: int = 0,
    **filters: Any,
) -> dict[str, Any] | None:
    cfg = get_kpi_config(kpi_code)
    if not cfg:
        return None
    items = _collect_items(cfg, filters)
    return {
        "_meta": {"engine": ENGINE_VERSION, "kpi_code": cfg["kpi_code"]},
        "total": len(items),
        "offset": offset,
        "limit": limit,
        "columns": cfg.get("list_columns") or [],
        "rows": items[offset : offset + limit],
    }


def build_explain(kpi_code: str, **filters: Any) -> dict[str, Any] | None:
    cfg = get_kpi_config(kpi_code)
    if not cfg:
        return None
    items = _collect_items(cfg, filters)
    value = None if cfg.get("pending") else len(items)
    return {
        "_meta": {"engine": ENGINE_VERSION, "kpi_code": cfg["kpi_code"]},
        **_explain(cfg, items, value),
    }


def build_export(
    kpi_code: str,
    *,
    format: str = "json",
    **filters: Any,
) -> dict[str, Any] | None:
    cfg = get_kpi_config(kpi_code)
    if not cfg:
        return None
    items = _collect_items(cfg, filters)
    columns = cfg.get("list_columns") or []
    if format == "geojson":
        return {
            "format": "geojson",
            "filename": f"{cfg['kpi_code']}.geojson",
            "payload": _map_geojson(cfg, items),
        }
    if format == "csv" or format == "excel":
        buf = io.StringIO()
        cols = columns or (list(items[0].keys()) if items else ["id"])
        writer = csv.DictWriter(buf, fieldnames=cols, extrasaction="ignore")
        writer.writeheader()
        for row in items:
            writer.writerow({c: row.get(c) for c in cols})
        return {
            "format": "csv",
            "filename": f"{cfg['kpi_code']}.csv",
            "content": buf.getvalue(),
            "count": len(items),
        }
    return {
        "format": "json",
        "filename": f"{cfg['kpi_code']}.json",
        "payload": {"kpi_code": cfg["kpi_code"], "count": len(items), "rows": items},
    }
