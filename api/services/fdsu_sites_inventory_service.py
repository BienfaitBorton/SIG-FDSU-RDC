"""Inventaire unifié des Sites FDSU (40 / 300 / 20 476).

Sources autoritatives (fichiers programme déjà intégrés) :
- Sites 40  → data/programs/sites_40/sites_40.json
- Sites 300 → data/programs/sites_300/sites_300.json
- Sites 20 476 → data/programs/sites_20476/sites_20476.json
  (+ enrichissement libellé via NCI uncovered.infra_name, jointure sur site_name)

Portefeuille 340 = agrégat Sites 40 + Sites 300 uniquement (pas un 3ᵉ programme).
Le compteur principal documenté = effectif du programme national Sites 20 476.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from api.services import fdsu_site_priority_service, fdsu_sites_import_service
from api.services.site_display_name import (
    NCI_UNCOVERED,
    enrich_site_labels,
    is_technical_site_identifier,
)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
_INVENTORY_CACHE: dict[str, tuple[float, list[dict[str, Any]]]] = {}

PROGRAM_CODES = ("sites_40", "sites_300", "sites_20476")


def _now_iso() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat()


def _normalize_program_site(site: dict[str, Any], program_code: str, index: int) -> dict[str, Any]:
    meta = fdsu_sites_import_service.program_meta(program_code)
    code = meta["program_code"]
    status = site.get("status") or site.get("priority_status")
    if not status:
        if code == "sites_40":
            status = "En exécution"
        elif code == "sites_300":
            status = "Planifié"
        else:
            status = "Programme national"

    raw_name = site.get("site_name") or site.get("name")
    row = {
        "site_id": site.get("site_id") or index,
        "site_code": site.get("site_code") or site.get("code") or f"{code.upper()}_{index:05d}",
        "site_name": raw_name,
        "name": site.get("name") or raw_name,
        "program_code": code,
        "program_label": meta.get("label"),
        "programme": site.get("programme") or meta.get("label"),
        "phase": meta.get("phase"),
        "province": site.get("province"),
        "territoire": site.get("territoire"),
        "zone": site.get("zone"),
        "status": status,
        "priority_status": site.get("priority_status"),
        "priority": site.get("priority") or site.get("priority_level"),
        "fdsu_score": site.get("fdsu_score"),
        "priority_score": site.get("priority_score"),
        "priority_level": site.get("priority_level"),
        "latitude": site.get("latitude"),
        "longitude": site.get("longitude"),
        "population": site.get("population"),
        "population_range": site.get("population_range"),
        "nearest_site": site.get("nearest_site"),
        "distance": site.get("distance"),
        "distance_level": site.get("distance_level"),
        "is_300_planned": bool(site.get("is_300_planned")) or code == "sites_300",
        "has_geometry": bool(
            site.get("has_geometry")
            if site.get("has_geometry") is not None
            else (site.get("latitude") is not None and site.get("longitude") is not None)
        ),
        "source": site.get("source") or meta.get("label"),
        "village_name": site.get("village_name"),
        "locality_name": site.get("locality_name") or site.get("localite"),
        "infra_name": site.get("infra_name"),
    }
    return enrich_site_labels(row)


def _program_mtime(program_code: str) -> float:
    path = fdsu_sites_import_service.program_output_dir(program_code) / f"{program_code}.json"
    try:
        return path.stat().st_mtime if path.exists() else 0.0
    except OSError:
        return 0.0


def _load_program_inventory(program_code: str) -> list[dict[str, Any]]:
    code = fdsu_sites_import_service.normalize_program_code(program_code)
    nci_m = 0.0
    try:
        nci_m = NCI_UNCOVERED.stat().st_mtime if NCI_UNCOVERED.exists() else 0.0
    except OSError:
        nci_m = 0.0
    stamp = _program_mtime(code) + nci_m
    cached = _INVENTORY_CACHE.get(code)
    if cached and cached[0] == stamp:
        return cached[1]

    sites = fdsu_site_priority_service._sites_for_program(code)  # noqa: SLF001 — même source priorisation
    normalized = [_normalize_program_site(site, code, index) for index, site in enumerate(sites, start=1)]
    _INVENTORY_CACHE[code] = (stamp, normalized)
    return normalized


def inventory_summary() -> dict[str, Any]:
    counts = {code: len(_load_program_inventory(code)) for code in PROGRAM_CODES}
    sites_40 = counts["sites_40"]
    sites_300 = counts["sites_300"]
    sites_20476 = counts["sites_20476"]
    portfolio_340 = sites_40 + sites_300

    # Chevauchements documentés (pas de double comptage dans le KPI principal)
    national = _load_program_inventory("sites_20476")
    flagged_300 = sum(1 for s in national if s.get("is_300_planned"))
    village_name_count = sum(1 for s in national if s.get("village_name"))
    locality_count = sum(1 for s in national if s.get("locality_name"))
    infra_label_count = sum(
        1
        for s in national
        if s.get("infra_name") and not is_technical_site_identifier(s.get("display_name"))
        and s.get("display_name_source") == "infra_name"
    )
    technical_fallback = sum(1 for s in national if s.get("display_name_is_technical_fallback"))

    return {
        "_meta": {
            "title": "Inventaire des Sites FDSU",
            "computed_at": _now_iso(),
            "primary_counter": {
                "key": "sites_20476",
                "label": "Programme national Sites 20 476",
                "value": sites_20476,
                "definition": (
                    "Effectif du programme national Sites 20 476 "
                    "(source autoritative data/programs/sites_20476). "
                    "Ce compteur n’additionne pas Sites 40 ni Sites 300."
                ),
            },
            "portfolio_340": {
                "label": "Portefeuille 340 (Sites 40 + Sites 300)",
                "value": portfolio_340,
                "definition": (
                    "Agrégat Sites 40 + Sites 300 uniquement. "
                    "Ce n’est pas un troisième programme."
                ),
                "sites_40": sites_40,
                "sites_300": sites_300,
            },
            "overlaps": {
                "national_flagged_is_300_planned": flagged_300,
                "note": (
                    "Le programme national marque is_300_planned=true pour une partie des sites "
                    f"({flagged_300}). Sites 40 / 300 / 20 476 ne sont pas des populations disjointes "
                    "au sens métier ; aucun total unique national n’est fabriqué par somme aveugle."
                ),
            },
            "display_name_audit_20476": {
                "village_name_present": village_name_count,
                "locality_name_present": locality_count,
                "display_from_infra_name": infra_label_count,
                "technical_fallback": technical_fallback,
                "source_note": (
                    "Le CSV PROGRAMME 20476 SITES.csv et l’Excel NCI « Localités non couvertes » "
                    "n’exposent pas de colonne Village Name. Le libellé principal utilise "
                    "infra_name NCI (Nom de l’infrastructure de base) lorsqu’il est disponible, "
                    "sinon repli sur l’identifiant technique site_name."
                ),
            },
        },
        "programs": [
            {
                **fdsu_sites_import_service.program_meta(code),
                "site_count": counts[code],
                "status_label": (
                    "En exécution" if code == "sites_40" else "Planifié" if code == "sites_300" else "National"
                ),
            }
            for code in PROGRAM_CODES
        ],
        "counts": {
            "sites_40": sites_40,
            "sites_300": sites_300,
            "sites_20476": sites_20476,
            "portfolio_340": portfolio_340,
            "primary": sites_20476,
        },
    }


def _match_text(site: dict[str, Any], query: str) -> bool:
    q = query.lower().strip()
    if not q:
        return True
    hay = " ".join(
        str(site.get(k) or "")
        for k in (
            "display_name",
            "site_name",
            "name",
            "site_code",
            "technical_id",
            "province",
            "territoire",
            "village_name",
            "locality_name",
            "infra_name",
            "nearest_site",
        )
    ).lower()
    return q in hay


def list_inventory(
    *,
    program_code: str | None = None,
    status: str | None = None,
    province: str | None = None,
    territoire: str | None = None,
    priority: str | None = None,
    q: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> dict[str, Any]:
    codes = (
        [fdsu_sites_import_service.normalize_program_code(program_code)]
        if program_code and program_code not in {"all", "*", "portfolio_340"}
        else list(PROGRAM_CODES)
    )
    if program_code == "portfolio_340":
        codes = ["sites_40", "sites_300"]

    rows: list[dict[str, Any]] = []
    for code in codes:
        rows.extend(_load_program_inventory(code))

    if status:
        status_l = status.lower().strip()
        rows = [r for r in rows if status_l in str(r.get("status") or "").lower()]
    if province:
        prov_l = province.lower().strip()
        rows = [r for r in rows if prov_l in str(r.get("province") or "").lower()]
    if territoire:
        terr_l = territoire.lower().strip()
        rows = [r for r in rows if terr_l in str(r.get("territoire") or "").lower()]
    if priority:
        prio_l = priority.lower().strip()
        rows = [
            r
            for r in rows
            if prio_l in str(r.get("priority_level") or r.get("priority") or r.get("priority_status") or "").lower()
        ]
    if q:
        rows = [r for r in rows if _match_text(r, q)]

    # Tri : score desc si dispo, sinon nom
    rows.sort(
        key=lambda r: (
            -float(r.get("priority_score") or r.get("fdsu_score") or 0),
            str(r.get("display_name") or ""),
        )
    )

    total = len(rows)
    page = rows[offset : offset + max(1, min(limit, 500))]

    # Facettes légères sur le filtre courant (échantillon borné pour perf)
    facet_source = rows if total <= 5000 else rows[:5000]
    provinces = sorted({str(r.get("province")) for r in facet_source if r.get("province")})
    territoires = sorted({str(r.get("territoire")) for r in facet_source if r.get("territoire")})
    statuses = sorted({str(r.get("status")) for r in facet_source if r.get("status")})

    by_program = {}
    for code in PROGRAM_CODES:
        by_program[code] = sum(1 for r in rows if r.get("program_code") == code)
    by_status: dict[str, int] = {}
    for r in rows:
        key = str(r.get("status") or "Non renseigné")
        by_status[key] = by_status.get(key, 0) + 1

    summary = inventory_summary()
    return {
        "_meta": {
            **summary["_meta"],
            "filter": {
                "program_code": program_code,
                "status": status,
                "province": province,
                "territoire": territoire,
                "priority": priority,
                "q": q,
            },
        },
        "counts": summary["counts"],
        "programs": summary["programs"],
        "distribution": {
            "by_program": by_program,
            "by_status": by_status,
        },
        "facets": {
            "provinces": provinces[:80],
            "territoires": territoires[:120],
            "statuses": statuses,
        },
        "total": total,
        "count": len(page),
        "offset": offset,
        "limit": limit,
        "sites": page,
    }


def get_inventory_site(site_id: int | str, *, program_code: str | None = None) -> dict[str, Any] | None:
    try:
        sid = int(site_id)
    except (TypeError, ValueError):
        sid = None
    codes = (
        [fdsu_sites_import_service.normalize_program_code(program_code)]
        if program_code
        else list(PROGRAM_CODES)
    )
    for code in codes:
        for site in _load_program_inventory(code):
            if sid is not None and int(site.get("site_id") or -1) == sid:
                detail = dict(site)
                # Joindre score priorisation si disponible
                explained = fdsu_site_priority_service.explain_site(sid, program_code=code)
                if explained:
                    scored = explained.get("site") or {}
                    detail["priority_score"] = scored.get("priority_score", detail.get("priority_score"))
                    detail["priority_level"] = scored.get("priority_level", detail.get("priority_level"))
                    detail["priority_level_label"] = scored.get("priority_level_label")
                    detail["criteria_details"] = scored.get("criteria_details") or explained.get("criteria_details")
                    detail = enrich_site_labels(detail)
                return {
                    "_meta": {
                        "title": "Fiche site FDSU",
                        "program_code": code,
                        "computed_at": _now_iso(),
                    },
                    "site": detail,
                }
            # Recherche par code
            if str(site.get("site_code") or "") == str(site_id):
                return {
                    "_meta": {"title": "Fiche site FDSU", "program_code": code, "computed_at": _now_iso()},
                    "site": site,
                }
    return None
