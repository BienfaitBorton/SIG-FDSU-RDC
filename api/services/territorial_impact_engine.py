"""Moteur d’Impact Territorial et d’Évolution de la Couverture — v1.0

Data First / No Black Box :
- Réutilise NCI + NSME (localités non couvertes dans le rayon).
- Aucune population inventée.
- Déduplication stricte par clé NCI (need_id).
- CCN ≠ couverture radio (bénéficiaires potentiels distincts).
- Réel / planifié / simulé clairement distingués.
"""

from __future__ import annotations

import math
import time
from datetime import datetime, timezone
from typing import Any

from api.config import DATA_MODE
from api.services import coverage_intelligence_service as nci
from api.services import spatial_matching_service as nsme

ENGINE_VERSION = "tie-1.0.0"
_CACHE: dict[str, Any] = {"ts": 0.0, "payloads": {}}
_CACHE_TTL_S = 300.0


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _norm(value: Any) -> str:
    return " ".join(str(value or "").strip().lower().replace("-", " ").split())


def _safe_int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6_371_000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * r * math.asin(min(1.0, math.sqrt(a)))


def population_key(locality: dict[str, Any] | None = None, *, need_id: str | None = None) -> str:
    """Clé stable anti double-comptage — priorise l’identifiant NCI."""
    if need_id:
        return f"nci:{need_id}"
    if not locality:
        return "unknown"
    lid = locality.get("id") or locality.get("need_id")
    if lid:
        return f"nci:{lid}"
    lat, lon = locality.get("latitude"), locality.get("longitude")
    name = _norm(locality.get("name") or locality.get("locality_name"))
    if lat is not None and lon is not None and name:
        return f"geo:{round(float(lat), 5)}:{round(float(lon), 5)}:{name}"
    if name:
        return f"name:{name}:{_norm(locality.get('territoire'))}:{_norm(locality.get('province'))}"
    return "unknown"


def resolve_locality_link(
    *,
    program_name: str | None = None,
    nci_row: dict[str, Any] | None = None,
    distance_m: float | None = None,
) -> dict[str, Any]:
    """Documente le rapprochement sans fusion abusive."""
    if nci_row and program_name and _norm(program_name) == _norm(nci_row.get("name")):
        return {
            "method": "exact_name_match",
            "confidence": "high",
            "source": "nci+program",
            "ambiguity": False,
            "note": "Nom NCI aligné sur l’identifiant programme.",
        }
    if nci_row and nci_row.get("id"):
        return {
            "method": "nsme_spatial_radius",
            "confidence": "high" if (distance_m is not None and distance_m < 5000) else "medium",
            "source": "data/coverage/localities_uncovered.jsonl",
            "ambiguity": False,
            "distance_m": distance_m,
            "note": "Appariement spatial NSME dans le rayon de service — pas une fusion nominale seule.",
        }
    return {
        "method": "unresolved",
        "confidence": "low",
        "source": None,
        "ambiguity": True,
        "note": "Aucun rapprochement fiable — population non fusionnée.",
    }


def classify_deployment_status(
    raw_status: Any,
    *,
    asset_type: str = "FDSU_SITE",
    program_code: str | None = None,
) -> dict[str, Any]:
    """Mappe via Program Lifecycle Engine — aucun faux « Réalisé/Opérationnel »."""
    from api.services import program_lifecycle_engine as ple

    if asset_type == "CCN":
        life = ple.resolve_asset_lifecycle(
            program_code=program_code or "ccn",
            raw_status=raw_status,
            asset_type="CCN",
            data_class="demonstration",
        )
        return {
            "status": "demo",
            "badge": "Donnée partielle",
            "mode": "demonstration",
            "note": "CCN de démonstration — bénéficiaires potentiels, pas une couverture radio.",
            "lifecycle": life,
        }
    text = _norm(raw_status)
    if "simul" in text:
        return {"status": "simulated", "badge": "Simulé", "mode": "simulation", "note": "Ordre hypothétique."}
    life = ple.resolve_asset_lifecycle(
        program_code=program_code,
        raw_status=raw_status,
        asset_type=asset_type,
    )
    acc = life.get("impact_accounting") or {}
    asset = life.get("asset_status") or {}
    return {
        "status": acc.get("mode") or "planned",
        "badge": (life.get("ui_badges") or {}).get("asset") or acc.get("badge") or "Planifié",
        "mode": acc.get("mode") or "planned",
        "note": asset.get("note") or acc.get("note"),
        "lifecycle": life,
        "counts_as_observed_coverage": bool(acc.get("counts_as_observed_coverage")),
    }


def _covered_localities(*, province: str | None = None, territoire: str | None = None) -> list[dict[str, Any]]:
    rows = nci._load_localities("covered")  # noqa: SLF001 — cache NCI partagé
    out = []
    for row in rows:
        if not row.get("coords_valid"):
            continue
        if province and _norm(row.get("province")) != _norm(province):
            continue
        if territoire and _norm(row.get("territoire")) != _norm(territoire):
            continue
        out.append(row)
    return out


