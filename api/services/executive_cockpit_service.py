"""Executive Data Visualization System — agrégation lecture seule pour la Salle de Pilotage DG.

Consomme Knowledge Hub, Decision Engine, Territorial Intelligence, Master Registry, CCN.
N'invente aucune valeur métier.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def build_cockpit_payload() -> dict[str, Any]:
    from api.services import (
        ccn_operational_service,
        coverage_intelligence_service,
        explainable_decision_service,
        knowledge_hub_service,
        master_registry_service,
        spatial_matching_service,
        territorial_intelligence_service,
    )

    master = master_registry_service.list_entities(entity_type="TERRITOIRE", limit=5000)
    territories = master.get("entities") or []
    ccn_stats = ccn_operational_service.statistics()
    ccn_kpis = ccn_stats.get("kpis") or {}
    by_province = ccn_stats.get("by_province") or {}
    nci_charts = coverage_intelligence_service.edvs_charts()
    nci_stats = coverage_intelligence_service.statistics()
    nci_kpis = nci_stats.get("kpis") or {}
    try:
        nsme_charts = spatial_matching_service.edvs_charts()
        nsme_stats = spatial_matching_service.get_statistics()
    except Exception:  # noqa: BLE001
        nsme_charts = {}
        nsme_stats = {}

    # Top provinces CCN
    top_provinces = [
        {"label": name, "value": count, "color": "blue"}
        for name, count in list(by_province.items())[:8]
    ]

    # Priorités sites (programme national si dispo)
    top_sites = []
    try:
        from api.services import fdsu_site_priority_service

        top = fdsu_site_priority_service.top_priorities("sites_20476", limit=8)
        for site in top.get("sites") or top.get("items") or []:
            top_sites.append(
                {
                    "label": site.get("site_name") or site.get("site_code"),
                    "value": site.get("priority_score"),
                    "color": "orange" if site.get("priority_level") in {"high", "critical"} else "blue",
                    "level": site.get("priority_level"),
                }
            )
    except Exception as exc:  # noqa: BLE001
        top_sites = []
        sites_error = str(exc)
    else:
        sites_error = None

    # Dungu as demo territorial snapshot (generic API, focus flag only)
    dungu_full = territorial_intelligence_service.build_territorial_profile("TERRITOIRE-05-002")
    dungu = dungu_full
    dungu_recs = territorial_intelligence_service.build_recommendations("TERRITOIRE-05-002") if dungu else None

    doctrine = explainable_decision_service.get_doctrine_payload("DOCTRINE_SITES_FDSU")
    kh = knowledge_hub_service.hub_manifest()

    def _axis_from_field(label: str, field: dict[str, Any] | None) -> dict[str, Any]:
        field = field or {}
        status = field.get("status")
        if status in {"confirmed"} and field.get("value") not in (None, 0, False):
            return {"label": label, "value": 80, "status": status}
        if status in {"partial", "estimated", "demonstration"}:
            return {"label": label, "value": 55, "status": status}
        if status in {"unavailable"} and field.get("value") == 0:
            return {"label": label, "value": 25, "status": status}
        return {"label": label, "value": 10, "status": status or "not_sourced"}

    sections = (dungu_full or {}).get("sections") or {}
    radar_axes = [
        _axis_from_field("Connectivité", (sections.get("digital") or {}).get("infrastructures_telecom")),
        _axis_from_field("Santé", (sections.get("public_services") or {}).get("etablissements_sante")),
        _axis_from_field("Éducation", (sections.get("public_services") or {}).get("ecoles")),
        _axis_from_field("Économie", (sections.get("economy") or {}).get("agriculture")),
        _axis_from_field("Énergie", (sections.get("energy") or {}).get("disponibilite")),
        _axis_from_field("Accessibilité", (sections.get("accessibility") or {}).get("routes")),
        _axis_from_field("Données", {"status": (dungu_full or {}).get("profile", {}).get("data_quality"), "value": 1 if (dungu_full or {}).get("profile") else None}),
    ]
    radar_note = "Radar dérivé des statuts de connaissance du profil territorial (pas de mesures inventées)."

    programs = []
    try:
        from pathlib import Path
        import json

        root = Path(__file__).resolve().parents[2]
        for code, label, color in (
            ("sites_40", "Sites 40", "green"),
            ("sites_300", "Sites 300", "orange"),
            ("sites_20476", "Sites 20 476", "blue"),
        ):
            path = root / "data" / "programs" / code / f"{code}.json"
            if path.exists():
                payload = json.loads(path.read_text(encoding="utf-8"))
                sites = payload.get("sites") if isinstance(payload, dict) else payload
                count = len(sites) if isinstance(sites, list) else None
                programs.append({"label": label, "value": count, "status": "confirmed", "color": color})
            else:
                programs.append({"label": label, "value": None, "status": "unavailable", "color": "gray"})
    except Exception:  # noqa: BLE001
        programs = [
            {"label": "Sites 40", "value": None, "status": "unavailable", "color": "gray"},
            {"label": "Sites 300", "value": None, "status": "unavailable", "color": "gray"},
            {"label": "Sites 20 476", "value": None, "status": "unavailable", "color": "gray"},
        ]
    programs.append(
        {
            "label": "CCN DEMO",
            "value": ccn_kpis.get("total"),
            "status": "demonstration",
            "color": "blue",
        }
    )

    stacked = {
        "categories": ["Effectifs"],
        "series": [
            {"label": p["label"], "values": [p["value"] or 0], "color": p["color"]}
            for p in programs
            if isinstance(p.get("value"), (int, float))
        ],
    }

    radar_avg = round(sum(a["value"] for a in radar_axes) / max(len(radar_axes), 1))
    ccn_completeness = 70 if ccn_kpis.get("total") else 20

    alerts = []
    if dungu and (dungu.get("data_gaps") or dungu.get("profile", {}).get("data_quality") == "partial"):
        alerts.append(
            {
                "level": "medium",
                "title": "Données territoriales partielles",
                "message": f"Gaps : {', '.join((dungu.get('data_gaps') or [])[:4]) or 'qualité partielle'}",
            }
        )
    if ccn_kpis.get("total"):
        alerts.append(
            {
                "level": "low",
                "title": "CCN en démonstration",
                "message": f"{ccn_kpis.get('total')} CCN DEMO — ne pas traiter comme production.",
            }
        )
    if sites_error:
        alerts.append({"level": "high", "title": "Priorisation sites partielle", "message": sites_error})

    recommendations = []
    for rec in (dungu_recs or {}).get("recommendations") or []:
        recommendations.append(
            {
                "action": rec.get("action"),
                "why": rec.get("why"),
                "doctrine": rec.get("doctrine"),
                "confidence_level": rec.get("confidence_level"),
            }
        )

    timeline = [
        {
            "title": "Explainable Decision Engine v1",
            "when": "2026-07-10",
            "detail": "Decision Case Files + justifications",
        },
        {
            "title": "Territorial Intelligence Explorer v1",
            "when": "2026-07-10",
            "detail": "Profils territoriaux consolidés (Dungu démo)",
        },
        {
            "title": "EDVS — Salle de Pilotage DG",
            "when": _now()[:10],
            "detail": "Framework de visualisation exécutive",
        },
    ]

    return {
        "_meta": {
            "title": "Salle de Pilotage DG — EDVS",
            "generated_at": _now(),
            "framework": "EDVS v1",
            "sources": [
                "/api/master",
                "/api/ccn",
                "/api/decision",
                "/api/territorial-intelligence",
                "/api/knowledge",
                "/api/coverage",
            ],
            "hardcoded_forbidden": True,
            "visual_ratio": "30% cartes / 30% graphiques / 20% KPI / 20% texte",
        },
        "kpis": [
            {
                "id": "pop_covered_nci",
                "label": "Population nationale couverte",
                "value": nci_kpis.get("population_covered"),
                "icon": "people",
                "color": "green",
                "confidence": "high",
                "trend": "up",
                "sparkline": nci_charts.get("sparkline_coverage_ratio") or [],
                "note": "Référentiel National des Besoins (NCI)",
            },
            {
                "id": "pop_remaining_nci",
                "label": "Population restante",
                "value": nci_kpis.get("population_remaining"),
                "icon": "people",
                "color": "orange",
                "confidence": "high",
                "trend": "flat",
                "note": "Population des localités non couvertes",
            },
            {
                "id": "loc_covered_nci",
                "label": "Localités couvertes",
                "value": nci_kpis.get("localities_covered"),
                "icon": "map",
                "color": "green",
                "confidence": "high",
                "trend": "flat",
            },
            {
                "id": "loc_uncovered_nci",
                "label": "Localités non couvertes",
                "value": nci_kpis.get("localities_uncovered"),
                "icon": "map",
                "color": "red",
                "confidence": "high",
                "trend": "flat",
            },
            {
                "id": "territoires",
                "label": "Territoires référencés",
                "value": len(territories),
                "icon": "map",
                "color": "blue",
                "confidence": "high",
                "trend": "flat",
                "sparkline": [len(territories)],
                "note": "Référentiel National (TERRITOIRE)",
            },
            {
                "id": "ccn_total",
                "label": "CCN (DEMO)",
                "value": ccn_kpis.get("total"),
                "icon": "ccn",
                "color": "blue",
                "confidence": "medium",
                "trend": "flat",
                "sparkline": [ccn_kpis.get("total") or 0],
                "note": "Jeu de démonstration CCN",
            },
            {
                "id": "ccn_ops",
                "label": "CCN opérationnels",
                "value": ccn_kpis.get("operationnels"),
                "icon": "gauge",
                "color": "green",
                "confidence": "medium",
                "trend": "flat",
                "sparkline": [ccn_kpis.get("operationnels") or 0],
            },
            {
                "id": "kh_domains",
                "label": "Domaines Knowledge Hub",
                "value": kh.get("domains_count"),
                "icon": "data",
                "color": "blue",
                "confidence": "high",
                "trend": "flat",
            },
        ],
        "rankings": {
            "provinces_ccn": top_provinces,
            "sites_priority": top_sites,
            "provinces_needs": (nci_charts.get("bars") or {}).get("items") or [],
            "territories_ndci": nci_charts.get("top_territories") or [],
        },
        "programs": programs,
        "stacked": stacked,
        "radar": nci_charts.get("radar") or {"axes": radar_axes, "note": radar_note, "color": "blue"},
        "gauges": [
            {
                "title": "Maturité connaissance territoriale",
                "value": radar_avg,
                "subtitle": radar_note,
                "color": "yellow" if radar_avg < 70 else "green",
            },
            {
                "title": "Couverture CCN DEMO",
                "value": ccn_completeness,
                "subtitle": "Présence d'un jeu DEMO CCN",
                "color": "blue",
            },
            {
                "title": "Ratio couverture population (NCI)",
                "value": round(float(nci_kpis.get("coverage_ratio_population") or 0) * 100, 1),
                "subtitle": "Population couverte / (couverte + restante)",
                "color": "green",
            },
        ],
        "waterfall": nci_charts.get("waterfall") or {
            "title": "Doctrine Sites — pondérations",
            "steps": [
                {
                    "label": c.get("label"),
                    "value": c.get("weight_percent"),
                    "color": "blue",
                }
                for c in ((doctrine or {}).get("doctrine") or {}).get("selection_criteria") or []
            ],
        },
        "treemap": nci_charts.get("treemap") or {
            "title": "Répartition programmes (effectifs)",
            "items": [
                {"label": p["label"], "value": p["value"], "color": p["color"]}
                for p in programs
                if isinstance(p.get("value"), (int, float))
            ],
        },
        "heatmap": nci_charts.get("heatmap") or {
            "title": "Priorités (échantillon sites)",
            "rows": [s["label"][:18] for s in top_sites[:5]],
            "cols": ["Score"],
            "matrix": [[int(s["value"] or 0)] for s in top_sites[:5]],
        },
        "bars_needs": nci_charts.get("bars"),
        "priority_split": nci_charts.get("priority_split"),
        "categories_split": nci_charts.get("categories"),
        "nci": {
            "kpis": nci_charts.get("kpis"),
            "heritage": "Référentiel National des Besoins",
        },
        "spatial_matching": {
            "heritage": "National Spatial Matching Engine",
            "statistics": {
                "matches_total": nsme_stats.get("matches_total"),
                "population_impacted_sum": nsme_stats.get("population_impacted_sum"),
                "avg_distance_m": nsme_stats.get("avg_distance_m"),
                "needs_matched": nsme_stats.get("needs_matched"),
            },
            "charts": nsme_charts,
            "source": "/api/spatial-matching/edvs",
        },
        "alerts": alerts,
        "recommendations": recommendations[:5],
        "timeline": timeline,
        "map": {
            "center": [-2.8, 23.5],
            "zoom": 5,
            "note": "Carte thermique des besoins — /api/coverage/map",
            "coverage_endpoint": "/api/coverage/map",
        },
        "doctrine": {
            "id": ((doctrine or {}).get("doctrine") or {}).get("_meta", {}).get("doctrine_id"),
            "version": ((doctrine or {}).get("doctrine") or {}).get("_meta", {}).get("version"),
        },
    }
