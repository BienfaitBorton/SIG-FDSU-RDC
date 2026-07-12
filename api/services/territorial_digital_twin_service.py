"""Territorial Digital Twin Foundation — couche d'agrégation (pas de doublon métier).

Compose Master Registry, NDF, TI, NCI, NSME, Transport, Santé, CCN, Decision, Knowledge Hub.
Chaque section est isolée : échec → statut partial/unavailable, jamais de valeur inventée.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable

ENGINE_VERSION = "tdt-1.0.0"
STATUS_SUCCESS = "success"
STATUS_PARTIAL = "partial"
STATUS_UNAVAILABLE = "unavailable"
STATUS_ERROR = "error"

ENTITY_ALIASES = {
    "province": "province",
    "provinces": "province",
    "territoire": "territoire",
    "territory": "territoire",
    "territoires": "territoire",
    "collectivite": "collectivite",
    "collectivité": "collectivite",
    "secteur": "collectivite",
    "chefferie": "collectivite",
    "cite": "collectivite",
    "cité": "collectivite",
    "groupement": "groupement",
    "localite": "localite",
    "localité": "localite",
    "village": "localite",
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _safe(fn: Callable[[], Any], default: Any = None) -> Any:
    try:
        return fn()
    except Exception:
        return default


def _section(status: str, payload: dict[str, Any] | None = None, *, note: str | None = None, source: str | None = None) -> dict[str, Any]:
    body = dict(payload or {})
    body["_section"] = {
        "status": status,
        "note": note,
        "source": source,
        "updated_at": _now(),
    }
    return body


def _unavailable(note: str, source: str | None = None) -> dict[str, Any]:
    return _section(STATUS_UNAVAILABLE, {"display": "Données insuffisantes"}, note=note, source=source)


def _normalize_type(entity_type: str) -> str:
    key = str(entity_type or "").strip().lower()
    return ENTITY_ALIASES.get(key, key)


def resolve_entity(entity_type: str, entity_id: str) -> dict[str, Any] | None:
    """Identité administrative — Master Registry / TI / nom province."""
    etype = _normalize_type(entity_type)
    needle = str(entity_id or "").strip()
    if not needle:
        return None

    if etype == "territoire":
        from api.services import territorial_intelligence_service as ti

        ref = ti._resolve_territory_ref(needle)  # noqa: SLF001 — réutilisation volontaire
        if not ref:
            return None
        return {
            "entity_id": ref.get("territory_id") or needle,
            "entity_type": "territoire",
            "nom": ref.get("territory_name") or needle,
            "code_officiel": ref.get("administrative_code"),
            "niveau_administratif": "Territoire",
            "parent": {"entity_type": "province", "nom": ref.get("province"), "code": ref.get("province_code")},
            "province": ref.get("province"),
            "province_code": ref.get("province_code"),
            "fdsu_zone": ref.get("fdsu_zone"),
            "source_administrative": ref.get("source") or "master_registry",
            "geometry": None,
            "centroid": None,
        }

    if etype == "province":
        from api.services import master_registry_service as mr

        entities = (mr.list_entities(entity_type="PROVINCE", limit=200).get("entities") or [])
        needle_n = " ".join(needle.lower().replace("-", " ").split())
        for ent in entities:
            name = str(ent.get("name") or "")
            bid = str(ent.get("business_id") or "")
            attrs = ent.get("attributes") or {}
            candidates = {
                name.lower().replace("-", " "),
                bid.lower(),
                str(attrs.get("province_code") or "").lower(),
                str(attrs.get("code") or "").lower(),
            }
            if needle_n in candidates or any(needle_n == " ".join(c.split()) for c in candidates if c):
                return {
                    "entity_id": bid or needle,
                    "entity_type": "province",
                    "nom": name or needle,
                    "code_officiel": attrs.get("province_code") or attrs.get("code"),
                    "niveau_administratif": "Province",
                    "parent": {"entity_type": "rdc", "nom": "RDC"},
                    "province": name or needle,
                    "source_administrative": "master_registry",
                    "geometry": ent.get("geometry"),
                    "centroid": None,
                }
        # Fallback nom libre (TST utilise souvent le nom normalisé)
        return {
            "entity_id": needle,
            "entity_type": "province",
            "nom": needle,
            "code_officiel": None,
            "niveau_administratif": "Province",
            "parent": {"entity_type": "rdc", "nom": "RDC"},
            "province": needle,
            "source_administrative": "territorial_summary / name",
            "geometry": None,
            "centroid": None,
        }

    # Niveaux inférieurs : identité Master Registry si présente, sinon contrat préparé
    type_map = {
        "collectivite": "COLLECTIVITE",
        "groupement": "GROUPEMENT",
        "localite": "LOCALITE",
    }
    mr_type = type_map.get(etype)
    if mr_type:
        from api.services import master_registry_service as mr

        ent = _safe(lambda: mr.get_entity(needle), None)
        if ent and str(ent.get("entity_type") or "").upper() == mr_type:
            attrs = ent.get("attributes") or {}
            return {
                "entity_id": ent.get("business_id") or needle,
                "entity_type": etype,
                "nom": ent.get("name") or needle,
                "code_officiel": attrs.get("code"),
                "niveau_administratif": etype.capitalize(),
                "parent": {
                    "entity_type": "territoire" if etype == "collectivite" else ("collectivite" if etype == "groupement" else "groupement"),
                    "nom": attrs.get("territoire") or attrs.get("collectivite") or attrs.get("groupement"),
                },
                "province": attrs.get("province_name") or attrs.get("province"),
                "source_administrative": "master_registry",
                "geometry": ent.get("geometry"),
                "centroid": None,
            }
        return {
            "entity_id": needle,
            "entity_type": etype,
            "nom": needle,
            "code_officiel": None,
            "niveau_administratif": etype.capitalize(),
            "parent": None,
            "source_administrative": "declared",
            "geometry": None,
            "centroid": None,
            "note": "Identité partielle — enrichissement Master Registry prévu",
        }
    return None


def build_hierarchy(entity: dict[str, Any]) -> list[dict[str, Any]]:
    trail = [{"entity_type": "rdc", "entity_id": "rdc", "nom": "RDC", "niveau_administratif": "Pays"}]
    etype = entity.get("entity_type")
    if etype == "province":
        trail.append({"entity_type": "province", "entity_id": entity.get("entity_id"), "nom": entity.get("nom"), "niveau_administratif": "Province"})
    elif etype == "territoire":
        if entity.get("province"):
            trail.append({"entity_type": "province", "entity_id": entity.get("province"), "nom": entity.get("province"), "niveau_administratif": "Province"})
        trail.append({"entity_type": "territoire", "entity_id": entity.get("entity_id"), "nom": entity.get("nom"), "niveau_administratif": "Territoire"})
    else:
        if entity.get("province"):
            trail.append({"entity_type": "province", "entity_id": entity.get("province"), "nom": entity.get("province"), "niveau_administratif": "Province"})
        parent = entity.get("parent") or {}
        if parent.get("nom"):
            trail.append({
                "entity_type": parent.get("entity_type"),
                "entity_id": parent.get("nom"),
                "nom": parent.get("nom"),
                "niveau_administratif": str(parent.get("entity_type") or "").capitalize(),
            })
        trail.append({
            "entity_type": etype,
            "entity_id": entity.get("entity_id"),
            "nom": entity.get("nom"),
            "niveau_administratif": entity.get("niveau_administratif"),
        })
    return trail


def section_summary(entity: dict[str, Any]) -> dict[str, Any]:
    etype = entity.get("entity_type")
    if etype == "territoire":
        from api.services import territorial_intelligence_service as ti

        profile = _safe(lambda: ti.build_territorial_profile(str(entity["entity_id"]), light=True), {}) or {}
        p = profile.get("profile") or {}
        if not p:
            return _unavailable("Profil territorial indisponible", "territorial_intelligence")
        return _section(
            STATUS_SUCCESS if p else STATUS_PARTIAL,
            {
                "headline": f"{p.get('territory_name') or entity.get('nom')} — {p.get('province') or ''}".strip(" —"),
                "population": p.get("population"),
                "area_km2": p.get("area_km2"),
                "density": p.get("density"),
                "data_quality": p.get("data_quality"),
                "confidence_level": p.get("confidence_level"),
                "fdsu_zone": p.get("fdsu_zone"),
            },
            source="territorial_intelligence",
        )
    if etype == "province":
        from api.services import territorial_summary_service as tst

        summary = _safe(
            lambda: tst.build_entity_summary("province", str(entity.get("entity_id")), entity.get("nom")),
            {},
        ) or {}
        if not summary:
            return _unavailable("Synthèse provinciale indisponible", "territorial_summary")
        return _section(
            STATUS_SUCCESS,
            {
                "headline": f"Province {entity.get('nom')}",
                "fields": summary.get("fields") or [],
                "source_label": summary.get("source"),
            },
            source="territorial_summary",
        )
    return _section(
        STATUS_PARTIAL,
        {
            "headline": entity.get("nom"),
            "note": "Résumé détaillé disponible principalement pour province et territoire",
        },
        note="Niveaux inférieurs : socle prêt",
        source="tdt",
    )


def section_connectivity(entity: dict[str, Any]) -> dict[str, Any]:
    from api.services import coverage_intelligence_service as nci

    name = entity.get("nom")
    province = entity.get("province") or (name if entity.get("entity_type") == "province" else None)
    if entity.get("entity_type") == "territoire":
        payload = _safe(lambda: nci.get_territory_coverage(str(name)), None)
        match = (payload or {}).get("territory") if isinstance(payload, dict) else None
        if not match:
            return _unavailable("Pas d’agrégat NCI pour ce territoire", "coverage_intelligence")
        return _section(
            STATUS_SUCCESS,
            {
                "population_uncovered": match.get("population_uncovered"),
                "population_covered": match.get("population_covered"),
                "localities_uncovered": match.get("localities_uncovered"),
                "localities_covered": match.get("localities_covered"),
                "ndci": match.get("ndci"),
                "demo": bool(match.get("is_demo") or match.get("demo")),
                "explain": (payload or {}).get("explain"),
            },
            source="national_coverage_intelligence",
        )
    if entity.get("entity_type") == "province" and province:
        agg = _safe(lambda: nci.get_aggregates(), {}) or {}
        by_p = (agg.get("by_province") or {}) if isinstance(agg, dict) else {}
        # clés normalisées
        key = " ".join(str(province).lower().split())
        row = None
        for k, v in by_p.items():
            if " ".join(str(k).lower().split()) == key:
                row = v if isinstance(v, dict) else {"value": v}
                break
            if isinstance(v, dict) and " ".join(str(v.get("province") or "").lower().split()) == key:
                row = v
                break
        if not row:
            # Essayer list via coverage stats
            stats = _safe(lambda: nci.statistics(), {}) or {}
            return _section(
                STATUS_PARTIAL,
                {"national_stats": stats.get("counts") or stats, "province": province},
                note="Agrégat provincial NCI partiel",
                source="coverage_intelligence",
            )
        return _section(STATUS_SUCCESS, {"province": province, **row}, source="coverage_intelligence")
    return _unavailable("Connectivité non agrégée pour ce niveau", "coverage_intelligence")


def section_public_services(entity: dict[str, Any]) -> dict[str, Any]:
    from api.services import health_service

    province = entity.get("province") or (entity.get("nom") if entity.get("entity_type") == "province" else None)
    territory = entity.get("nom") if entity.get("entity_type") == "territoire" else None
    facilities = _safe(
        lambda: health_service.list_facilities(province_name=province, territory_name=territory, limit=50),
        None,
    )
    if facilities is None:
        return _unavailable("Référentiel santé indisponible", "health")
    rows = facilities if isinstance(facilities, list) else (facilities.get("facilities") or facilities.get("items") or [])
    education = _unavailable("Référentiel Éducation non encore intégré (NDF planned)", "ndf/education")
    return _section(
        STATUS_PARTIAL if rows else STATUS_PARTIAL,
        {
            "health": {
                "count": len(rows),
                "sample": rows[:10],
                "source": "/api/health",
            },
            "education": education,
            "administration": _unavailable("Services administratifs non sourcés", None),
            "markets": _unavailable("Marchés non encore intégrés", None),
        },
        note="Santé branchée ; éducation/marchés préparés",
        source="health + ndf",
    )


def section_accessibility(entity: dict[str, Any]) -> dict[str, Any]:
    from api.services import transport_service

    # Province : ne pas recalculer nearest_road pour tous les sites dans le jumeau
    # (perf) — exposer la disponibilité transport + formule ; score détaillé via /api/transport
    if entity.get("entity_type") == "province":
        quality = _safe(transport_service.get_quality_report, {}) or {}
        db_stats = quality.get("database_stats") or {}
        routes_total = db_stats.get("routes_total") or ((quality.get("pipeline_report") or {}).get("counts") or {}).get("accepted")
        if not routes_total:
            return _unavailable("Référentiel transport indisponible", "transport")
        return _section(
            STATUS_PARTIAL,
            {
                "routes_total": routes_total,
                "formula": transport_service.ACCESSIBILITY_FORMULA,
                "note": "Score provincial détaillé disponible via Transport Intelligence / sites géoréférencés",
                "endpoint_hint": "/api/transport/accessibility/by-province",
            },
            note="Agrégat provincial non recalculé dans le jumeau (échantillon sites via endpoint transport)",
            source="transport.routes",
        )
    if entity.get("entity_type") == "territoire":
        # Centroïde non toujours dispo — tenter sites du territoire via TI profile assets
        from api.services import territorial_intelligence_service as ti

        profile = _safe(lambda: ti.build_territorial_profile(str(entity["entity_id"])), {}) or {}
        sites = ((profile.get("assets") or {}).get("sites_sample") or [])[:5]
        scores = []
        nearest = None
        for site in sites:
            lon, lat = site.get("longitude"), site.get("latitude")
            if lon is None or lat is None:
                continue
            acc = _safe(lambda: transport_service.site_accessibility(lon=float(lon), lat=float(lat)), {}) or {}
            if acc.get("nearest_road") and nearest is None:
                nearest = acc
            sc = (acc.get("accessibility") or {}).get("score")
            if sc is not None:
                scores.append(float(sc))
        if not scores and not nearest:
            quality = _safe(transport_service.get_quality_report, {}) or {}
            return _section(
                STATUS_PARTIAL,
                {
                    "display": "Données insuffisantes",
                    "transport_quality": (quality.get("database_stats") or quality.get("pipeline_report", {}).get("counts")),
                    "formula": transport_service.ACCESSIBILITY_FORMULA,
                },
                note="Aucun site géoréférencé utilisable pour ce territoire",
                source="transport",
            )
        avg = round(sum(scores) / len(scores), 1) if scores else None
        return _section(
            STATUS_SUCCESS if avg is not None else STATUS_PARTIAL,
            {
                "avg_score": avg,
                "sites_scored": len(scores),
                "sample_nearest_road": (nearest or {}).get("nearest_road"),
                "sample_justification": ((nearest or {}).get("accessibility") or {}).get("justification"),
                "formula": transport_service.ACCESSIBILITY_FORMULA,
            },
            source="transport + fdsu_sites",
        )
    return _unavailable("Accessibilité non calculée pour ce niveau", "transport")


def section_energy(_entity: dict[str, Any]) -> dict[str, Any]:
    return _unavailable("Données non encore intégrées — référentiel Énergie (NDF planned)", "ndf/energy")


def section_economy(entity: dict[str, Any]) -> dict[str, Any]:
    if entity.get("entity_type") == "territoire":
        from api.services import territorial_intelligence_service as ti

        profile = _safe(lambda: ti.build_territorial_profile(str(entity["entity_id"])), {}) or {}
        eco = ((profile.get("sections") or {}).get("economy")) if isinstance(profile, dict) else None
        if eco:
            return _section(STATUS_PARTIAL, {"economy": eco}, note="Champs TI — souvent not_sourced", source="territorial_intelligence")
    return _unavailable("Données économiques non encore intégrées", "ndf/economy")


def section_programs(entity: dict[str, Any]) -> dict[str, Any]:
    etype = entity.get("entity_type")
    if etype == "territoire":
        from api.services import territorial_intelligence_service as ti

        profile = _safe(lambda: ti.build_territorial_profile(str(entity["entity_id"])), {}) or {}
        assets = profile.get("assets") or {}
        programs = (profile.get("sections") or {}).get("programs")
        return _section(
            STATUS_SUCCESS if assets or programs else STATUS_PARTIAL,
            {
                "sites_sample": assets.get("sites_sample") or [],
                "sites_scored_top": assets.get("sites_scored_top") or [],
                "ccn": assets.get("ccn"),
                "programs_section": programs,
                "note_ccn": "Site FDSU ≠ CCN",
            },
            source="territorial_intelligence / programs / ccn",
        )
    if etype == "province":
        from api.services import territorial_summary_service as tst

        summary = _safe(
            lambda: tst.build_entity_summary("province", str(entity.get("entity_id")), entity.get("nom")),
            {},
        ) or {}
        fields = {f.get("label"): f for f in (summary.get("fields") or [])}
        return _section(
            STATUS_SUCCESS,
            {
                "sites_fdsu": fields.get("Sites FDSU"),
                "sites_priority": fields.get("Sites prioritaires"),
                "ccn": fields.get("CCN"),
            },
            source="territorial_summary",
        )
    return _unavailable("Programmes non agrégés pour ce niveau", "programs")


def section_decision(entity: dict[str, Any]) -> dict[str, Any]:
    if entity.get("entity_type") == "territoire":
        from api.services import territorial_intelligence_service as ti

        profile = _safe(lambda: ti.build_territorial_profile(str(entity["entity_id"])), {}) or {}
        priority = (profile.get("sections") or {}).get("priority") or profile.get("priority")
        explain = _safe(lambda: ti.explain_territory(str(entity["entity_id"])), None)
        recommendations = _safe(lambda: ti.build_recommendations(str(entity["entity_id"])), {})
        status = STATUS_SUCCESS if priority else STATUS_PARTIAL
        return _section(
            status,
            {
                "priority": priority,
                "recommendations": recommendations,
                "explain": explain,
                "scenarios_hint": ["invest_priority", "territory_priority", "dg_dossier"],
            },
            source="territorial_intelligence / decision",
        )
    if entity.get("entity_type") == "province":
        from api.services import territorial_summary_service as tst

        layer = _safe(lambda: tst.build_province_layer("priority"), {}) or {}
        feats = layer.get("features") or []
        if isinstance(feats, dict):
            feats = feats.get("features") or []
        key = " ".join(str(entity.get("nom") or "").lower().split())
        match = next(
            (
                f
                for f in feats
                if " ".join(str((f.get("properties") or {}).get("name") or "").lower().split()) == key
            ),
            None,
        )
        if not match:
            return _unavailable("Pas de métrique de priorité pour cette province", "territorial_summary")
        props = match.get("properties") or {}
        return _section(
            STATUS_SUCCESS,
            {
                "priority_metric": props.get("display"),
                "class_label": props.get("class_label"),
                "value": props.get("value"),
                "source": props.get("source"),
                "scenarios_hint": ["invest_priority", "dg_dossier"],
            },
            source="territorial_summary / decision scores",
        )
    return _unavailable("Décision non calculée pour ce niveau", "decision")


def section_quality(entity: dict[str, Any]) -> dict[str, Any]:
    from api.services import national_data_fabric_service as ndf

    registries = ["administrative", "population", "telecom", "health", "transport", "fdsu_sites", "ccn", "prioritization"]
    rows = []
    for rid in registries:
        q = _safe(lambda r=rid: ndf.compute_quality(r), {}) or {}
        rows.append(
            {
                "registry_id": rid,
                "status": (q.get("registry") or {}).get("status"),
                "measured": (q.get("summary") or {}).get("measured"),
                "insufficient": (q.get("summary") or {}).get("insufficient"),
            }
        )
    return _section(
        STATUS_SUCCESS,
        {
            "entity_confidence": entity.get("source_administrative"),
            "ndf_registries": rows,
            "rule": "Données DEMO doivent être signalées explicitement",
        },
        source="national_data_fabric",
    )


def section_timeline(entity: dict[str, Any]) -> dict[str, Any]:
    """Timeline unifiée extensible — sans case_history.json comme source centrale."""
    events: list[dict[str, Any]] = []
    events.append(
        {
            "at": _now(),
            "kind": "twin_open",
            "label": f"Ouverture du jumeau — {entity.get('nom')}",
            "source": "territorial_digital_twin",
        }
    )
    # Import transport si dispo
    from api.services import transport_service

    quality = _safe(transport_service.get_quality_report, {}) or {}
    generated = ((quality.get("pipeline_report") or {}).get("_meta") or {}).get("generated_at")
    if generated:
        events.append(
            {
                "at": generated,
                "kind": "import",
                "label": "Import routes principales (pipeline transport)",
                "source": "transport.pipeline",
            }
        )
    # NCI quality
    from api.services import coverage_intelligence_service as nci

    nci_q = _safe(nci.get_quality_report, {}) or {}
    nci_at = (nci_q.get("_meta") or {}).get("generated_at")
    if nci_at:
        events.append(
            {
                "at": nci_at,
                "kind": "recalc",
                "label": "Rapport qualité NCI",
                "source": "coverage_intelligence",
            }
        )
    events.sort(key=lambda e: str(e.get("at") or ""), reverse=True)
    return _section(
        STATUS_PARTIAL if len(events) <= 1 else STATUS_SUCCESS,
        {"events": events, "persistence": "extensible DB — hors case_history.json"},
        note="Socle timeline — persistance dédiée prévue",
        source="tdt",
    )


def _compose_section(name: str, builder: Callable[[], dict[str, Any]]) -> tuple[str, dict[str, Any]]:
    try:
        result = builder()
        status = ((result or {}).get("_section") or {}).get("status") or STATUS_SUCCESS
        return name, result
    except Exception as exc:
        return name, _section(STATUS_ERROR, {"display": "Données insuffisantes"}, note=str(exc), source="tdt")


def build_twin(entity_type: str, entity_id: str, *, sections: list[str] | None = None) -> dict[str, Any] | None:
    entity = resolve_entity(entity_type, entity_id)
    if not entity:
        return None

    wanted = set(sections or [
        "summary", "connectivity", "public_services", "accessibility",
        "energy", "economy", "programs", "decision", "quality", "timeline",
    ])
    builders: dict[str, Callable[[], dict[str, Any]]] = {
        "summary": lambda: section_summary(entity),
        "connectivity": lambda: section_connectivity(entity),
        "public_services": lambda: section_public_services(entity),
        "accessibility": lambda: section_accessibility(entity),
        "energy": lambda: section_energy(entity),
        "economy": lambda: section_economy(entity),
        "programs": lambda: section_programs(entity),
        "decision": lambda: section_decision(entity),
        "quality": lambda: section_quality(entity),
        "timeline": lambda: section_timeline(entity),
    }

    composed: dict[str, Any] = {}
    section_status: dict[str, str] = {}
    # Composition séquentielle résiliente (évite les deadlocks psycopg2 multi-thread).
    # Le parallélisme UI reste assuré via les endpoints sectionnels + AbortController.
    for name in wanted:
        if name not in builders:
            continue
        _n, payload = _compose_section(name, builders[name])
        composed[name] = payload
        section_status[name] = ((payload or {}).get("_section") or {}).get("status") or STATUS_ERROR

    sources = []
    for name, payload in composed.items():
        src = ((payload or {}).get("_section") or {}).get("source")
        if src and src not in sources:
            sources.append(src)

    overall = STATUS_SUCCESS
    statuses = list(section_status.values())
    if any(s == STATUS_ERROR for s in statuses):
        overall = STATUS_PARTIAL
    elif any(s in {STATUS_PARTIAL, STATUS_UNAVAILABLE} for s in statuses):
        overall = STATUS_PARTIAL

    return {
        "_meta": {
            "version": ENGINE_VERSION,
            "generated_at": _now(),
            "overall_status": overall,
            "principle": "Composition des moteurs existants — aucune donnée inventée",
        },
        "entity": entity,
        "hierarchy": build_hierarchy(entity),
        "summary": composed.get("summary") or _unavailable("Non demandé"),
        "connectivity": composed.get("connectivity") or _unavailable("Non demandé"),
        "public_services": composed.get("public_services") or _unavailable("Non demandé"),
        "accessibility": composed.get("accessibility") or _unavailable("Non demandé"),
        "energy": composed.get("energy") or _unavailable("Non demandé"),
        "economy": composed.get("economy") or _unavailable("Non demandé"),
        "programs": composed.get("programs") or _unavailable("Non demandé"),
        "decision": composed.get("decision") or _unavailable("Non demandé"),
        "quality": composed.get("quality") or _unavailable("Non demandé"),
        "timeline": (composed.get("timeline") or {}).get("events")
        if isinstance(composed.get("timeline"), dict) and "events" in (composed.get("timeline") or {})
        else composed.get("timeline") or [],
        "sources": sources,
        "section_status": section_status,
        "actions": [
            {"id": "open_ti", "label": "Intelligence territoriale", "hash": f"territorial-intelligence/{entity.get('entity_id')}" if entity.get("entity_type") == "territoire" else "territorial-intelligence"},
            {"id": "open_decision", "label": "Centre de Décision", "hash": "decision-view"},
            {"id": "open_tst", "label": "Synthèse territoriale", "hash": "decision-view"},
        ],
    }


def build_section(entity_type: str, entity_id: str, section: str) -> dict[str, Any] | None:
    twin = build_twin(entity_type, entity_id, sections=[section])
    if not twin:
        return None
    if section == "timeline":
        return {
            "_meta": twin["_meta"],
            "entity": twin["entity"],
            "timeline": twin.get("timeline"),
            "section_status": {section: twin["section_status"].get(section)},
        }
    return {
        "_meta": twin["_meta"],
        "entity": twin["entity"],
        section: twin.get(section),
        "section_status": {section: twin["section_status"].get(section)},
    }