def _localities_in_radius(
    asset: dict[str, Any],
    rows: list[dict[str, Any]],
    *,
    radius_m: float,
    limit: int = 200,
) -> list[dict[str, Any]]:
    lat, lon = asset.get("latitude"), asset.get("longitude")
    if lat is None or lon is None:
        return []
    hits = []
    try:
        lat0, lon0 = float(lat), float(lon)
    except (TypeError, ValueError):
        return []
    deg = max(0.15, (radius_m / 111_000.0) * 1.25)
    for row in rows:
        try:
            rlat, rlon = float(row["latitude"]), float(row["longitude"])
        except (TypeError, ValueError, KeyError):
            continue
        if abs(rlat - lat0) > deg or abs(rlon - lon0) > deg:
            continue
        dist = _haversine_m(lat0, lon0, rlat, rlon)
        if dist <= radius_m:
            hits.append({**row, "_distance_m": round(dist, 1)})
    hits.sort(key=lambda r: r.get("_distance_m") or 1e18)
    return hits[:limit]


def _dedup_population(rows: list[dict[str, Any]], *, pop_field: str = "population") -> dict[str, Any]:
    seen: set[str] = set()
    pop_raw = 0
    pop_dedup = 0
    duplicates = 0
    missing_pop = 0
    kept: list[dict[str, Any]] = []
    for row in rows:
        key = population_key(row, need_id=str(row.get("id") or row.get("need_id") or "") or None)
        p = _safe_int(row.get(pop_field) if pop_field in row else row.get("population_impacted"))
        if p is not None:
            pop_raw += p
        else:
            missing_pop += 1
        if key in seen or key == "unknown":
            duplicates += 1
            continue
        seen.add(key)
        if p is not None:
            pop_dedup += p
        kept.append(row)
    return {
        "population_brute": pop_raw,
        "population_dedupliquee": pop_dedup,
        "doublons_exclus": duplicates,
        "localites_sans_population": missing_pop,
        "localites_dedupliquees": len(kept),
        "method": "dedup_by_nci_id_then_geo_name",
        "confidence": "high" if missing_pop == 0 and duplicates >= 0 else "medium",
        "items": kept,
        "double_counting_guard": "nci_need_id_exclusive",
    }


def _phase_for_program(program_code: str | None) -> str:
    code = _norm(program_code or "").replace("prog_", "")
    if "40" in code and "20476" not in code and "300" not in code:
        return "Phase 0 — Sites 40"
    if "300" in code:
        return "Phase 1 — Sites 300"
    if "20476" in code or "20_476" in code:
        return "Programme national 20 476"
    if "ccn" in code:
        return "Programme National des CCN"
    return program_code or "Programme non classé"


def _resolve_site(asset_id: str | int, program_code: str | None = None) -> dict[str, Any] | None:
    aid = str(asset_id)
    sites: list[dict[str, Any]] = []
    if DATA_MODE == "db":
        if aid.isdigit():
            sites = nsme.list_fdsu_sites(asset_id=int(aid), program_code=program_code, limit=1)
        if not sites:
            sites = [
                s
                for s in nsme.list_fdsu_sites(program_code=program_code, limit=5000)
                if str(s.get("site_code")) == aid or str(s.get("id")) == aid or _norm(s.get("site_name")) == _norm(aid)
            ]
    if not sites:
        # Fallback fichiers programmes
        try:
            from api.services import fdsu_sites_import_service as imports

            for code in (program_code, "sites_40", "sites_300", "sites_20476"):
                if not code:
                    continue
                payload = imports.load_program_sites(str(code).replace("PROG_", "").lower())
                for s in payload.get("sites") or []:
                    if (
                        str(s.get("site_id") or s.get("id")) == aid
                        or str(s.get("site_code")) == aid
                        or _norm(s.get("site_name") or s.get("name")) == _norm(aid)
                    ):
                        sites.append(
                            {
                                "id": s.get("site_id") or s.get("id"),
                                "site_code": s.get("site_code") or str(s.get("site_id") or s.get("id")),
                                "site_name": s.get("site_name") or s.get("name"),
                                "province": s.get("province"),
                                "territoire": s.get("territoire"),
                                "zone": s.get("zone"),
                                "status": s.get("status"),
                                "latitude": s.get("latitude"),
                                "longitude": s.get("longitude"),
                                "program_code": s.get("program_code") or code,
                                "population": s.get("population"),
                            }
                        )
                        break
                if sites:
                    break
        except Exception:
            pass
    return sites[0] if sites else None


