"""Territorial Intelligence Explorer v1 — consolidation de connaissance territoriale.

Répond à : « Que sait le FDSU d’un territoire, quels besoins numériques,
quelles interventions prioriser ? »

Ne duplique pas les sources : consolide Référentiel National, Knowledge Hub,
programmes, santé, télécom, CCN, priorisation et Explainable Decision Engine.
N’invente aucune valeur — statut explicite si indisponible.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
NOMENCLATURE_PATH = PROJECT_ROOT / "data" / "reports" / "fdsu_nomenclature.json"
HIERARCHY_PATH = PROJECT_ROOT / "data" / "reports" / "territory_hierarchy" / "territoires_hierarchie_kmz.report.json"
PROGRAMS_DIR = PROJECT_ROOT / "data" / "programs"

ENGINE_VERSION = "territorial-intelligence-1.0.0"
DEMO_FOCUS_NAME = "DUNGU"  # cas de démo UI uniquement — pas de logique métier dédiée

STATUS_CONFIRMED = "confirmed"
STATUS_ESTIMATED = "estimated"
STATUS_PARTIAL = "partial"
STATUS_UNAVAILABLE = "unavailable"
STATUS_NOT_SOURCED = "not_sourced"
STATUS_DEMONSTRATION = "demonstration"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_json(path: Path) -> Any:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def field(
    value: Any,
    status: str,
    *,
    source: str | None = None,
    note: str | None = None,
) -> dict[str, Any]:
    return {
        "value": value,
        "status": status,
        "source": source,
        "note": note,
        "available": status in {STATUS_CONFIRMED, STATUS_ESTIMATED, STATUS_PARTIAL, STATUS_DEMONSTRATION}
        and value is not None,
    }


def unavailable(note: str = "Non disponible dans les sources actuelles", source: str | None = None) -> dict[str, Any]:
    return field(None, STATUS_UNAVAILABLE, source=source, note=note)


def not_sourced(note: str = "Non sourcé", source: str | None = None) -> dict[str, Any]:
    return field(None, STATUS_NOT_SOURCED, source=source, note=note)


def _norm(text: str | None) -> str:
    return " ".join(str(text or "").strip().upper().replace("-", " ").split())


def _names_match(a: str | None, b: str | None) -> bool:
    na, nb = _norm(a), _norm(b)
    return bool(na and nb and (na == nb or na in nb or nb in na))


def _nomenclature_territories() -> list[dict[str, Any]]:
    payload = _load_json(NOMENCLATURE_PATH)
    return list(payload.get("territoires") or payload.get("territories") or [])


def _master_territories() -> list[dict[str, Any]]:
    from api.services import master_registry_service

    result = master_registry_service.list_entities(entity_type="TERRITOIRE", limit=5000)
    return list(result.get("entities") or [])


def _resolve_territory_ref(territory_id: str) -> dict[str, Any] | None:
    needle = str(territory_id or "").strip()
    if not needle:
        return None

    for entity in _master_territories():
        attrs = entity.get("attributes") or {}
        candidates = {
            str(entity.get("business_id") or ""),
            str(entity.get("uuid") or ""),
            str(entity.get("name") or ""),
            f"{attrs.get('province_code')}-{attrs.get('territoire_code')}",
            str(attrs.get("territoire_code") or ""),
        }
        if needle in candidates or _names_match(needle, entity.get("name")):
            return {
                "territory_id": entity.get("business_id"),
                "territory_name": entity.get("name"),
                "province": attrs.get("province_name"),
                "province_code": attrs.get("province_code"),
                "administrative_code": attrs.get("territoire_code"),
                "fdsu_zone": attrs.get("zone_fdsu"),
                "nb_sites_reference": attrs.get("nb_sites_reference"),
                "source": "master_registry",
                "master": entity,
            }

    for item in _nomenclature_territories():
        name = item.get("nom") or item.get("name")
        code = str(item.get("territoire_code") or item.get("code") or "")
        prov_code = str(item.get("province_code") or "")
        business_id = f"TERRITOIRE-{prov_code}-{code}" if prov_code and code else None
        if (
            needle == business_id
            or needle == code
            or needle == f"{prov_code}-{code}"
            or _names_match(needle, name)
        ):
            return {
                "territory_id": business_id or code or name,
                "territory_name": name,
                "province": item.get("province"),
                "province_code": prov_code,
                "administrative_code": code,
                "fdsu_zone": item.get("zone_fdsu"),
                "nb_sites_reference": item.get("nb_sites_reference"),
                "source": "fdsu_nomenclature",
                "nomenclature": item,
            }
    return None


def list_territories(
    *,
    province: str | None = None,
    zone: str | None = None,
    priority_level: str | None = None,
    data_quality: str | None = None,
    q: str | None = None,
    limit: int = 500,
) -> dict[str, Any]:
    items = []
    for entity in _master_territories():
        attrs = entity.get("attributes") or {}
        row = {
            "territory_id": entity.get("business_id"),
            "territory_name": entity.get("name"),
            "province": attrs.get("province_name"),
            "province_code": attrs.get("province_code"),
            "administrative_code": attrs.get("territoire_code"),
            "fdsu_zone": attrs.get("zone_fdsu"),
            "nb_sites_reference": attrs.get("nb_sites_reference"),
            "confidence_level": entity.get("confidence_level"),
            "data_quality": "partial",
            "is_demo_focus": _norm(entity.get("name")) == DEMO_FOCUS_NAME,
        }
        if province and not _names_match(province, row["province"]):
            continue
        if zone and str(row.get("fdsu_zone") or "").upper() != zone.upper():
            continue
        if q and q.lower() not in f"{row['territory_name']} {row['province']} {row['territory_id']}".lower():
            continue
        if data_quality and row["data_quality"] != data_quality:
            continue
        items.append(row)

    # priority_level filter applied after light scoring if requested
    if priority_level:
        filtered = []
        for item in items:
            profile = build_territorial_profile(item["territory_id"], light=True)
            level = ((profile or {}).get("priority") or {}).get("level", {}).get("value")
            if level == priority_level:
                filtered.append(item)
        items = filtered

    items.sort(key=lambda r: (str(r.get("province") or ""), str(r.get("territory_name") or "")))
    page = items[:limit]
    return {
        "_meta": {
            "title": "Territoires — Territorial Intelligence Explorer",
            "count": len(page),
            "total": len(items),
            "engine_version": ENGINE_VERSION,
            "demo_focus": DEMO_FOCUS_NAME,
            "note": "Liste issue du Référentiel National (TERRITOIRE). Aucune valeur inventée.",
        },
        "territories": page,
    }


def _program_sites(program_code: str, territory_name: str) -> list[dict[str, Any]]:
    path = PROGRAMS_DIR / program_code / f"{program_code}.json"
    payload = _load_json(path)
    sites = payload.get("sites") if isinstance(payload, dict) else payload
    if not isinstance(sites, list):
        return []
    return [s for s in sites if _names_match(s.get("territoire"), territory_name)]


def _hierarchy_feature(territory_name: str, province: str | None = None) -> dict[str, Any] | None:
    payload = _load_json(HIERARCHY_PATH)
    territories = payload.get("territories") or []
    for item in territories:
        attrs = (item.get("attributs") or {}).get("extended_data") or {}
        if attrs.get("TYPE") and str(attrs.get("TYPE")).lower() != "territoire":
            # some entries may not have TYPE; still match by name
            pass
        name = item.get("nom") or item.get("name")
        item_province = item.get("province")
        if _names_match(name, territory_name) and (not province or _names_match(item_province, province) or not item_province):
            return item
    return None


def _safe_health(territory_name: str, province: str | None) -> dict[str, Any]:
    try:
        from api.services import health_service

        facilities = health_service.list_facilities(
            province_name=province,
            territory_name=territory_name,
            limit=500,
        )
        if isinstance(facilities, list):
            rows = facilities
        elif isinstance(facilities, dict):
            rows = facilities.get("facilities") or facilities.get("items") or []
        else:
            rows = []
        return {
            "count": len(rows),
            "items": rows[:50],
            "status": STATUS_CONFIRMED if rows else STATUS_PARTIAL,
            "source": "/api/health",
            "note": None if rows else "Aucun établissement de santé trouvé pour ce filtre territoire/province.",
        }
    except Exception as exc:  # noqa: BLE001 — consolidation tolérante
        return {"count": 0, "items": [], "status": STATUS_UNAVAILABLE, "source": "/api/health", "note": str(exc)}


def _safe_telecom(territory_name: str, province: str | None) -> dict[str, Any]:
    try:
        from api.services import telecom_service

        objects = telecom_service.list_infrastructure(limit=20000)
        filtered = [
            o
            for o in (objects or [])
            if _names_match(o.get("territoire") or o.get("territory"), territory_name)
            or (
                province
                and _names_match(o.get("province"), province)
                and _names_match(o.get("territoire") or o.get("territory"), territory_name)
            )
        ]
        # Prefer strict territory match
        strict = [o for o in (objects or []) if _names_match(o.get("territoire"), territory_name)]
        rows = strict or filtered
        if rows:
            return {
                "count": len(rows),
                "items": rows[:50],
                "status": STATUS_PARTIAL,
                "source": "/api/telecom/infrastructure",
            }
        return {
            "count": 0,
            "items": [],
            "status": STATUS_NOT_SOURCED,
            "source": "/api/telecom/infrastructure",
            "note": "Aucune infrastructure télécom rattachée explicitement à ce territoire.",
        }
    except Exception as exc:  # noqa: BLE001
        return {"count": None, "items": [], "status": STATUS_UNAVAILABLE, "source": "/api/telecom", "note": str(exc)}


def _safe_ccn(territory_name: str, province: str | None) -> dict[str, Any]:
    try:
        from api.services import ccn_operational_service

        listed = ccn_operational_service.list_ccn(territoire=territory_name, province=province, limit=200)
        items = listed.get("ccn") or []
        # also try name-only if empty
        if not items:
            listed = ccn_operational_service.list_ccn(territoire=territory_name, limit=200)
            items = listed.get("ccn") or []
        return {
            "count": len(items),
            "items": items,
            "status": STATUS_DEMONSTRATION if items else STATUS_UNAVAILABLE,
            "source": "/api/ccn",
            "data_class": listed.get("_meta", {}).get("data_class"),
            "note": None if items else "Aucun CCN DEMO associé à ce territoire dans le jeu actuel.",
        }
    except Exception as exc:  # noqa: BLE001
        return {"count": 0, "items": [], "status": STATUS_UNAVAILABLE, "source": "/api/ccn", "note": str(exc)}


def _score_sites(sites: list[dict[str, Any]]) -> list[dict[str, Any]]:
    from api.services import fdsu_site_priority_service

    scored = []
    for site in sites:
        try:
            scored.append(fdsu_site_priority_service.compute_national_site_score(site))
        except Exception:  # noqa: BLE001
            continue
    scored.sort(key=lambda s: (-float(s.get("priority_score") or 0), str(s.get("site_name") or "")))
    return scored


def build_territorial_profile(territory_id: str, *, light: bool = False) -> dict[str, Any] | None:
    ref = _resolve_territory_ref(territory_id)
    if not ref:
        return None

    name = ref["territory_name"]
    province = ref.get("province")
    zone = ref.get("fdsu_zone")

    sites_40 = _program_sites("sites_40", name)
    sites_300 = _program_sites("sites_300", name)
    sites_20476 = _program_sites("sites_20476", name)
    all_program_sites = sites_20476 or sites_300 or sites_40

    populations = [int(s["population"]) for s in all_program_sites if s.get("population") not in (None, "")]
    distances = [float(s["distance"]) for s in all_program_sites if s.get("distance") not in (None, "")]

    population_field = (
        field(sum(populations), STATUS_PARTIAL, source="programmes sites (somme populations sites)", note="Somme des populations des sites programme — pas un recensement territorial officiel.")
        if populations
        else unavailable("Population territoriale officielle non sourcée")
    )
    area_field = unavailable("Superficie (km²) non sourcée dans les référentiels actuels")
    density_field = unavailable("Densité non calculable sans superficie sourcée")

    hierarchy = _hierarchy_feature(name, province)
    localities_count = unavailable("Nombre de localités non consolidé")
    groupements_count = unavailable("Nombre de groupements non consolidé")
    if hierarchy:
        # Prefer explicit counts if present; otherwise leave unavailable
        for key, target in (("nb_localites", "localities"), ("nb_groupements", "groupements")):
            val = hierarchy.get(key) or (hierarchy.get("attributs") or {}).get(key)
            if val is not None:
                if target == "localities":
                    localities_count = field(val, STATUS_PARTIAL, source="territory_hierarchy")
                else:
                    groupements_count = field(val, STATUS_PARTIAL, source="territory_hierarchy")

    health = {"count": 0, "items": [], "status": STATUS_UNAVAILABLE}
    telecom = {"count": None, "items": [], "status": STATUS_NOT_SOURCED}
    ccn = {"count": 0, "items": [], "status": STATUS_UNAVAILABLE}
    scored_sites: list[dict[str, Any]] = []

    if not light:
        health = _safe_health(name, province)
        telecom = _safe_telecom(name, province)
        ccn = _safe_ccn(name, province)
        scored_sites = _score_sites(all_program_sites[:200])

    avg_score = None
    top_level = None
    if scored_sites:
        avg_score = round(sum(float(s["priority_score"]) for s in scored_sites) / len(scored_sites), 1)
        top_level = scored_sites[0].get("priority_level")

    missing = []
    if population_field["status"] == STATUS_UNAVAILABLE:
        missing.append("population_officielle")
    if area_field["status"] == STATUS_UNAVAILABLE:
        missing.append("area_km2")
    if health["status"] in {STATUS_UNAVAILABLE, STATUS_NOT_SOURCED} or health.get("count") == 0:
        missing.append("services_sante_complets")
    if telecom["status"] in {STATUS_UNAVAILABLE, STATUS_NOT_SOURCED}:
        missing.append("telecom_territorial")
    if ccn.get("count") == 0:
        missing.append("ccn")

    confidence = "medium"
    if len(missing) >= 4:
        confidence = "low"
    elif scored_sites and population_field["available"]:
        confidence = "medium"
    if scored_sites and health.get("count"):
        confidence = "high" if len(missing) <= 2 else "medium"

    profile = {
        "territory_id": ref["territory_id"],
        "territory_name": name,
        "province": province,
        "fdsu_zone": zone,
        "administrative_code": ref.get("administrative_code"),
        "province_code": ref.get("province_code"),
        "population": population_field,
        "area_km2": area_field,
        "density": density_field,
        "localities_count": localities_count,
        "groupements_count": groupements_count,
        "data_quality": "partial" if missing else "good",
        "confidence_level": confidence,
        "last_updated": _now(),
        "sources": [
            "data/master/registry.json",
            "data/reports/fdsu_nomenclature.json",
            "data/programs/sites_*/",
            "/api/health",
            "/api/telecom",
            "/api/ccn",
            "/api/knowledge",
            "/api/decision",
        ],
        "is_demo_focus": _norm(name) == DEMO_FOCUS_NAME,
        "engine_version": ENGINE_VERSION,
    }

    if light:
        profile["priority"] = {
            "score": field(avg_score, STATUS_ESTIMATED if avg_score is not None else STATUS_UNAVAILABLE, source="agrégation scores sites"),
            "level": field(top_level, STATUS_ESTIMATED if top_level else STATUS_UNAVAILABLE, source="top site scoré"),
        }
        return profile

    # Full portrait sections
    synthesis = {
        "province": field(province, STATUS_CONFIRMED, source="master_registry / nomenclature"),
        "fdsu_zone": field(zone, STATUS_CONFIRMED, source="nomenclature FDSU"),
        "population": population_field,
        "area_km2": area_field,
        "density": density_field,
        "localities": localities_count,
        "groupements": groupements_count,
        "administrative_code": field(ref.get("administrative_code"), STATUS_CONFIRMED, source="nomenclature"),
        "nb_sites_reference_nomenclature": field(
            ref.get("nb_sites_reference"),
            STATUS_CONFIRMED if ref.get("nb_sites_reference") is not None else STATUS_UNAVAILABLE,
            source="fdsu_nomenclature",
            note="Référence nomenclature (peut différer du stock programme national).",
        ),
    }

    digital = {
        "operateurs_presents": not_sourced("Ventilation opérateurs par territoire non disponible"),
        "infrastructures_telecom": field(
            telecom.get("count"),
            telecom.get("status", STATUS_NOT_SOURCED),
            source=telecom.get("source"),
            note=telecom.get("note"),
        ),
        "fibre": not_sourced("Couche fibre non filtrée par territoire"),
        "backbone": not_sourced("Backbone non sourcé au niveau territoire"),
        "couverture_disponible": not_sourced("Indicateur de couverture territoriale non valorisé (NIF structure_only)"),
        "distance_moyenne_sites": field(
            round(sum(distances) / len(distances), 1) if distances else None,
            STATUS_PARTIAL if distances else STATUS_UNAVAILABLE,
            source="programmes sites.distance",
            note="Moyenne des distances renseignées sur les sites programme du territoire.",
        ),
        "zones_peu_desservies": field(
            sum(1 for s in all_program_sites if str(s.get("distance_level") or "").lower() in {"far", "éloigné", "eloigne", "high"}),
            STATUS_PARTIAL if all_program_sites else STATUS_UNAVAILABLE,
            source="sites.distance_level",
        ),
        "sites_fdsu_presents": {
            "sites_40": field(len(sites_40), STATUS_CONFIRMED, source="data/programs/sites_40"),
            "sites_300": field(len(sites_300), STATUS_CONFIRMED, source="data/programs/sites_300"),
            "sites_20476": field(len(sites_20476), STATUS_CONFIRMED, source="data/programs/sites_20476"),
        },
        "ccn_presents_ou_proposes": field(
            ccn.get("count"),
            ccn.get("status", STATUS_UNAVAILABLE),
            source=ccn.get("source"),
            note=ccn.get("note"),
        ),
    }

    public_services = {
        "etablissements_sante": field(
            health.get("count"),
            health.get("status", STATUS_UNAVAILABLE),
            source=health.get("source"),
            note=health.get("note"),
        ),
        "ecoles": not_sourced("Référentiel écoles non branché"),
        "administrations": not_sourced("Référentiel administrations non branché"),
        "marches": not_sourced("Référentiel marchés non branché"),
        "health_sample": health.get("items") or [],
    }

    economy = {
        "agriculture": not_sourced(),
        "elevage": not_sourced(),
        "peche": not_sourced(),
        "commerce": not_sourced(),
        "mines": not_sourced(),
        "tourisme": not_sourced(),
        "autres": not_sourced("Profils socio-économiques CNCT non renseignés pour ce territoire"),
    }

    accessibility = {
        "routes": not_sourced(),
        "pistes": not_sourced(),
        "ports": not_sourced(),
        "aerodromes": field(
            any("airport" in str(s.get("nearest_site") or "").lower() or "aerodrome" in str(s.get("site_name") or "").lower() for s in all_program_sites),
            STATUS_PARTIAL if all_program_sites else STATUS_NOT_SOURCED,
            source="indices sites (nearest_site / site_name)",
            note="Signal faible dérivé des libellés sites — à confirmer.",
        ),
        "contraintes_acces": not_sourced(),
        "enclavement": not_sourced(),
    }

    energy = {
        "reseau": not_sourced(),
        "solaire": not_sourced(),
        "groupes_electrogenes": not_sourced(),
        "disponibilite": not_sourced("Domaine énergie non valorisé"),
    }

    programs = {
        "sites_40": field(len(sites_40), STATUS_CONFIRMED, source="programmes"),
        "sites_300": field(len(sites_300), STATUS_CONFIRMED, source="programmes"),
        "sites_20476": field(len(sites_20476), STATUS_CONFIRMED, source="programmes"),
        "ccn": field(ccn.get("count"), ccn.get("status", STATUS_UNAVAILABLE), source="/api/ccn", note=ccn.get("note")),
        "autres": not_sourced(),
    }

    top_factors = []
    if scored_sites:
        details = (scored_sites[0].get("criteria_details") or {}).get("top_factors") or []
        top_factors = details

    priority = {
        "score": field(
            avg_score,
            STATUS_ESTIMATED if avg_score is not None else STATUS_UNAVAILABLE,
            source="moyenne scores sites (Doctrine Sites / matrice nationale)",
            note="Score territorial estimé par agrégation des sites scorés — pas un score officiel territoire.",
        ),
        "level": field(
            top_level,
            STATUS_ESTIMATED if top_level else STATUS_UNAVAILABLE,
            source="niveau du site le plus prioritaire",
        ),
        "sites_scored": field(len(scored_sites), STATUS_CONFIRMED if scored_sites else STATUS_UNAVAILABLE, source="priorisation nationale"),
        "top_site": scored_sites[0] if scored_sites else None,
        "main_factors": top_factors,
        "missing_criteria": missing,
        "confidence_level": confidence,
    }

    from api.services import knowledge_hub_service

    kh_domain = knowledge_hub_service.get_domain("territory")
    nif = knowledge_hub_service.list_indicators(domain_id="territory")

    return {
        "_meta": {
            "title": f"Profil Territorial FDSU — {name}",
            "engine_version": ENGINE_VERSION,
            "principle": "Consolider sans inventer",
            "generated_at": _now(),
        },
        "profile": profile,
        "sections": {
            "synthesis": synthesis,
            "digital": digital,
            "public_services": public_services,
            "economy": economy,
            "accessibility": accessibility,
            "energy": energy,
            "programs": programs,
            "priority": priority,
            "opportunities": _build_opportunities(scored_sites, health, ccn, sites_300),
            "risks": _build_risks(missing, confidence, distances),
        },
        "assets": {
            "sites_sample": all_program_sites[:20],
            "sites_scored_top": scored_sites[:10],
            "ccn": ccn.get("items") or [],
            "health_sample": health.get("items") or [],
        },
        "knowledge_hub": {
            "domain": (kh_domain or {}).get("domain"),
            "indicators_count": (nif or {}).get("_meta", {}).get("count"),
        },
        "data_gaps": missing,
    }


def _build_opportunities(scored_sites, health, ccn, sites_300) -> dict[str, Any]:
    items = []
    if sites_300:
        items.append({"id": "wave_300", "label": "Présence dans la vague 300", "status": STATUS_CONFIRMED, "source": "sites_300"})
    if scored_sites:
        items.append({"id": "priority_sites", "label": f"{len(scored_sites)} sites scorés disponibles pour arbitrage", "status": STATUS_CONFIRMED, "source": "priorisation"})
    if health.get("count"):
        items.append({"id": "health_anchor", "label": "Ancrage services de santé documenté", "status": STATUS_CONFIRMED, "source": "/api/health"})
    if ccn.get("count"):
        items.append({"id": "ccn_demo", "label": "CCN DEMO présents", "status": STATUS_DEMONSTRATION, "source": "/api/ccn"})
    if not items:
        items.append({"id": "collect_data", "label": "Opportunité principale : compléter la connaissance territoriale", "status": STATUS_NOT_SOURCED})
    return {"items": items}


def _build_risks(missing: list[str], confidence: str, distances: list[float]) -> dict[str, Any]:
    risks = []
    if "telecom_territorial" in missing:
        risks.append({"type": "data", "label": "Télécom non ventilé par territoire", "severity": "confidence"})
    if "area_km2" in missing:
        risks.append({"type": "data", "label": "Superficie absente — densité indisponible", "severity": "analysis"})
    if "ccn" in missing:
        risks.append({"type": "program", "label": "Aucun CCN associé dans les sources actuelles", "severity": "planning"})
    if confidence == "low":
        risks.append({"type": "confidence", "label": "Faible confiance globale du profil", "severity": "flag"})
    if distances and (sum(distances) / len(distances)) > 10000:
        risks.append({"type": "access", "label": "Distance moyenne élevée aux sites de référence", "severity": "partial", "status": STATUS_PARTIAL})
    risks.append({"type": "security", "label": "Contraintes sécuritaires", "status": STATUS_NOT_SOURCED, "note": "Non sourcé pour ce territoire"})
    return {"items": risks}


def build_map_payload(territory_id: str) -> dict[str, Any] | None:
    profile = build_territorial_profile(territory_id)
    if not profile:
        return None
    name = profile["profile"]["territory_name"]
    province = profile["profile"]["province"]
    features = []

    hierarchy = _hierarchy_feature(name, province)
    if hierarchy and hierarchy.get("geometry"):
        features.append(
            {
                "type": "Feature",
                "geometry": hierarchy["geometry"],
                "properties": {
                    "kind": "territory_boundary",
                    "name": name,
                    "territory_id": profile["profile"]["territory_id"],
                },
            }
        )

    for site in profile["assets"]["sites_sample"]:
        if site.get("latitude") is None or site.get("longitude") is None:
            continue
        features.append(
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [site["longitude"], site["latitude"]]},
                "properties": {
                    "kind": "site_fdsu",
                    "id": site.get("site_id"),
                    "code": site.get("site_code"),
                    "name": site.get("site_name"),
                    "program_code": site.get("program_code"),
                },
            }
        )

    for ccn in profile["assets"]["ccn"]:
        if ccn.get("latitude") is None or ccn.get("longitude") is None:
            continue
        features.append(
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [ccn["longitude"], ccn["latitude"]]},
                "properties": {
                    "kind": "ccn",
                    "id": ccn.get("id"),
                    "name": ccn.get("name"),
                    "data_class": "demonstration",
                },
            }
        )

    for facility in profile["assets"]["health_sample"]:
        lat = facility.get("latitude") or facility.get("lat")
        lon = facility.get("longitude") or facility.get("lon")
        if lat is None or lon is None:
            continue
        features.append(
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [lon, lat]},
                "properties": {
                    "kind": "health",
                    "id": facility.get("id"),
                    "name": facility.get("name") or facility.get("facility_name"),
                },
            }
        )

    return {
        "_meta": {
            "title": f"Carte territoriale — {name}",
            "feature_count": len(features),
            "engine_version": ENGINE_VERSION,
        },
        "territory_id": profile["profile"]["territory_id"],
        "legend": [
            {"kind": "territory_boundary", "label": "Limite territoriale"},
            {"kind": "site_fdsu", "label": "Sites FDSU"},
            {"kind": "ccn", "label": "CCN"},
            {"kind": "health", "label": "Santé"},
        ],
        "geojson": {"type": "FeatureCollection", "features": features},
    }


def build_indicators(territory_id: str) -> dict[str, Any] | None:
    profile = build_territorial_profile(territory_id)
    if not profile:
        return None
    from api.services import knowledge_hub_service

    nif = knowledge_hub_service.list_indicators()
    return {
        "_meta": {
            "title": "Indicateurs territoriaux",
            "values_policy": "Pas de valeur inventée — NIF structure_only + champs profil",
        },
        "territory_id": profile["profile"]["territory_id"],
        "profile_fields": {
            "population": profile["profile"]["population"],
            "area_km2": profile["profile"]["area_km2"],
            "sites_20476": profile["sections"]["programs"]["sites_20476"],
            "health": profile["sections"]["public_services"]["etablissements_sante"],
            "priority_score": profile["sections"]["priority"]["score"],
        },
        "nif": nif.get("indicators") or [],
        "data_gaps": profile.get("data_gaps") or [],
    }


def build_recommendations(territory_id: str) -> dict[str, Any] | None:
    profile = build_territorial_profile(territory_id)
    if not profile:
        return None

    from api.services import explainable_decision_service

    doctrine_sites = explainable_decision_service.get_doctrine_payload("DOCTRINE_SITES_FDSU")
    doctrine_ccn = explainable_decision_service.get_doctrine_payload("DOCTRINE_CCN_FDSU")
    gaps = profile.get("data_gaps") or []
    top_sites = profile["assets"]["sites_scored_top"][:3]
    recommendations = []

    for site in top_sites:
        case = None
        try:
            case = explainable_decision_service.build_site_case(str(site.get("site_id")), program_code=site.get("program_code"))
        except Exception:  # noqa: BLE001
            case = None
        recommendations.append(
            {
                "id": f"site-{site.get('site_id')}",
                "type": "site",
                "action": "Prioriser le site pour arbitrage FDSU",
                "target": {
                    "site_id": site.get("site_id"),
                    "site_code": site.get("site_code"),
                    "site_name": site.get("site_name"),
                    "score": site.get("priority_score"),
                    "level": site.get("priority_level"),
                },
                "why": (
                    f"Score site {site.get('priority_score')}/100 ({site.get('priority_level_label')}) "
                    f"selon Doctrine Sites v{(doctrine_sites or {}).get('doctrine', {}).get('_meta', {}).get('version')}."
                ),
                "doctrine": {
                    "id": "DOCTRINE_SITES_FDSU",
                    "version": (doctrine_sites or {}).get("doctrine", {}).get("_meta", {}).get("version"),
                },
                "indicators": ["population", "deficit_distance", "wave_calibration"],
                "missing_data": gaps,
                "confidence_level": profile["profile"]["confidence_level"],
                "case_ref": case.get("case_id") if case else None,
            }
        )

    if "ccn" in gaps:
        recommendations.append(
            {
                "id": "ccn-study",
                "type": "ccn",
                "action": "Étudier l’opportunité d’un CCN (pas de CCN sourcé actuellement)",
                "why": (
                    "Aucun CCN associé dans les sources actuelles. "
                    f"Doctrine CCN v{(doctrine_ccn or {}).get('doctrine', {}).get('_meta', {}).get('version')} "
                    "exige critères versionnés avant recommandation d’implantation."
                ),
                "doctrine": {
                    "id": "DOCTRINE_CCN_FDSU",
                    "version": (doctrine_ccn or {}).get("doctrine", {}).get("_meta", {}).get("version"),
                },
                "indicators": ["MEAS_SCHOOL", "MEAS_HOSPITAL", "MEAS_ADMIN", "CRIT_CONN_EXTENSION"],
                "missing_data": ["ccn", "typologie_besoins_locale"],
                "confidence_level": "low",
                "fdsu_action": "étude terrain + collecte indicateurs doctrine CCN",
            }
        )

    if "telecom_territorial" in gaps:
        recommendations.append(
            {
                "id": "telecom-collect",
                "type": "extension_reseau",
                "action": "Collecter / ventiler les données télécom au niveau territoire",
                "why": "Le référentiel télécom n’expose pas encore une ventilation fiable par territoire.",
                "doctrine": {"id": "DOCTRINE_SITES_FDSU", "rule": "RULE_DATA_CONFIDENCE"},
                "indicators": ["IND_CONN_COVERAGE_GAP"],
                "missing_data": ["telecom_territorial"],
                "confidence_level": "low",
                "fdsu_action": "collecte de données",
            }
        )

    recommendations.append(
        {
            "id": "data-collect",
            "type": "collecte_donnees",
            "action": "Compléter superficie, écoles, administrations, énergie",
            "why": "Plusieurs domaines du portrait restent not_sourced / unavailable — la décision territoriale reste partielle.",
            "doctrine": {"id": "Knowledge Hub", "note": "NIF structure_only"},
            "indicators": list(gaps),
            "missing_data": gaps,
            "confidence_level": profile["profile"]["confidence_level"],
            "fdsu_action": "collecte de données / étude terrain",
        }
    )

    # Guarantee: every recommendation has why
    for rec in recommendations:
        if not rec.get("why"):
            rec["why"] = "Justification manquante — recommandation non affichable sans explication."
            rec["confidence_level"] = "low"

    return {
        "_meta": {
            "title": "Recommandations territoriales explicables",
            "principle": "Aucune recommandation sans justification",
            "count": len(recommendations),
            "engine_version": ENGINE_VERSION,
        },
        "territory_id": profile["profile"]["territory_id"],
        "confidence_level": profile["profile"]["confidence_level"],
        "recommendations": recommendations,
    }


def explain_territory(territory_id: str) -> dict[str, Any] | None:
    profile = build_territorial_profile(territory_id)
    recs = build_recommendations(territory_id)
    if not profile or not recs:
        return None

    from api.services import explainable_decision_service

    doctrine_sites = explainable_decision_service.get_doctrine_payload("DOCTRINE_SITES_FDSU")
    return {
        "_meta": {
            "title": "Justification territoriale",
            "principle": "Aucune recommandation sans justification",
            "engine_version": ENGINE_VERSION,
        },
        "territory": {
            "id": profile["profile"]["territory_id"],
            "name": profile["profile"]["territory_name"],
            "province": profile["profile"]["province"],
            "zone": profile["profile"]["fdsu_zone"],
        },
        "priority": profile["sections"]["priority"],
        "doctrine": {
            "id": "DOCTRINE_SITES_FDSU",
            "version": (doctrine_sites or {}).get("doctrine", {}).get("_meta", {}).get("version"),
            "title": (doctrine_sites or {}).get("doctrine", {}).get("_meta", {}).get("title"),
            "references": (doctrine_sites or {}).get("doctrine", {}).get("_meta", {}).get("source_document"),
        },
        "matrix": "data/business/priority_matrix.json",
        "indicators_mobilized": [
            "population (sites)",
            "deficit_distance",
            "wave_calibration",
            "health facilities (si DB)",
        ],
        "rules_applied": ["agrégation scores sites", "Doctrine Sites", "signalement gaps Knowledge Hub"],
        "sources": profile["profile"]["sources"],
        "assumptions": [
            "Le score territorial est une agrégation des scores sites, pas un score officiel territoire.",
            "Les champs not_sourced / unavailable ne sont pas remplacés par des valeurs inventées.",
            "Les CCN DEMO restent explicitement marqués demonstration.",
        ],
        "missing_data": profile.get("data_gaps") or [],
        "confidence_level": profile["profile"]["confidence_level"],
        "recommendations": recs["recommendations"],
    }
