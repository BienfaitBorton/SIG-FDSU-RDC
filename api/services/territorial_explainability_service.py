"""Territorial Explainability & Drill-down — contrat commun Data First.

Chaîne obligatoire : Combien ? Lesquels ? Où ? Caractéristiques ? Pourquoi ? Action ?
Aucune invention : attributs absents → « Non renseignée ».
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from psycopg2.extras import RealDictCursor

from api.config import DATA_MODE, connect_db
from api.services.territorial_entity_resolver import resolve_territory
from api.services.territorial_profile_service import (
    ST_OPERATIONAL,
    ST_PARTIAL,
    ST_PENDING,
    ST_ANOMALY,
    ST_ERROR,
    indicator,
)

ENGINE = "territorial-explainability-1.0.0"

DOMAIN_LABELS = {
    "telecom": "Télécommunications",
    "fiber": "Fibre",
    "health": "Santé",
    "routes": "Routes",
    "programs": "Programmes FDSU",
    "sites_20476": "Sites programme 20 476",
    "sites_300": "Sites 300",
    "sites_40": "Sites 40",
    "ccn": "CCN",
    "admin": "Administratif",
    "localities": "Localités",
    "localites": "Localités",
    "groupements": "Groupements",
    "collectivites": "Collectivités",
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _props(row: dict[str, Any]) -> dict[str, Any]:
    p = row.get("properties")
    return p if isinstance(p, dict) else {}


def _nr(value: Any, fallback: str = "Non renseignée") -> str:
    if value is None or value == "" or str(value).strip().lower() in {"null", "none", "nan"}:
        return fallback
    return str(value)


def explain_payload(
    *,
    domain: str,
    count: int | None,
    status: str,
    source: str,
    confidence: str,
    headline: str,
    business_impact: str,
    recommendation: str,
    breakdown: list[dict[str, Any]] | None = None,
    top_items: list[dict[str, Any]] | None = None,
    quality: dict[str, Any] | None = None,
    pagination: dict[str, Any] | None = None,
    technical: dict[str, Any] | None = None,
    actions: list[dict[str, str]] | None = None,
    extras: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "domain": domain,
        "domain_label": DOMAIN_LABELS.get(domain, domain),
        "summary": {
            "count": count,
            "status": status,
            "source": source,
            "confidence": confidence,
            "updated_at": _now(),
            "headline": headline,
            "business_impact": business_impact,
            "recommendation": recommendation,
        },
        "breakdown": breakdown or [],
        "top_items": top_items or [],
        "quality": quality or {},
        "pagination": pagination or {"page": 1, "page_size": len(top_items or []), "total": count},
        "actions": actions
        or [
            {"id": "details", "label": f"Voir les détails"},
            {"id": "map", "label": "Afficher sur la carte"},
            {"id": "impact", "label": "Analyser l’impact"},
        ],
        "technical": technical or {},
        **(extras or {}),
    }


def _db_id(entity: dict[str, Any]) -> int | None:
    return entity.get("db_id")


def _classify_infra_type(infra_type: str | None) -> str:
    t = (infra_type or "").lower()
    if "fttx" in t or "fibre" in t or "fiber" in t:
        return "Nœuds FTTX / fibre"
    if "rcs" in t:
        return "RCS"
    if "radio" in t or "macro" in t:
        return "Sites radio / BTS"
    if "normal site" in t or "site" in t:
        return "Sites radio / BTS"
    if "pole" in t or "pyl" in t or "tower" in t:
        return "Pylônes"
    if "node" in t:
        return "Nœuds"
    return "Autres infrastructures"


def _tech_bucket(raw: str | None) -> str:
    t = (raw or "").upper()
    if not t or t in {"NON RENSEIGNÉE", "NON RENSEIGNEE"}:
        return "Non renseignée"
    has2 = "2G" in t
    has3 = "3G" in t
    has4 = "4G" in t
    has5 = "5G" in t
    parts = []
    if has2:
        parts.append("2G")
    if has3:
        parts.append("3G")
    if has4:
        parts.append("4G")
    if has5:
        parts.append("5G")
    if parts:
        return "-".join(parts)
    if "RADIO" in t:
        return "Radio (détail non précisé)"
    return "Non renseignée" if not t.strip() else raw or "Non renseignée"


def build_telecom_explain(territory_ref: str, *, page: int = 1, page_size: int = 50) -> dict[str, Any] | None:
    entity = resolve_territory(territory_ref)
    if not entity:
        return None
    db_id = _db_id(entity)
    if DATA_MODE != "db" or not db_id:
        return explain_payload(
            domain="telecom",
            count=None,
            status=ST_ANOMALY,
            source="telecom.infrastructure",
            confidence="low",
            headline="Télécommunications — recherche non exécutable",
            business_impact="Impact non encore calculé — référentiel non interrogé en mode actuel.",
            recommendation="Basculer en DATA_MODE=db pour exposer les infrastructures.",
        )

    page = max(1, page)
    page_size = min(max(1, page_size), 200)
    offset = (page - 1) * page_size

    with connect_db() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT i.id, i.infra_code, i.infra_name, i.infra_type, i.technology, i.status,
                       i.operator_id, o.operator_name, o.operator_code,
                       i.latitude, i.longitude, i.properties, i.source_file
                FROM telecom.infrastructure i
                JOIN public.territoires t ON t.id = %s
                LEFT JOIN telecom.operators o ON o.id = i.operator_id
                WHERE i.geom IS NOT NULL AND ST_Intersects(i.geom, t.geom)
                ORDER BY COALESCE(o.operator_name, ''), i.infra_name
                """,
                (db_id,),
            )
            rows = [dict(r) for r in cur.fetchall()]

    total = len(rows)
    type_counts: dict[str, int] = {}
    op_counts: dict[str, int] = {}
    tech_counts: dict[str, int] = {}
    items = []
    for r in rows:
        props = _props(r)
        owner = props.get("OWNER_Sites") or r.get("operator_name")
        op_label = _nr(owner or r.get("operator_name"), "Opérateur non renseigné")
        class_label = _classify_infra_type(r.get("infra_type"))
        tech_raw = props.get("Technologie") or r.get("technology")
        tech = _tech_bucket(str(tech_raw) if tech_raw else None)
        type_counts[class_label] = type_counts.get(class_label, 0) + 1
        op_counts[op_label] = op_counts.get(op_label, 0) + 1
        tech_counts[tech] = tech_counts.get(tech, 0) + 1
        items.append(
            {
                "id": r.get("id"),
                "name": r.get("infra_name") or r.get("infra_code") or f"Infra {r.get('id')}",
                "type": _nr(r.get("infra_type")),
                "type_group": class_label,
                "operator": op_label,
                "technology": _nr(tech_raw, "Non renseignée"),
                "technology_group": tech,
                "locality": _nr(props.get("Town_Village"), "Non renseignée"),
                "status": _nr(r.get("status") or props.get("Site_Status"), "Non renseigné"),
                "tower_height_m": props.get("Tower_Height"),
                "coordinates": {"latitude": r.get("latitude"), "longitude": r.get("longitude")},
                "source": "telecom.infrastructure",
                "confidence": "high",
                "distance_m": None,
            }
        )

    breakdown = [{"label": k, "count": v} for k, v in sorted(type_counts.items(), key=lambda x: -x[1])]
    operators = [{"label": k, "count": v} for k, v in sorted(op_counts.items(), key=lambda x: -x[1])]
    technologies = [{"label": k, "count": v} for k, v in sorted(tech_counts.items(), key=lambda x: -x[1])]
    op_names = [o["label"] for o in operators if o["label"] != "Opérateur non renseigné"]

    impact = (
        f"La présence de {len(op_names)} opérateur(s) ({', '.join(op_names)}) améliore la résilience du service "
        f"sur le territoire, avec {total} infrastructure(s) détectée(s)."
        if op_names
        else f"{total} infrastructure(s) détectée(s) — diversité opérateurs limitée ou non renseignée."
    )
    if total == 0:
        impact = "Recherche spatiale exécutée : aucune infrastructure télécom dans le polygone territorial."

    page_items = items[offset : offset + page_size]
    return explain_payload(
        domain="telecom",
        count=total,
        status=ST_OPERATIONAL,
        source="telecom.infrastructure (+ telecom.operators)",
        confidence="high",
        headline=f"Télécommunications — {total} infrastructure(s)",
        business_impact=impact if total else "Aucun actif télécom spatialement rattaché — couverture à investiguer.",
        recommendation="Voir les infrastructures et croiser avec les localités non couvertes (NCI).",
        breakdown=breakdown,
        top_items=page_items,
        quality={"operators_named": len(op_names), "rows_with_coords": sum(1 for i in items if i["coordinates"]["latitude"] is not None)},
        pagination={"page": page, "page_size": page_size, "total": total, "pages": max(1, (total + page_size - 1) // page_size)},
        technical={"method": "ST_Intersects(telecom.infrastructure, territoires.geom)", "db_id": db_id},
        extras={"operators": operators, "technologies": technologies},
        actions=[
            {"id": "details", "label": f"Voir les {total} infrastructures"},
            {"id": "map", "label": "Afficher sur la carte"},
            {"id": "impact", "label": "Analyser l’impact"},
        ],
    )


def build_fiber_explain(territory_ref: str, *, page: int = 1, page_size: int = 50) -> dict[str, Any] | None:
    entity = resolve_territory(territory_ref)
    if not entity:
        return None
    db_id = _db_id(entity)
    if DATA_MODE != "db" or not db_id:
        return explain_payload(
            domain="fiber",
            count=None,
            status=ST_ANOMALY,
            source="telecom.infrastructure / telecom.network_lines",
            confidence="low",
            headline="Fibre — recherche non exécutable",
            business_impact="Impact non encore calculé.",
            recommendation="Activer le mode DB.",
        )

    page = max(1, page)
    page_size = min(max(1, page_size), 200)
    offset = (page - 1) * page_size

    with connect_db() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT i.id, i.infra_name, i.infra_type, i.technology, i.operator_id,
                       o.operator_name, i.latitude, i.longitude, i.properties
                FROM telecom.infrastructure i
                JOIN public.territoires t ON t.id = %s
                LEFT JOIN telecom.operators o ON o.id = i.operator_id
                WHERE i.geom IS NOT NULL AND ST_Intersects(i.geom, t.geom)
                  AND (i.infra_type ILIKE '%%fttx%%' OR i.infra_type ILIKE '%%fibre%%' OR i.infra_type ILIKE '%%fiber%%')
                ORDER BY i.infra_name
                """,
                (db_id,),
            )
            nodes = [dict(r) for r in cur.fetchall()]
            cur.execute(
                """
                SELECT nl.id, nl.line_code, nl.line_name, nl.line_type, nl.technology,
                       nl.operator_id, o.operator_name,
                       ROUND((ST_Length(ST_Intersection(nl.geom, t.geom)::geography)/1000.0)::numeric, 3) AS length_km
                FROM telecom.network_lines nl
                JOIN public.territoires t ON t.id = %s
                LEFT JOIN telecom.operators o ON o.id = nl.operator_id
                WHERE nl.geom IS NOT NULL AND ST_Intersects(nl.geom, t.geom)
                ORDER BY length_km DESC NULLS LAST
                """,
                (db_id,),
            )
            lines = [dict(r) for r in cur.fetchall()]

    node_items = [
        {
            "id": f"node-{n['id']}",
            "name": n.get("infra_name") or f"Nœud {n['id']}",
            "type": _nr(n.get("infra_type")),
            "operator": _nr(n.get("operator_name") or _props(n).get("OWNER_Sites"), "Non renseigné"),
            "technology": _nr(n.get("technology") or _props(n).get("Technologie"), "Non renseignée"),
            "locality": _nr(_props(n).get("Town_Village"), "Non renseignée"),
            "coordinates": {"latitude": n.get("latitude"), "longitude": n.get("longitude")},
            "source": "telecom.infrastructure",
            "confidence": "high",
            "kind": "fttx_node",
        }
        for n in nodes
    ]
    line_items = [
        {
            "id": f"line-{ln['id']}",
            "name": ln.get("line_name") or ln.get("line_code") or f"Tronçon {ln['id']}",
            "type": _nr(ln.get("line_type")),
            "operator": _nr(ln.get("operator_name"), "Non renseigné"),
            "technology": _nr(ln.get("technology"), "Non renseignée"),
            "length_km": float(ln["length_km"]) if ln.get("length_km") is not None else None,
            "locality": "Non renseignée",
            "coordinates": None,
            "source": "telecom.network_lines",
            "confidence": "high",
            "kind": "network_line",
        }
        for ln in lines
    ]
    total_length = round(sum(float(x["length_km"]) for x in line_items if x.get("length_km") is not None), 2)
    all_items = node_items + line_items
    breakdown = [
        {"label": "Nœuds FTTX", "count": len(nodes)},
        {"label": "Tronçons network_lines", "count": len(lines)},
    ]
    headline = f"Fibre — {len(nodes)} nœud(s) FTTX"
    if lines:
        headline += f" · {len(lines)} tronçon(s)"
        if total_length:
            headline += f" · {total_length} km (intersection)"

    impact = (
        f"{len(nodes)} nœud(s) FTTX détecté(s)"
        + (f" et {len(lines)} tronçon(s) de réseau ({total_length} km dans le territoire)." if lines else ".")
        + " Ce n’est pas équivalent à un réseau fibre complet pour toutes les localités."
    )
    limit_note = None
    if not lines:
        limit_note = "Aucune table linéaire fibre dédiée hors telecom.network_lines — aucun tronçon intersecté."

    return explain_payload(
        domain="fiber",
        count=len(nodes),
        status=ST_OPERATIONAL if (nodes or lines) else ST_OPERATIONAL,
        source="telecom.infrastructure (FTTX) + telecom.network_lines",
        confidence="medium" if nodes or lines else "high",
        headline=headline,
        business_impact=impact if (nodes or lines) else "Recherche exécutée : aucun nœud FTTX ni tronçon dans le territoire.",
        recommendation="Afficher nœuds et tronçons sur la carte ; croiser avec sites FDSU pour potentiel de raccordement.",
        breakdown=breakdown,
        top_items=all_items[offset : offset + page_size],
        quality={"network_lines_km": total_length, "limit_note": limit_note},
        pagination={"page": page, "page_size": page_size, "total": len(all_items)},
        technical={"method": "ST_Intersects FTTX nodes + network_lines", "db_id": db_id},
        extras={"nodes_count": len(nodes), "lines_count": len(lines), "length_km": total_length, "limit_note": limit_note},
        actions=[
            {"id": "details", "label": "Voir la fibre"},
            {"id": "map", "label": "Afficher sur la carte"},
            {"id": "impact", "label": "Analyser l’impact"},
        ],
    )


def build_health_explain(territory_ref: str, *, page: int = 1, page_size: int = 50) -> dict[str, Any] | None:
    entity = resolve_territory(territory_ref)
    if not entity:
        return None
    db_id = _db_id(entity)
    if DATA_MODE != "db" or not db_id:
        return explain_payload(
            domain="health",
            count=None,
            status=ST_ANOMALY,
            source="health.health_facilities",
            confidence="low",
            headline="Santé — recherche non exécutable",
            business_impact="Impact non encore calculé.",
            recommendation="Activer le mode DB.",
        )

    page = max(1, page)
    page_size = min(max(1, page_size), 200)
    offset = (page - 1) * page_size

    with connect_db() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT f.id, f.name, f.facility_type_code, tname.name AS facility_type_name,
                       f.province_name, f.territory_name, f.locality_name,
                       ST_Y(f.geom) AS latitude, ST_X(f.geom) AS longitude,
                       f.data_source, f.official_code
                FROM health.health_facilities f
                JOIN public.territoires t ON t.id = %s
                LEFT JOIN health.health_facility_types tname ON tname.code = f.facility_type_code
                WHERE f.geom IS NOT NULL AND ST_Within(f.geom, t.geom)
                ORDER BY f.name
                """,
                (db_id,),
            )
            rows = [dict(r) for r in cur.fetchall()]

    total = len(rows)
    by_code: dict[str, int] = {}
    for r in rows:
        code = r.get("facility_type_code") or "OTHER"
        by_code[code] = by_code.get(code, 0) + 1

    classified = {"HGR": 0, "CS": 0, "PS": 0, "OTHER": 0}
    for code, n in by_code.items():
        cu = str(code).upper()
        if cu in {"HGR", "HOSPITAL", "CH"}:
            classified["HGR"] += n
        elif cu in {"CS", "CSR", "CM", "CLINIC", "POLYCLINIC"}:
            classified["CS"] += n
        elif cu in {"PS", "DISP", "SSC", "MAT"}:
            classified["PS"] += n
        else:
            classified["OTHER"] += n

    typology_usable = classified["OTHER"] < total  # if all OTHER, typology not usable for HGR/CS/PS
    typology = []
    for key, label in (("HGR", "HGR / Hôpitaux"), ("CS", "Centres de santé"), ("PS", "Postes de santé")):
        if classified["OTHER"] == total and total > 0:
            typology.append(
                {
                    "label": label,
                    "count": None,
                    "display": "Non calculable",
                    "note": "Typologie des établissements non normalisée (codes OTHER / absents).",
                }
            )
        else:
            typology.append({"label": label, "count": classified[key], "display": str(classified[key])})
    typology.append({"label": "OTHER / non classés", "count": classified["OTHER"], "display": str(classified["OTHER"])})

    items = [
        {
            "id": r["id"],
            "name": r.get("name") or f"Établissement {r['id']}",
            "type": _nr(r.get("facility_type_name") or r.get("facility_type_code"), "Non classé"),
            "type_code": r.get("facility_type_code") or "OTHER",
            "locality": _nr(r.get("locality_name"), "Non renseignée"),
            "coordinates": {"latitude": r.get("latitude"), "longitude": r.get("longitude")},
            "source": r.get("data_source") or "health.health_facilities",
            "confidence": "high",
            "official_code": r.get("official_code"),
        }
        for r in rows
    ]

    breakdown = [{"label": k, "count": v} for k, v in sorted(by_code.items(), key=lambda x: -x[1])[:12]]
    impact = (
        f"{total} établissement(s) de santé localisé(s) dans le territoire."
        + (
            " La typologie HGR/CS/PS n’est pas fiable : majorité de codes non normalisés."
            if not typology_usable and total
            else ""
        )
    )

    return explain_payload(
        domain="health",
        count=total,
        status=ST_PARTIAL if (total and not typology_usable) else ST_OPERATIONAL,
        source="health.health_facilities",
        confidence="high" if typology_usable else "medium",
        headline=f"Santé — {total} établissement(s)",
        business_impact=impact if total else "Recherche spatiale exécutée : aucun établissement dans le polygone.",
        recommendation="Voir les établissements et croiser avec accessibilité / sites FDSU.",
        breakdown=breakdown,
        top_items=items[offset : offset + page_size],
        pagination={"page": page, "page_size": page_size, "total": total},
        technical={"method": "ST_Within(health.health_facilities, territoires.geom)", "typology_usable": typology_usable},
        extras={"typology": typology, "by_type_code": by_code},
        actions=[
            {"id": "details", "label": "Voir les établissements de santé"},
            {"id": "map", "label": "Afficher sur la carte"},
            {"id": "impact", "label": "Analyser l’impact"},
        ],
    )


def build_routes_explain(territory_ref: str, *, page: int = 1, page_size: int = 50) -> dict[str, Any] | None:
    entity = resolve_territory(territory_ref)
    if not entity:
        return None
    db_id = _db_id(entity)
    if DATA_MODE != "db" or not db_id:
        return explain_payload(
            domain="routes",
            count=None,
            status=ST_ANOMALY,
            source="transport.routes",
            confidence="low",
            headline="Routes — recherche non exécutable",
            business_impact="Impact non encore calculé.",
            recommendation="Activer le mode DB.",
        )

    page = max(1, page)
    page_size = min(max(1, page_size), 200)
    offset = (page - 1) * page_size

    with connect_db() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT r.id, r.nom, r.type_route, r.categorie, r.etat, r.revetement, r.numero, r.cl_admin,
                       COALESCE(r.longueur_m, ST_Length(ST_Intersection(r.geom, t.geom)::geography)) AS longueur_m,
                       r.source
                FROM transport.routes r
                JOIN public.territoires t ON t.id = %s
                WHERE r.geom IS NOT NULL AND ST_Intersects(r.geom, t.geom)
                ORDER BY longueur_m DESC NULLS LAST
                """,
                (db_id,),
            )
            rows = [dict(r) for r in cur.fetchall()]

    total = len(rows)
    length_km = round(sum(float(r["longueur_m"] or 0) for r in rows) / 1000.0, 2)
    by_cat: dict[str, int] = {}
    unnamed = 0
    for r in rows:
        cat = r.get("categorie") or r.get("type_route") or r.get("cl_admin") or "Non classé"
        by_cat[str(cat)] = by_cat.get(str(cat), 0) + 1
        if not r.get("nom"):
            unnamed += 1

    items = [
        {
            "id": r["id"],
            "name": r.get("nom") or (f"Axe {r.get('numero')}" if r.get("numero") else f"Tronçon {r['id']}"),
            "type": _nr(r.get("type_route")),
            "category": _nr(r.get("categorie") or r.get("cl_admin"), "Non classée"),
            "length_km": round(float(r["longueur_m"] or 0) / 1000.0, 3),
            "condition": _nr(r.get("etat"), "Non renseigné"),
            "surface": _nr(r.get("revetement"), "Non renseigné"),
            "numero": r.get("numero"),
            "source": r.get("source") or "transport.routes",
            "confidence": "high",
            "coordinates": None,
        }
        for r in rows
    ]
    named = [i["name"] for i in items if i.get("name") and not str(i["name"]).startswith("Tronçon")][:8]
    accessibility = "Moyenne"
    if length_km >= 100 and total >= 10:
        accessibility = "Bonne"
    elif total < 5 or length_km < 30:
        accessibility = "Faible"

    return explain_payload(
        domain="routes",
        count=total,
        status=ST_OPERATIONAL,
        source="transport.routes",
        confidence="high",
        headline=f"Routes — {total} tronçon(s) · {length_km} km",
        business_impact=(
            f"{total} tronçon(s) totalisant {length_km} km dans le territoire. "
            f"Accessibilité estimée : {accessibility} (heuristique longueur/nombre)."
        ),
        recommendation="Voir les routes et croiser avec sites FDSU pour contraintes logistiques.",
        breakdown=[{"label": k, "count": v} for k, v in sorted(by_cat.items(), key=lambda x: -x[1])],
        top_items=items[offset : offset + page_size],
        pagination={"page": page, "page_size": page_size, "total": total},
        technical={"method": "ST_Intersects(transport.routes, territoires.geom)"},
        extras={
            "length_km": length_km,
            "named_axes": named,
            "unnamed_count": unnamed,
            "accessibility_label": accessibility,
        },
        actions=[
            {"id": "details", "label": "Voir les routes"},
            {"id": "map", "label": "Afficher sur la carte"},
            {"id": "impact", "label": "Analyser l’impact"},
        ],
    )


def build_programs_explain(
    territory_ref: str, *, program: str = "sites_20476", page: int = 1, page_size: int = 50
) -> dict[str, Any] | None:
    from api.services.territorial_profile_service import _program_sites, _names_match

    entity = resolve_territory(territory_ref)
    if not entity:
        return None
    name = entity.get("name")
    program = program if program in {"sites_40", "sites_300", "sites_20476", "ccn"} else "sites_20476"

    if program == "ccn":
        try:
            from api.services import ccn_operational_service

            listed = ccn_operational_service.list_ccn(territoire=name, limit=200)
            rows = listed.get("ccn") or []
        except Exception:
            rows = []
        items = [
            {
                "id": r.get("id") or r.get("business_id"),
                "name": r.get("name") or r.get("business_id"),
                "type": r.get("ccn_type") or "CCN",
                "status": "DEMO",
                "program": "ccn",
                "coordinates": {"latitude": r.get("latitude"), "longitude": r.get("longitude")},
                "source": "demo_ccn.json",
                "confidence": "low",
                "locality": _nr(r.get("territoire")),
                "score": None,
                "priority": None,
            }
            for r in rows
        ]
        return explain_payload(
            domain="ccn",
            count=len(items),
            status="demonstration" if items else ST_OPERATIONAL,
            source="/api/ccn (DEMO)",
            confidence="low",
            headline=f"CCN — {len(items)} (jeu DEMO)",
            business_impact=(
                "Jeu CCN de démonstration uniquement — pas une base de production nationale."
                if items
                else "Recherche exécutée sur le jeu DEMO : aucun CCN pour ce territoire."
            ),
            recommendation="Ne pas fonder une décision d’investissement uniquement sur les CCN DEMO.",
            breakdown=[{"label": "DEMO", "count": len(items)}],
            top_items=items,
            actions=[{"id": "details", "label": "Voir les CCN"}, {"id": "map", "label": "Afficher sur la carte"}],
        )

    sites = _program_sites(program, name)
    # optional scoring sample
    scored_map: dict[str, dict[str, Any]] = {}
    try:
        from api.services import fdsu_site_priority_service

        for s in sites[:200]:
            try:
                sc = fdsu_site_priority_service.compute_national_site_score(s)
                key = str(s.get("site_code") or s.get("id") or s.get("site_name"))
                scored_map[key] = sc
            except Exception:
                continue
    except Exception:
        pass

    status_counts: dict[str, int] = {}
    priority_counts: dict[str, int] = {}
    items = []
    for s in sites:
        key = str(s.get("site_code") or s.get("id") or s.get("site_name"))
        sc = scored_map.get(key) or {}
        st = s.get("status") or s.get("operational_status") or "Statut non renseigné"
        status_counts[str(st)] = status_counts.get(str(st), 0) + 1
        pr = sc.get("priority_level") or s.get("priority_level") or "Non renseignée"
        priority_counts[str(pr)] = priority_counts.get(str(pr), 0) + 1
        items.append(
            {
                "id": key,
                "name": s.get("site_name") or key,
                "type": "Site FDSU",
                "program": program,
                "status": _nr(st, "Statut non renseigné"),
                "score": sc.get("priority_score"),
                "priority": _nr(pr, "Non renseignée"),
                "locality": _nr(s.get("localite") or s.get("groupement"), "Non renseignée"),
                "coordinates": {"latitude": s.get("latitude"), "longitude": s.get("longitude")},
                "source": f"data/programs/{program}",
                "confidence": "high" if sc else "medium",
            }
        )

    page = max(1, page)
    page_size = min(max(1, page_size), 200)
    offset = (page - 1) * page_size
    domain = program
    return explain_payload(
        domain=domain,
        count=len(items),
        status=ST_OPERATIONAL,
        source=f"data/programs/{program}",
        confidence="high",
        headline=f"{DOMAIN_LABELS.get(program, program)} — {len(items)} site(s)",
        business_impact=f"{len(items)} site(s) programme sur le territoire — base d’arbitrage FDSU.",
        recommendation="Voir les sites et ouvrir le dossier des plus prioritaires.",
        breakdown=[{"label": k, "count": v} for k, v in sorted(status_counts.items(), key=lambda x: -x[1])],
        top_items=items[offset : offset + page_size],
        pagination={"page": page, "page_size": page_size, "total": len(items)},
        extras={"priority_breakdown": [{"label": k, "count": v} for k, v in sorted(priority_counts.items(), key=lambda x: -x[1])]},
        actions=[
            {"id": "details", "label": "Voir les sites"},
            {"id": "map", "label": "Afficher sur la carte"},
            {"id": "dossier", "label": "Ouvrir le dossier"},
        ],
    )


def build_admin_explain(
    territory_ref: str, *, level: str = "localites", page: int = 1, page_size: int = 50
) -> dict[str, Any] | None:
    entity = resolve_territory(territory_ref)
    if not entity:
        return None
    db_id = _db_id(entity)
    if DATA_MODE != "db" or not db_id:
        return explain_payload(
            domain="admin",
            count=None,
            status=ST_ANOMALY,
            source="public.*",
            confidence="low",
            headline="Administratif — recherche non exécutable",
            business_impact="Impact non encore calculé.",
            recommendation="Activer le mode DB.",
        )

    level = level if level in {"collectivites", "groupements", "localites"} else "localites"
    page = max(1, page)
    page_size = min(max(1, page_size), 200)
    offset = (page - 1) * page_size

    with connect_db() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            if level == "collectivites":
                cur.execute(
                    """
                    SELECT c.id, c.code, c.nom, c.type, 'territoire' AS parent_level, t.nom AS parent_name,
                           ST_Y(ST_Centroid(c.geom)) AS latitude, ST_X(ST_Centroid(c.geom)) AS longitude
                    FROM public.collectivites c
                    JOIN public.territoires t ON t.id = c.parent_id
                    WHERE c.parent_id = %s
                    ORDER BY c.nom
                    """,
                    (db_id,),
                )
            elif level == "groupements":
                cur.execute(
                    """
                    SELECT DISTINCT g.id, g.code, g.nom, g.type,
                           CASE WHEN c.id IS NOT NULL THEN 'collectivité' ELSE 'territoire' END AS parent_level,
                           COALESCE(c.nom, t.nom) AS parent_name,
                           ST_Y(ST_Centroid(g.geom)) AS latitude, ST_X(ST_Centroid(g.geom)) AS longitude
                    FROM public.groupements g
                    JOIN public.territoires t ON t.id = %s
                    LEFT JOIN public.collectivites c ON g.parent_id = c.id AND c.parent_id = t.id
                    WHERE (c.parent_id = t.id OR g.parent_id = t.id
                           OR (g.geom IS NOT NULL AND ST_Within(g.geom, t.geom)))
                    ORDER BY g.nom
                    """,
                    (db_id,),
                )
            else:
                cur.execute(
                    """
                    SELECT l.id, l.code, l.nom, l.type, 'groupement/collectivité' AS parent_level,
                           NULL AS parent_name,
                           ST_Y(l.geom) AS latitude, ST_X(l.geom) AS longitude
                    FROM public.localites l
                    JOIN public.territoires t ON t.id = %s
                    WHERE l.geom IS NOT NULL AND ST_Within(l.geom, t.geom)
                    ORDER BY l.nom
                    """,
                    (db_id,),
                )
            rows = [dict(r) for r in cur.fetchall()]

    items = [
        {
            "id": r["id"],
            "name": r.get("nom"),
            "type": _nr(r.get("type")),
            "code": r.get("code"),
            "parent": _nr(r.get("parent_name"), "Non renseigné"),
            "parent_level": r.get("parent_level"),
            "coordinates": {"latitude": r.get("latitude"), "longitude": r.get("longitude")},
            "source": f"public.{level}",
            "confidence": "high",
            "attachment_quality": "spatial" if level == "localites" else "hierarchy_or_spatial",
        }
        for r in rows
    ]
    return explain_payload(
        domain="admin" if level == "collectivites" else level,
        count=len(items),
        status=ST_PARTIAL if level == "localites" else ST_OPERATIONAL,
        source=f"public.{level}",
        confidence="high",
        headline=f"{DOMAIN_LABELS.get(level, level)} — {len(items)}",
        business_impact=f"{len(items)} entité(s) administrative(s) de niveau « {DOMAIN_LABELS.get(level, level)} » rattachée(s) au territoire.",
        recommendation="Voir les entités administratives et vérifier les rattachements.",
        breakdown=[],
        top_items=items[offset : offset + page_size],
        pagination={"page": page, "page_size": page_size, "total": len(items)},
        technical={
            "attachment": "ST_Within prioritaire pour localités ; hiérarchie FK + spatial pour groupements",
            "note_metier": "Les détails FK/ST_Within restent dans Détail technique.",
        },
        actions=[
            {"id": "details", "label": "Voir les entités administratives"},
            {"id": "map", "label": "Afficher sur la carte"},
        ],
    )


def build_domain_explain(
    territory_ref: str,
    domain: str,
    *,
    page: int = 1,
    page_size: int = 50,
    program: str | None = None,
    level: str | None = None,
) -> dict[str, Any] | None:
    domain = (domain or "").lower()
    if domain in {"telecom", "telecommunications", "télécom"}:
        return build_telecom_explain(territory_ref, page=page, page_size=page_size)
    if domain in {"fiber", "fibre"}:
        return build_fiber_explain(territory_ref, page=page, page_size=page_size)
    if domain in {"health", "sante", "santé"}:
        return build_health_explain(territory_ref, page=page, page_size=page_size)
    if domain in {"routes", "transport"}:
        return build_routes_explain(territory_ref, page=page, page_size=page_size)
    if domain in {"programs", "sites", "sites_20476", "sites_300", "sites_40", "ccn"}:
        prog = program or (domain if domain.startswith("sites_") or domain == "ccn" else "sites_20476")
        return build_programs_explain(territory_ref, program=prog, page=page, page_size=page_size)
    if domain in {"admin", "administratif", "localites", "groupements", "collectivites"}:
        return build_admin_explain(territory_ref, level=level or (domain if domain != "admin" else "localites"), page=page, page_size=page_size)
    return None


def build_explainability_bundle(territory_ref: str) -> dict[str, Any] | None:
    """Synthèses décideur pour tous les domaines (sans listes complètes)."""
    entity = resolve_territory(territory_ref)
    if not entity:
        return None

    def light(domain: str, **kw: Any) -> dict[str, Any] | None:
        payload = build_domain_explain(territory_ref, domain, page=1, page_size=5, **kw)
        if not payload:
            return None
        # keep top 5 only for bundle
        return payload

    bundle = {
        "_meta": {"engine": ENGINE, "generated_at": _now(), "territory": entity.get("name")},
        "telecom": light("telecom"),
        "fiber": light("fiber"),
        "health": light("health"),
        "routes": light("routes"),
        "sites_20476": light("sites_20476", program="sites_20476"),
        "sites_300": light("sites_300", program="sites_300"),
        "sites_40": light("sites_40", program="sites_40"),
        "ccn": light("ccn", program="ccn"),
        "localites": light("localites", level="localites"),
        "groupements": light("groupements", level="groupements"),
        "collectivites": light("collectivites", level="collectivites"),
    }
    return bundle