def build_site_impact_profile(
    asset_id: str | int,
    *,
    program_code: str | None = None,
    scenario_mode: str = "planned",
) -> dict[str, Any] | None:
    """Profil d’impact d’un site FDSU — populations / localités sans invention."""
    site = _resolve_site(asset_id, program_code)
    if not site:
        return None

    radius = float(nsme._radius_for_asset("fdsu_site"))  # noqa: SLF001
    matches = nsme.match_site_to_uncovered_localities(site, max_distance_m=radius)
    unc_dedup = _dedup_population(
        [
            {
                "id": m.get("need_id"),
                "need_id": m.get("need_id"),
                "name": (m.get("properties") or {}).get("locality_name"),
                "population": m.get("population_impacted"),
                "population_impacted": m.get("population_impacted"),
                "latitude": (m.get("properties") or {}).get("need_lat"),
                "longitude": (m.get("properties") or {}).get("need_lon"),
                "province": m.get("province"),
                "territoire": m.get("territoire"),
                "priority": m.get("priority_level"),
                "categorie": m.get("category"),
                "_distance_m": m.get("distance_m"),
                "confidence_level": m.get("confidence_level"),
                "coverage_status_before": "uncovered",
                "source": m.get("source_need"),
            }
            for m in matches
            if m.get("relation_type") == "SERVES_LOCALITY"
        ]
    )

    covered_near = _localities_in_radius(
        site,
        _covered_localities(province=site.get("province"), territoire=site.get("territoire")),
        radius_m=radius,
    )
    # Si peu de couvertes locales, élargir province
    if len(covered_near) < 1 and site.get("province"):
        covered_near = _localities_in_radius(site, _covered_localities(province=site.get("province")), radius_m=radius)
    cov_dedup = _dedup_population(covered_near)

    pop_uncovered = unc_dedup["population_dedupliquee"]
    pop_covered = cov_dedup["population_dedupliquee"]
    pop_total = pop_uncovered + pop_covered
    locs_uncovered = unc_dedup["localites_dedupliquees"]
    locs_covered = cov_dedup["localites_dedupliquees"]
    locs_total = locs_uncovered + locs_covered

    rate_before = round(100.0 * pop_covered / pop_total, 1) if pop_total > 0 else None
    # Après : estimation = toutes les NCI non couvertes du rayon passent couvertes SI mode planifié/simulé
    # Ne jamais forcer 100 % si populations manquantes ou localités hors jeu.
    missing = unc_dedup["localites_sans_population"] + cov_dedup["localites_sans_population"]
    if pop_total > 0 and missing == 0:
        pop_after_covered = pop_total
        rate_after = 100.0
        remaining_after = 0
        rate_note = "Toutes les localités NCI du rayon avec population connue sont incluses dans le dénominateur."
    elif pop_total > 0:
        pop_after_covered = pop_covered + pop_uncovered
        rate_after = round(100.0 * pop_after_covered / (pop_total + 0), 1)
        # Population inconnue hors total → pas 100 %
        rate_after = None if missing else rate_after
        remaining_after = None
        rate_note = (
            f"{missing} localité(s) sans population fiable — taux après non présenté comme couverture totale."
            if missing
            else "Estimation sur populations connues du rayon uniquement."
        )
        if missing:
            remaining_after = None
            # On ne peut pas affirmer 100 %
            rate_after = round(100.0 * pop_after_covered / pop_total, 1) if pop_total else None
            # Mais on documente que des populations manquent
            rate_note = (
                f"Taux sur populations connues uniquement ; {missing} localité(s) sans population "
                "— couverture totale non affirmée."
            )
            remaining_after = 0  # parmi le dénominateur connu
        else:
            remaining_after = 0
    else:
        pop_after_covered = None
        rate_after = None
        remaining_after = None
        rate_note = "Population rayon indisponible — aucun taux inventé."

    status_meta = classify_deployment_status(
        site.get("status"),
        program_code=site.get("program_code") or program_code,
    )
    if scenario_mode == "simulation":
        status_meta = {
            "status": "simulated",
            "badge": "Simulé",
            "mode": "simulation",
            "note": "Scénario d’ordonnancement — impact projeté.",
            "lifecycle": status_meta.get("lifecycle"),
        }
    elif scenario_mode == "real" and not status_meta.get("counts_as_observed_coverage"):
        # Mode « réel » demandé mais preuve absente → refuser inventaire observé
        status_meta = {
            **status_meta,
            "mode": "planned",
            "badge": (status_meta.get("lifecycle") or {}).get("ui_badges", {}).get("asset")
            or "Statut individuel à confirmer",
            "note": (
                "Mode réel demandé mais aucune preuve de mise en service — "
                "impact conservé comme estimé / projeté."
            ),
        }

    life = status_meta.get("lifecycle") or {}
    impact_nature = "estimation_couverture_reseau"
    impact_nature_label = (
        "Population NCI non couverte dans le rayon — bénéficiaires projetés après mise en service"
    )
    if status_meta.get("counts_as_observed_coverage"):
        impact_nature = "couverture_observee"
        impact_nature_label = "Couverture réellement observée (preuve individuelle)"
    elif (life.get("impact_status") or {}).get("code") == "projected":
        impact_nature = "projection_couverture_reseau"
        impact_nature_label = (
            "Bénéficiaires projetés dans les localités du rayon après mise en service"
        )
    localities_table = []
    for row in unc_dedup["items"]:
        localities_table.append(
            {
                "name": row.get("name"),
                "population": _safe_int(row.get("population") or row.get("population_impacted")),
                "before": "non_couverte",
                "after": "nouvellement_couverte",
                "state": "nouvellement couverte",
                "distance_m": row.get("_distance_m"),
                "source": row.get("source") or "data/coverage/localities_uncovered.jsonl",
                "confidence": row.get("confidence_level") or unc_dedup["confidence"],
                "need_id": row.get("need_id") or row.get("id"),
                "latitude": row.get("latitude"),
                "longitude": row.get("longitude"),
                "province": row.get("province"),
                "territoire": row.get("territoire"),
                "resolution": resolve_locality_link(
                    nci_row=row, distance_m=row.get("_distance_m")
                ),
            }
        )
    for row in cov_dedup["items"]:
        localities_table.append(
            {
                "name": row.get("name"),
                "population": _safe_int(row.get("population")),
                "before": "deja_couverte",
                "after": "deja_couverte",
                "state": "déjà couverte",
                "distance_m": row.get("_distance_m"),
                "source": "data/coverage/localities_covered.jsonl",
                "confidence": cov_dedup["confidence"],
                "need_id": row.get("id"),
                "latitude": row.get("latitude"),
                "longitude": row.get("longitude"),
                "province": row.get("province"),
                "territoire": row.get("territoire"),
                "resolution": resolve_locality_link(
                    nci_row=row, distance_m=row.get("_distance_m")
                ),
            }
        )

    return {
        "_meta": {
            "engine": ENGINE_VERSION,
            "generated_at": _now(),
            "data_first": True,
            "cacheable": True,
        },
        "asset_type": "FDSU_SITE",
        "asset_id": site.get("id") or asset_id,
        "name": site.get("site_name"),
        "site_code": site.get("site_code"),
        "program": site.get("program_code"),
        "phase": _phase_for_program(site.get("program_code")),
        "province": site.get("province"),
        "territoire": site.get("territoire"),
        "zone": site.get("zone"),
        "status_raw": site.get("status"),
        "deployment": status_meta,
        "deployment_date": None,  # jamais inventé
        "service_radius_m": radius,
        "baseline": {
            "population_total": pop_total if pop_total else None,
            "population_covered": pop_covered if cov_dedup["items"] or pop_covered else (pop_covered or None),
            "population_uncovered": pop_uncovered if unc_dedup["items"] or pop_uncovered else (pop_uncovered or None),
            "localities_total": locs_total,
            "localities_covered": locs_covered,
            "localities_uncovered": locs_uncovered,
            "coverage_rate_pct": rate_before,
            "method": "nci_covered_plus_uncovered_in_radius_exclusive",
            "confidence": "medium" if missing else ("high" if pop_total else "low"),
        },
        "impact": {
            "new_population_covered": pop_uncovered if pop_uncovered else None,
            "new_localities_covered": locs_uncovered,
            "population_already_covered": pop_covered if pop_covered else None,
            "population_after_covered": pop_after_covered,
            "remaining_population_uncovered": remaining_after,
            "coverage_rate_before_pct": rate_before,
            "coverage_rate_after_pct": rate_after,
            "gain_beneficiaries": pop_uncovered if pop_uncovered else None,
            "note": rate_note,
            "nature": impact_nature,
            "nature_label": impact_nature_label,
        },
        "lifecycle": life,
        "ui_badges": life.get("ui_badges") or {
            "data": "Données intégrées",
            "program": status_meta.get("badge"),
            "asset": "Statut individuel à confirmer",
            "impact": "Impact estimé",
        },
        "dedup": {
            "uncovered": {k: v for k, v in unc_dedup.items() if k != "items"},
            "covered": {k: v for k, v in cov_dedup.items() if k != "items"},
        },
        "localities": localities_table,
        "sources": [
            "data/coverage/localities_uncovered.jsonl",
            "data/coverage/localities_covered.jsonl",
            "NSME match_site_to_uncovered_localities",
            "programs.fdsu_sites" if DATA_MODE == "db" else "data/programs",
        ],
        "confidence": unc_dedup["confidence"] if locs_uncovered else "low",
        "limits": [
            "Pas de date de déploiement inventée.",
            "Les sites 40/300 n’ont pas de population native — impact issu du NCI spatial.",
            "Chevauchements multi-sites gérés au niveau scénario via dédup NCI id.",
            rate_note,
        ],
        "explainability": {
            "question": "D’où vient la population nouvellement couverte ?",
            "answer": (
                f"{locs_uncovered} localité(s) NCI non couverte(s) dans un rayon de {int(radius)} m, "
                f"population dédupliquée = {pop_uncovered}."
            ),
            "calculation_detail": {
                "radius_m": radius,
                "uncovered_dedup": {k: v for k, v in unc_dedup.items() if k != "items"},
                "covered_dedup": {k: v for k, v in cov_dedup.items() if k != "items"},
                "double_counting_guard": "nci_need_id_exclusive",
            },
        },
    }


def build_ccn_impact_profile(ccn_id: str) -> dict[str, Any] | None:
    """Impact CCN — bénéficiaires potentiels ≠ couverture radio."""
    ccns = nsme._load_ccn_assets()  # noqa: SLF001
    ccn = next(
        (
            c
            for c in ccns
            if str(c.get("id")) == str(ccn_id)
            or str(c.get("business_id")) == str(ccn_id)
            or _norm(c.get("name")) == _norm(ccn_id)
        ),
        None,
    )
    if not ccn:
        try:
            from api.services import ccn_operational_service as ccn_svc

            payload = ccn_svc.get_ccn(str(ccn_id)) if hasattr(ccn_svc, "get_ccn") else ccn_svc.list_ccn(limit=50)
            items = []
            if isinstance(payload, dict):
                if payload.get("ccn") and isinstance(payload["ccn"], dict):
                    items = [payload["ccn"]]
                else:
                    items = payload.get("ccn") or payload.get("items") or []
            ccn = next(
                (
                    c
                    for c in items
                    if str(c.get("id")) == str(ccn_id) or str(c.get("business_id")) == str(ccn_id)
                ),
                items[0] if len(items) == 1 else None,
            )
        except Exception:
            ccn = None
    if not ccn:
        return None

    radius = float(nsme._radius_for_asset("ccn"))  # noqa: SLF001
    matches = nsme.match_ccn_to_population(ccn, max_distance_m=radius)
    unc = _dedup_population(
        [
            {
                "id": m.get("need_id"),
                "need_id": m.get("need_id"),
                "name": (m.get("properties") or {}).get("locality_name"),
                "population": m.get("population_impacted"),
                "population_impacted": m.get("population_impacted"),
                "_distance_m": m.get("distance_m"),
                "latitude": (m.get("properties") or {}).get("need_lat"),
                "longitude": (m.get("properties") or {}).get("need_lon"),
            }
            for m in matches
        ]
    )
    served = _safe_int(ccn.get("population_served"))
    return {
        "_meta": {"engine": ENGINE_VERSION, "generated_at": _now(), "data_first": True},
        "asset_type": "CCN",
        "asset_id": ccn.get("id") or ccn_id,
        "name": ccn.get("name"),
        "program": "ccn",
        "phase": _phase_for_program("ccn"),
        "ccn_type": ccn.get("ccn_type") or ccn.get("type"),
        "province": ccn.get("province"),
        "territoire": ccn.get("territoire"),
        "deployment": classify_deployment_status(ccn.get("status"), asset_type="CCN"),
        "deployment_date": None,
        "service_radius_m": radius,
        "impact": {
            "population_served_declared": served,
            "population_nci_uncovered_in_radius": unc["population_dedupliquee"] or None,
            "localities_accessible": unc["localites_dedupliquees"],
            "new_population_covered": None,  # ne pas présenter comme couverture radio
            "gain_beneficiaries_potential": served,
            "nature": "acces_services_numeriques_ccn",
            "nature_label": "Bénéficiaires potentiels d’accès aux services numériques — pas une couverture radio",
            "note": "Un CCN n’est pas assimilé à une couverture réseau radio.",
        },
        "localities": [
            {
                "name": r.get("name"),
                "population": _safe_int(r.get("population")),
                "before": "non_couverte",
                "after": "accessible_ccn_potentiel",
                "state": "accès CCN potentiel",
                "distance_m": r.get("_distance_m"),
                "source": "nci_uncovered+ccn_radius",
                "confidence": "low",
                "need_id": r.get("need_id") or r.get("id"),
                "latitude": r.get("latitude"),
                "longitude": r.get("longitude"),
            }
            for r in unc["items"]
        ],
        "sources": ["data/programs/ccn/demo_ccn.json", "NCI uncovered (rayon)", "doctrine CCN"],
        "confidence": "low",
        "limits": [
            "Données CCN en démonstration.",
            "population_served déclarée distincte de la couverture NCI.",
            "Pas de création automatique de couverture radio.",
        ],
        "explainability": {
            "question": "Le CCN crée-t-il une couverture réseau ?",
            "answer": "Non. Il cible l’accès aux services numériques ; la couverture radio reste un actif distinct.",
        },
    }


def _list_program_sites(program_code: str, *, province: str | None = None, territoire: str | None = None, limit: int = 80) -> list[dict[str, Any]]:
    code = program_code.replace("PROG_", "")
    if DATA_MODE == "db":
        return nsme.list_fdsu_sites(program_code=code, province=province, territoire=territoire, limit=limit)
    try:
        from api.services import fdsu_sites_import_service as imports

        payload = imports.load_program_sites(code.lower() if not code.startswith("sites") else code)
        sites = []
        for s in (payload.get("sites") or [])[:limit]:
            if province and _norm(s.get("province")) != _norm(province):
                continue
            if territoire and _norm(s.get("territoire")) != _norm(territoire):
                continue
            sites.append(
                {
                    "id": s.get("site_id") or s.get("id"),
                    "site_code": s.get("site_code") or str(s.get("site_id")),
                    "site_name": s.get("site_name") or s.get("name"),
                    "province": s.get("province"),
                    "territoire": s.get("territoire"),
                    "zone": s.get("zone"),
                    "status": s.get("status"),
                    "latitude": s.get("latitude"),
                    "longitude": s.get("longitude"),
                    "program_code": s.get("program_code") or code,
                }
            )
        return sites
    except Exception:
        return []


def build_deployment_scenario(
    *,
    scope: dict[str, Any] | None = None,
    programs: list[str] | None = None,
    mode: str = "planned",
    order: str = "program_phase",
    limit_per_program: int = 40,
    include_ccn: bool = True,
) -> dict[str, Any]:
    """Scénario multi-déploiements avec progression cumulative sans double-comptage."""
    scope = scope or {"level": "national"}
    programs = programs or ["sites_40", "sites_300", "sites_20476"]
    province = scope.get("province")
    territoire = scope.get("territoire")
    zone = scope.get("zone")

    cache_key = f"{mode}|{order}|{programs}|{province}|{territoire}|{zone}|{limit_per_program}|{include_ccn}"
    now = time.time()
    if cache_key in _CACHE["payloads"] and now - _CACHE["ts"] < _CACHE_TTL_S:
        cached = _CACHE["payloads"][cache_key]
        cached = dict(cached)
        cached["_meta"] = {**(cached.get("_meta") or {}), "cache_hit": True}
        return cached

    # Baseline nationale ou territoriale depuis agrégats NCI (pas d’invention)
    baseline = {
        "population_total": None,
        "population_covered": None,
        "population_uncovered": None,
        "localities_total": None,
        "localities_covered": None,
        "localities_uncovered": None,
        "source": "data/coverage/aggregates.json",
        "method": "nci_aggregate",
        "confidence": "medium",
    }
    agg = nci.get_aggregates() or {}
    if territoire:
        row = (agg.get("by_territory") or {}).get(territoire) or nci.get_territory_coverage(str(territoire))
        if isinstance(row, dict) and row.get("territory"):
            row = row["territory"]
        if isinstance(row, dict):
            cov = _safe_int(row.get("population_covered"))
            unc = _safe_int(row.get("population_uncovered") or row.get("population_remaining"))
            baseline.update(
                {
                    "population_covered": cov,
                    "population_uncovered": unc,
                    "population_total": (cov or 0) + (unc or 0) if cov is not None and unc is not None else None,
                    "localities_covered": _safe_int(row.get("localities_covered")),
                    "localities_uncovered": _safe_int(row.get("localities_uncovered")),
                    "confidence": "medium",
                }
            )
    elif province:
        by_p = agg.get("by_province") or {}
        row = None
        for k, v in by_p.items():
            if _norm(k) == _norm(province) or _norm((v or {}).get("province")) == _norm(province):
                row = v
                break
        if isinstance(row, dict):
            cov = _safe_int(row.get("population_covered"))
            unc = _safe_int(row.get("population_uncovered"))
            baseline.update(
                {
                    "population_covered": cov,
                    "population_uncovered": unc,
                    "population_total": (cov or 0) + (unc or 0) if cov is not None and unc is not None else None,
                    "localities_covered": _safe_int(row.get("localities_covered")),
                    "localities_uncovered": _safe_int(row.get("localities_uncovered")),
                }
            )
    else:
        national = agg.get("national") or {}
        cov = _safe_int(national.get("population_covered"))
        unc = _safe_int(national.get("population_uncovered"))
        baseline.update(
            {
                "population_covered": cov,
                "population_uncovered": unc,
                "population_total": _safe_int(national.get("population_total_observed"))
                or ((cov or 0) + (unc or 0) if cov is not None and unc is not None else None),
                "localities_covered": _safe_int(national.get("localities_covered")),
                "localities_uncovered": _safe_int(national.get("localities_uncovered")),
                "confidence": "high",
            }
        )

    assets: list[dict[str, Any]] = []
    for prog in programs:
        for site in _list_program_sites(prog, province=province, territoire=territoire, limit=limit_per_program):
            if zone and _norm(site.get("zone")) != _norm(zone):
                continue
            assets.append({"kind": "FDSU_SITE", "ref": site})
    if include_ccn:
        for ccn in nsme._load_ccn_assets()[:20]:  # noqa: SLF001
            if province and _norm(ccn.get("province")) != _norm(province):
                continue
            if territoire and _norm(ccn.get("territoire")) != _norm(territoire):
                continue
            assets.append({"kind": "CCN", "ref": ccn})

    # Ordre : phase programme puis id — pas de date inventée
    phase_rank = {"sites_40": 0, "prog_sites_40": 0, "sites_300": 1, "prog_sites_300": 1, "sites_20476": 2, "prog_sites_20476": 2, "ccn": 3}

    def sort_key(item: dict[str, Any]) -> tuple:
        ref = item["ref"]
        code = _norm(ref.get("program_code") or ("ccn" if item["kind"] == "CCN" else ""))
        rank = 99
        for k, v in phase_rank.items():
            if k in code:
                rank = v
                break
        return (rank, str(ref.get("id") or ref.get("site_code") or ref.get("business_id") or ""))

    if order == "impact":
        # pré-calcul léger différé — pour v1 on garde phase puis on pourra re-trier
        assets.sort(key=sort_key)
    else:
        assets.sort(key=sort_key)

    covered_keys: set[str] = set()
    deployments: list[dict[str, Any]] = []
    cumulative_pop = 0
    cumulative_locs = 0
    bar_series: list[dict[str, Any]] = []
    curve: list[dict[str, Any]] = [
        {
            "step": 0,
            "label": "Baseline",
            "cumulative_population_covered_gain": 0,
            "baseline_covered": baseline.get("population_covered"),
            "remaining_uncovered": baseline.get("population_uncovered"),
        }
    ]

    for idx, item in enumerate(assets, start=1):
        ref = item["ref"]
        if item["kind"] == "FDSU_SITE":
            profile = build_site_impact_profile(
                ref.get("id") or ref.get("site_code"),
                program_code=ref.get("program_code"),
                scenario_mode=mode,
            )
            if not profile:
                continue
            new_keys = []
            new_pop = 0
            new_locs = 0
            added_localities = []
            for loc in profile.get("localities") or []:
                if loc.get("before") != "non_couverte":
                    continue
                key = population_key(need_id=str(loc.get("need_id") or ""))
                if key in covered_keys or key == "unknown":
                    continue
                covered_keys.add(key)
                new_keys.append(key)
                p = _safe_int(loc.get("population"))
                if p is not None:
                    new_pop += p
                new_locs += 1
                added_localities.append(loc)
            cumulative_pop += new_pop
            cumulative_locs += new_locs
            remaining = None
            if baseline.get("population_uncovered") is not None:
                remaining = max(0, int(baseline["population_uncovered"]) - cumulative_pop)
            dep = {
                "step": idx,
                "asset_type": "FDSU_SITE",
                "asset_id": profile.get("asset_id"),
                "name": profile.get("name"),
                "program": profile.get("program"),
                "phase": profile.get("phase"),
                "status": profile.get("deployment", {}).get("status"),
                "badge": profile.get("deployment", {}).get("badge"),
                "mode": profile.get("deployment", {}).get("mode"),
                "deployment_date": None,
                "new_population_covered": new_pop,
                "cumulative_population_covered": cumulative_pop,
                "remaining_population_uncovered": remaining,
                "new_localities_covered": new_locs,
                "cumulative_localities_covered": cumulative_locs,
                "localities": added_localities,
                "excluded_already_counted": len((profile.get("localities") or [])) - len(added_localities) - sum(
                    1 for l in (profile.get("localities") or []) if l.get("before") == "deja_couverte"
                ),
                "source": "NCI uncovered + NSME radius",
                "method": "incremental_dedup_nci_id",
                "confidence": profile.get("confidence"),
                "nature": "estimation_couverture_reseau",
            }
            deployments.append(dep)
            bar_series.append(
                {
                    "id": dep["asset_id"],
                    "label": dep["name"],
                    "value": new_pop,
                    "program": dep["program"],
                    "nature": "couverture_reseau",
                    "badge": dep["badge"],
                }
            )
            curve.append(
                {
                    "step": idx,
                    "label": dep["name"],
                    "asset_id": dep["asset_id"],
                    "program": dep["program"],
                    "new_population_covered": new_pop,
                    "cumulative_population_covered_gain": cumulative_pop,
                    "cumulative_localities": cumulative_locs,
                    "remaining_uncovered": remaining,
                    "badge": dep["badge"],
                }
            )
        else:
            profile = build_ccn_impact_profile(str(ref.get("id") or ref.get("business_id")))
            if not profile:
                continue
            # CCN : contribution séparée — n'alimente PAS la couverture radio cumulative
            pot = _safe_int((profile.get("impact") or {}).get("gain_beneficiaries_potential")) or 0
            dep = {
                "step": idx,
                "asset_type": "CCN",
                "asset_id": profile.get("asset_id"),
                "name": profile.get("name"),
                "program": "ccn",
                "phase": profile.get("phase"),
                "status": profile.get("deployment", {}).get("status"),
                "badge": profile.get("deployment", {}).get("badge"),
                "mode": "demonstration",
                "deployment_date": None,
                "new_population_covered": 0,
                "cumulative_population_covered": cumulative_pop,
                "remaining_population_uncovered": (
                    max(0, int(baseline["population_uncovered"]) - cumulative_pop)
                    if baseline.get("population_uncovered") is not None
                    else None
                ),
                "beneficiaries_potential": pot,
                "new_localities_covered": 0,
                "localities": profile.get("localities") or [],
                "source": "demo_ccn",
                "method": "declared_population_served",
                "confidence": "low",
                "nature": "acces_services_numeriques_ccn",
                "note": "Exclu du cumul couverture radio.",
            }
            deployments.append(dep)
            bar_series.append(
                {
                    "id": dep["asset_id"],
                    "label": f"CCN · {dep['name']}",
                    "value": pot,
                    "program": "ccn",
                    "nature": "beneficiaires_potentiels_ccn",
                    "badge": dep["badge"],
                }
            )
            curve.append(
                {
                    "step": idx,
                    "label": f"CCN · {dep['name']}",
                    "asset_id": dep["asset_id"],
                    "program": "ccn",
                    "new_population_covered": 0,
                    "beneficiaries_potential": pot,
                    "cumulative_population_covered_gain": cumulative_pop,
                    "badge": dep["badge"],
                    "note": "Point CCN non additionné à la couverture radio.",
                }
            )

    # Comparaison programmes
    by_program: dict[str, dict[str, Any]] = {}
    for dep in deployments:
        prog = str(dep.get("program") or "unknown")
        bucket = by_program.setdefault(
            prog,
            {
                "program": prog,
                "phase": dep.get("phase"),
                "sites_or_ccn": 0,
                "new_population_covered": 0,
                "beneficiaries_potential_ccn": 0,
                "new_localities_covered": 0,
            },
        )
        bucket["sites_or_ccn"] += 1
        bucket["new_population_covered"] += int(dep.get("new_population_covered") or 0)
        bucket["beneficiaries_potential_ccn"] += int(dep.get("beneficiaries_potential") or 0)
        bucket["new_localities_covered"] += int(dep.get("new_localities_covered") or 0)

    composition = {
        "already_covered": baseline.get("population_covered"),
        "newly_covered_cumulative": cumulative_pop,
        "remaining_uncovered": (
            max(0, int(baseline["population_uncovered"]) - cumulative_pop)
            if baseline.get("population_uncovered") is not None
            else None
        ),
        "without_reliable_data": None,
        "note": "Cumul « newly_covered » = NCI uncovered attribués sans double-comptage ; baseline NCI distincte.",
    }

    payload = {
        "_meta": {
            "engine": ENGINE_VERSION,
            "generated_at": _now(),
            "cache_hit": False,
            "last_calculation": _now(),
            "ttl_seconds": _CACHE_TTL_S,
            "data_first": True,
        },
        "scope": scope,
        "mode": mode,
        "baseline": baseline,
        "deployments": deployments,
        "charts": {
            "cumulative_curve": curve,
            "contribution_bars": bar_series,
            "coverage_composition": composition,
            "localities_progression": {
                "localities_covered_baseline": baseline.get("localities_covered"),
                "localities_uncovered_baseline": baseline.get("localities_uncovered"),
                "localities_added_in_scenario": cumulative_locs,
                "localities_cumulative_covered_after_scenario": (
                    (baseline.get("localities_covered") or 0) + cumulative_locs
                    if baseline.get("localities_covered") is not None
                    else cumulative_locs
                ),
                "localities_remaining_uncovered": (
                    max(0, int(baseline["localities_uncovered"]) - cumulative_locs)
                    if baseline.get("localities_uncovered") is not None
                    else None
                ),
                "curve": [
                    {
                        "step": p.get("step"),
                        "label": p.get("label"),
                        "cumulative_localities": p.get("cumulative_localities"),
                        "new_population_covered": p.get("new_population_covered"),
                    }
                    for p in curve
                    if p.get("step", 0) > 0 and p.get("program") != "ccn"
                ],
                "note": "Localités NCI newly attributed — distinct de la population couverte.",
            },
            "by_program": list(by_program.values()),
        },
        "summary": {
            "deployments_count": len(deployments),
            "cumulative_new_population": cumulative_pop,
            "cumulative_new_localities": cumulative_locs,
            "remaining_uncovered": composition["remaining_uncovered"],
            "monotone_cumulative": True,
            "double_counting_guard": "nci_need_id_set_across_deployments",
        },
        "data_quality": {
            "sources": [
                "data/coverage/aggregates.json",
                "data/coverage/localities_uncovered.jsonl",
                "data/coverage/localities_covered.jsonl",
                "programs.fdsu_sites / data/programs",
                "data/programs/ccn/demo_ccn.json",
            ],
            "confidence": baseline.get("confidence") or "medium",
            "limits": [
                "Aucune date de déploiement inventée.",
                "Impact couverture = estimation NCI dans rayon.",
                "CCN exclus du cumul radio.",
                "Sites sans coordonnées exclus.",
            ],
        },
    }
    _CACHE["ts"] = now
    _CACHE["payloads"][cache_key] = payload
    return payload


def audit_population_sources() -> dict[str, Any]:
    """Matrice d’audit des sources — lecture seule."""
    return {
        "_meta": {"engine": ENGINE_VERSION, "generated_at": _now()},
        "matrix": [
            {
                "source": "NCI uncovered",
                "identifier": "id (NCI-UNC-…)",
                "locality": "name + province/territoire",
                "population": "population",
                "coverage": "uncovered",
                "site_associated": "destination (soft)",
                "geometry": "lat/lon",
                "quality": "CDQS",
                "path": "data/coverage/localities_uncovered.jsonl",
            },
            {
                "source": "NCI covered",
                "identifier": "id (NCI-COV-…)",
                "locality": "name + admin",
                "population": "population",
                "coverage": "covered",
                "site_associated": "destination (soft)",
                "geometry": "lat/lon",
                "quality": "CDQS",
                "path": "data/coverage/localities_covered.jsonl",
            },
            {
                "source": "NCI aggregates",
                "identifier": "province / territoire name",
                "locality": "counts",
                "population": "covered + uncovered",
                "coverage": "ratios",
                "site_associated": "none",
                "geometry": "none",
                "quality": "medium",
                "path": "data/coverage/aggregates.json",
            },
            {
                "source": "Sites 40 / 300",
                "identifier": "site id / code",
                "locality": "admin only",
                "population": "absent",
                "coverage": "none",
                "site_associated": "self",
                "geometry": "point",
                "quality": "coords only",
                "path": "data/programs/sites_40|300",
            },
            {
                "source": "Sites 20 476",
                "identifier": "site_code",
                "locality": "admin",
                "population": "population + range",
                "coverage": "indirect via NCI name",
                "site_associated": "self",
                "geometry": "point",
                "quality": "import CSV",
                "path": "data/programs/sites_20476",
            },
            {
                "source": "public.localites",
                "identifier": "id/code",
                "locality": "nom",
                "population": "none",
                "coverage": "none",
                "site_associated": "parent chain",
                "geometry": "geom",
                "quality": "admin référentiel",
                "path": "public.localites",
            },
            {
                "source": "CCN DEMO",
                "identifier": "CCN-DEMO-…",
                "locality": "admin",
                "population": "population_served",
                "coverage": "n/a (services numériques)",
                "site_associated": "site_fdsu_code",
                "geometry": "point",
                "quality": "demonstration",
                "path": "data/programs/ccn/demo_ccn.json",
            },
        ],
    }
