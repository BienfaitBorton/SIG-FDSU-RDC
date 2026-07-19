"""Audit d'enrichissement du référentiel localités (lecture seule).

Identifie des candidates NCI absentes des 26 710 localités admin — sans intégrer
ni modifier le référentiel ni les sources brutes.
"""

from __future__ import annotations

import hashlib
import json
import re
import time
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from difflib import SequenceMatcher
from typing import Any

from api.services.nire import locality_coverage as lc

ENGINE_VERSION = "nire-locality-enrichment-audit-1.0.0"

ENRICHMENT_CLASSES = (
    "EXISTING_LOCALITY_VARIANT",
    "DUPLICATE_NCI_OBSERVATION",
    "HOMONYM_DIFFERENT_LOCALITY",
    "AMBIGUOUS_LOCALITY",
    "NEW_LOCALITY_CANDIDATE_HIGH_CONFIDENCE",
    "NEW_LOCALITY_CANDIDATE_REVIEW",
    "UNRESOLVED_LOCALITY",
)

IN_SCOPE_COVERAGE = {
    "UNMATCHED_COVERED",
    "UNMATCHED_UNCOVERED",
    "COVERAGE_STATUS_REQUIRES_REVIEW",
}

THRESHOLDS = {
    "variant_name_ratio": 0.88,
    "ambiguous_variant_gap": 0.05,
    # Proximité = signal de rapprochement nom+géo uniquement (jamais rejet/acceptation seule)
    "geo_variant_m": 1500.0,
    "bbox_padding_deg": 0.25,
    "min_name_len": 3,
}


@dataclass
class EnrichmentAuditState:
    executed: bool = False
    message: str = ""
    meta: dict[str, Any] = field(default_factory=dict)
    kpis: dict[str, Any] = field(default_factory=dict)
    rows: list[dict[str, Any]] = field(default_factory=list)
    funnel: dict[str, Any] = field(default_factory=dict)
    integration_method: dict[str, Any] = field(default_factory=dict)
    performance: dict[str, Any] = field(default_factory=dict)


_STATE = EnrichmentAuditState()


def get_state() -> EnrichmentAuditState:
    return _STATE


def reset_state() -> None:
    global _STATE
    _STATE = EnrichmentAuditState()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _name_ratio(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a, b).ratio()


def _valid_coords(row: dict[str, Any]) -> bool:
    try:
        lat, lon = float(row["latitude"]), float(row["longitude"])
        if lat == 0.0 and lon == 0.0:
            return False
        return -90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0
    except (TypeError, ValueError, KeyError):
        return False


def _exploitable_name(toponym: str) -> bool:
    n = lc._norm(toponym)
    return bool(n and re.search(r"[a-z]", n) and len(n) >= 2)


def identity_key(row: dict[str, Any]) -> str:
    try:
        geo = f"{round(float(row['latitude']), 3)}|{round(float(row['longitude']), 3)}"
    except (TypeError, ValueError, KeyError):
        geo = "nogeo"
    toponym = row.get("toponym") or lc._nci_toponym(row)
    return "|".join(
        [
            lc._norm(toponym),
            lc._norm(row.get("province")),
            lc._norm(row.get("territoire")),
            geo,
        ]
    )


def future_canonical_id(row: dict[str, Any]) -> str:
    """Identifiant idempotent prévu pour une intégration future (non appliqué)."""
    try:
        geo = f"{round(float(row['latitude']), 3)}|{round(float(row['longitude']), 3)}"
    except (TypeError, ValueError, KeyError):
        geo = "nogeo"
    raw = "|".join(
        [
            lc._norm(row.get("toponym") or lc._nci_toponym(row)),
            lc._norm(row.get("province")),
            lc._norm(row.get("territoire")),
            geo,
            "nci",
        ]
    )
    digest = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:12].upper()
    return f"RDC-NCI-LOC-{digest}"


def build_integration_blueprint(candidate: dict[str, Any]) -> dict[str, Any]:
    """Méthode d'intégration idempotente — préparation uniquement, aucune écriture."""
    return {
        "canonical_id": future_canonical_id(candidate),
        "provenance": "nci",
        "source_observation_ids": candidate.get("observation_ids") or [candidate.get("nci_id")],
        "nom_source": candidate.get("toponym") or candidate.get("nci_destination"),
        "nom_normalise": lc._norm(candidate.get("toponym") or ""),
        "administrative_attachment": {
            "province": candidate.get("province"),
            "territoire": candidate.get("territoire"),
            "collectivite": candidate.get("collectivite"),
            "groupement": candidate.get("groupement"),
        },
        "geometry": {
            "type": "Point",
            "coordinates": [
                candidate.get("longitude"),
                candidate.get("latitude"),
            ],
        },
        "nire_status": "pending_human_validation",
        "enrichment_classification": candidate.get("enrichment_class"),
        "integration_date": None,
        "applied": False,
        "idempotency_key": future_canonical_id(candidate),
    }


def describe_integration_method() -> dict[str, Any]:
    return {
        "mode": "idempotent_pending_validation",
        "auto_create_during_audit": False,
        "steps": [
            "1. Valider humainement les NEW_LOCALITY_CANDIDATE_HIGH_CONFIDENCE",
            "2. Générer canonical_id = RDC-NCI-LOC-{sha1(name|prov|terr|geo|nci)[:12]}",
            "3. Upsert par idempotency_key — seconde exécution = no-op",
            "4. Conserver observations NCI séparées (covered/uncovered) liées à l'identité",
            "5. Propager vers hiérarchie / NIRE / NSME uniquement après validation",
        ],
        "required_fields": [
            "canonical_id",
            "provenance",
            "nom_source",
            "nom_normalise",
            "administrative_attachment",
            "geometry",
            "nire_status",
            "integration_date",
        ],
        "note": "Aucune intégration massive exécutée par cet audit.",
    }


def _province_bboxes(admin: list[dict[str, Any]]) -> dict[str, tuple[float, float, float, float]]:
    acc: dict[str, list[tuple[float, float]]] = defaultdict(list)
    for a in admin:
        prov = lc._norm(a.get("province"))
        try:
            lat, lon = float(a["latitude"]), float(a["longitude"])
        except (TypeError, ValueError, KeyError):
            continue
        if prov:
            acc[prov].append((lat, lon))
    out: dict[str, tuple[float, float, float, float]] = {}
    pad = THRESHOLDS["bbox_padding_deg"]
    for prov, pts in acc.items():
        lats = [p[0] for p in pts]
        lons = [p[1] for p in pts]
        out[prov] = (min(lats) - pad, max(lats) + pad, min(lons) - pad, max(lons) + pad)
    return out


def _in_bbox(lat: float, lon: float, bbox: tuple[float, float, float, float] | None) -> bool:
    if not bbox:
        return False
    min_lat, max_lat, min_lon, max_lon = bbox
    return min_lat <= lat <= max_lat and min_lon <= lon <= max_lon


def _nearest_admin_in_province(
    lat: float,
    lon: float,
    province_admins: list[dict[str, Any]],
    *,
    max_m: float,
    geo_grid: dict[tuple[int, int], list[dict[str, Any]]] | None = None,
) -> tuple[dict[str, Any] | None, float | None]:
    # cell 0.02° ≈ 2.2 km ; ring adapté à max_m
    ring = max(2, int(max_m / 2200.0) + 1)
    pool = _grid_neighbors(geo_grid, lat, lon, ring=ring) if geo_grid is not None else province_admins
    best = None
    best_d = None
    for a in pool:
        try:
            d = lc.haversine_m(lat, lon, float(a["latitude"]), float(a["longitude"]))
        except (TypeError, ValueError, KeyError):
            continue
        if d <= max_m and (best_d is None or d < best_d):
            best, best_d = a, d
    return best, best_d


def _name_buckets(admins: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    """Buckets par territoire + initiale pour limiter le fuzzy matching."""
    buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for a in admins:
        akey = lc._norm(a.get("nom"))
        if not akey:
            continue
        terr = lc._norm(a.get("territoire")) or "_"
        initial = akey[0]
        buckets[f"{terr}|{initial}"].append(a)
        buckets[f"{terr}|*"].append(a)
        buckets[f"_|{initial}"].append(a)
    return buckets


def _geo_grid(admins: list[dict[str, Any]], cell: float = 0.02) -> dict[tuple[int, int], list[dict[str, Any]]]:
    grid: dict[tuple[int, int], list[dict[str, Any]]] = defaultdict(list)
    for a in admins:
        try:
            lat, lon = float(a["latitude"]), float(a["longitude"])
        except (TypeError, ValueError, KeyError):
            continue
        grid[(int(lat / cell), int(lon / cell))].append(a)
    return grid


def _grid_neighbors(
    grid: dict[tuple[int, int], list[dict[str, Any]]],
    lat: float,
    lon: float,
    *,
    cell: float = 0.02,
    ring: int = 1,
) -> list[dict[str, Any]]:
    ci, cj = int(lat / cell), int(lon / cell)
    out: list[dict[str, Any]] = []
    for di in range(-ring, ring + 1):
        for dj in range(-ring, ring + 1):
            out.extend(grid.get((ci + di, cj + dj)) or [])
    return out


def _find_variants(
    nkey: str,
    province: str,
    territory: str,
    lat: float | None,
    lon: float | None,
    province_admins: list[dict[str, Any]],
    *,
    name_buckets: dict[str, list[dict[str, Any]]] | None = None,
    geo_grid: dict[tuple[int, int], list[dict[str, Any]]] | None = None,
) -> list[tuple[float, dict[str, Any], list[str]]]:
    """Candidats variantes (même contexte) — jamais fusion sur nom seul.

    Optimisation : fuzzy limité au bucket territoire+initiale (+ voisins géo).
    """
    candidates: list[dict[str, Any]] = []
    seen: set[str] = set()

    def _add(items: list[dict[str, Any]]) -> None:
        for a in items:
            aid = str(a.get("admin_id") or id(a))
            if aid in seen:
                continue
            seen.add(aid)
            candidates.append(a)

    # Pool restreint : même territoire (exact/partiel) + voisins géo (fuzzy autorisé)
    if name_buckets is not None and nkey and territory:
        terr = territory
        _add(name_buckets.get(f"{terr}|{nkey[0]}") or [])
        # Exact/partiel sur tout le territoire sans fuzzy coûteux
        for a in name_buckets.get(f"{terr}|*") or []:
            akey = lc._norm(a.get("nom"))
            if akey == nkey or nkey in akey or akey in nkey:
                _add([a])
    elif name_buckets is not None and nkey:
        _add(name_buckets.get(f"_|{nkey[0]}") or [])

    geo_candidates: list[dict[str, Any]] = []
    if lat is not None and lon is not None and geo_grid is not None:
        geo_candidates = _grid_neighbors(geo_grid, lat, lon, ring=2)
        _add(geo_candidates)

    scored: list[tuple[float, dict[str, Any], list[str]]] = []
    for a in candidates:
        akey = lc._norm(a.get("nom"))
        if not akey:
            continue
        a_terr = lc._norm(a.get("territoire"))
        terr_ok = bool(territory and a_terr and territory == a_terr)
        geo_ok = False
        if lat is not None and lon is not None:
            try:
                d = lc.haversine_m(lat, lon, float(a["latitude"]), float(a["longitude"]))
                if d <= THRESHOLDS["geo_variant_m"]:
                    geo_ok = True
            except (TypeError, ValueError, KeyError):
                pass
        # Variante = similarité nom + (territoire OU géo) — jamais nom seul
        if not (terr_ok or geo_ok):
            continue

        if akey == nkey:
            ratio = 1.0
            evidence = ["NORMALIZED_NAME_EXACT"]
        elif nkey in akey or akey in nkey:
            ratio = max(0.8, _name_ratio(nkey, akey))
            evidence = ["NORMALIZED_NAME_PARTIAL"]
        elif geo_ok:
            # Fuzzy uniquement pour voisins géographiques proches
            if abs(len(akey) - len(nkey)) > max(3, int(0.35 * len(nkey))):
                continue
            ratio = _name_ratio(nkey, akey)
            if ratio < THRESHOLDS["variant_name_ratio"]:
                continue
            evidence = ["NORMALIZED_NAME_FUZZY"]
        else:
            # Même territoire sans exact/partiel : fuzzy léger
            if abs(len(akey) - len(nkey)) > max(2, int(0.25 * len(nkey))):
                continue
            ratio = _name_ratio(nkey, akey)
            if ratio < THRESHOLDS["variant_name_ratio"]:
                continue
            evidence = ["NORMALIZED_NAME_FUZZY"]

        if terr_ok:
            evidence.append("TERRITORY_MATCH")
        if geo_ok:
            evidence.append("GEOGRAPHIC_NEAR")
        score = ratio + (0.1 if terr_ok else 0.0) + (0.1 if geo_ok else 0.0)
        scored.append((score, a, evidence))
    scored.sort(key=lambda x: -x[0])
    return scored[:5]


def classify_enrichment_observation(
    obs: dict[str, Any],
    *,
    is_duplicate_extra: bool,
    admin_by_name: dict[str, list[dict[str, Any]]],
    admin_by_province: dict[str, list[dict[str, Any]]],
    province_bboxes: dict[str, tuple[float, float, float, float]],
    province_name_buckets: dict[str, dict[str, list[dict[str, Any]]]] | None = None,
    province_geo_grids: dict[str, dict[tuple[int, int], list[dict[str, Any]]]] | None = None,
) -> dict[str, Any]:
    """Classifie une observation / identité pour l'enrichissement (pas d'écriture)."""
    proofs: list[str] = []
    toponym = obs.get("toponym") or lc._nci_toponym(obs)
    nkey = lc._norm(toponym)
    province = lc._norm(obs.get("province"))
    territory = lc._norm(obs.get("territoire"))
    has_name = _exploitable_name(toponym)
    has_coords = _valid_coords(obs)
    lat = lon = None
    if has_coords:
        lat, lon = float(obs["latitude"]), float(obs["longitude"])

    review_status = "audit_only"

    if is_duplicate_extra:
        return {
            "enrichment_class": "DUPLICATE_NCI_OBSERVATION",
            "confidence": "high",
            "score": 1.0,
            "proofs": ["SAME_IDENTITY_KEY_REPEATED_IN_NCI"],
            "reason_unmatched": obs.get("coverage_classification") or "duplicate_nci",
            "review_status": review_status,
            "candidate_admin_id": None,
            "candidate_admin_name": None,
        }

    if not has_name or not province:
        return {
            "enrichment_class": "UNRESOLVED_LOCALITY",
            "confidence": "low",
            "score": 0.0,
            "proofs": (["MISSING_EXPLOITABLE_NAME"] if not has_name else [])
            + (["MISSING_PROVINCE"] if not province else []),
            "reason_unmatched": "insufficient_identity_fields",
            "review_status": "needs_data",
            "candidate_admin_id": None,
            "candidate_admin_name": None,
        }

    province_admins = admin_by_province.get(province) or []
    buckets = (province_name_buckets or {}).get(province)
    grid = (province_geo_grids or {}).get(province)
    variants = _find_variants(
        nkey,
        province,
        territory,
        lat,
        lon,
        province_admins,
        name_buckets=buckets,
        geo_grid=grid,
    )
    if variants:
        best_score, best_admin, evidence = variants[0]
        if len(variants) > 1:
            gap = best_score - variants[1][0]
            if gap < THRESHOLDS["ambiguous_variant_gap"]:
                return {
                    "enrichment_class": "AMBIGUOUS_LOCALITY",
                    "confidence": "medium",
                    "score": round(best_score, 4),
                    "proofs": evidence + ["MULTIPLE_VARIANT_CANDIDATES"],
                    "reason_unmatched": "ambiguous_existing_variant",
                    "review_status": "human_review",
                    "candidate_admin_id": best_admin.get("admin_id"),
                    "candidate_admin_name": best_admin.get("nom"),
                }
        return {
            "enrichment_class": "EXISTING_LOCALITY_VARIANT",
            "confidence": "high" if best_score >= 1.0 else "medium",
            "score": round(best_score, 4),
            "proofs": evidence + ["SAME_PROVINCE_CONTEXT"],
            "reason_unmatched": "orthographic_or_source_variant_of_existing",
            "review_status": "no_enrichment_needed",
            "candidate_admin_id": best_admin.get("admin_id"),
            "candidate_admin_name": best_admin.get("nom"),
        }

    # Homonyme : même nom normalisé ailleurs, pas dans le même contexte
    same_name_elsewhere = []
    for a in admin_by_name.get(nkey) or []:
        a_prov = lc._norm(a.get("province"))
        a_terr = lc._norm(a.get("territoire"))
        if a_prov == province and (not territory or not a_terr or a_terr == territory):
            continue  # même contexte — déjà traité via variantes exactes
        same_name_elsewhere.append(a)
    if same_name_elsewhere:
        proofs = ["HOMONYM_NAME_EXISTS_ELSEWHERE"]
        if any(lc._norm(a.get("province")) != province for a in same_name_elsewhere):
            proofs.append("PROVINCE_CONTEXT_DIFFERENT")
        if any(lc._norm(a.get("territoire")) != territory for a in same_name_elsewhere):
            proofs.append("TERRITORY_CONTEXT_DIFFERENT")
        return {
            "enrichment_class": "HOMONYM_DIFFERENT_LOCALITY",
            "confidence": "high",
            "score": 0.7,
            "proofs": proofs,
            "reason_unmatched": "homonym_different_admin_context",
            "review_status": "human_review_homonym",
            "candidate_admin_id": same_name_elsewhere[0].get("admin_id"),
            "candidate_admin_name": same_name_elsewhere[0].get("nom"),
        }

    # Nouvelle localité potentielle — prudence : pas tout UNMATCHED → HIGH_CONFIDENCE
    # Distance inter-localités : jamais utilisée seule pour accepter/rejeter.
    proofs = ["NO_RELIABLE_ADMIN_MATCH", "NAME_ABSENT_SAME_CONTEXT", "DISTANCE_NOT_USED_AS_IDENTITY_RULE"]
    if has_name:
        proofs.append("EXPLOITABLE_NAME")
    if has_coords:
        proofs.append("VALID_COORDINATES")
    if province:
        proofs.append("PROVINCE_IDENTIFIED")
    if territory:
        proofs.append("TERRITORY_IDENTIFIED")

    in_bbox = False
    if has_coords and lat is not None and lon is not None:
        in_bbox = _in_bbox(lat, lon, province_bboxes.get(province))
        if in_bbox:
            proofs.append("GEOMETRY_IN_PROVINCE_BBOX")
        else:
            proofs.append("GEOMETRY_OUTSIDE_PROVINCE_BBOX")

    name_long_enough = len(nkey) >= THRESHOLDS["min_name_len"]
    # Partial/exact dans le même territoire → plutôt variante (déjà couverte) ou revue
    province_name_hits = 0
    for a in admin_by_name.get(nkey) or []:
        if lc._norm(a.get("province")) == province:
            province_name_hits += 1
            break
    if province_name_hits == 0 and territory and buckets is not None and len(nkey) >= 4:
        for a in buckets.get(f"{territory}|*") or []:
            akey = lc._norm(a.get("nom"))
            if akey and akey != nkey and (nkey in akey or akey in nkey):
                province_name_hits += 1
                break
    if province_name_hits:
        proofs.append("PARTIAL_NAME_PRESENT_IN_PROVINCE")

    strong = (
        has_name
        and name_long_enough
        and has_coords
        and bool(province)
        and bool(territory)
        and in_bbox
        and province_name_hits == 0
    )
    if strong:
        return {
            "enrichment_class": "NEW_LOCALITY_CANDIDATE_HIGH_CONFIDENCE",
            "confidence": "high",
            "score": 0.85,
            "proofs": proofs + ["MULTI_EVIDENCE_COHERENT"],
            "reason_unmatched": "absent_from_admin_referential_with_coherent_context",
            "review_status": "candidate_pending_validation",
            "candidate_admin_id": None,
            "candidate_admin_name": None,
        }

    if has_name and has_coords and province:
        return {
            "enrichment_class": "NEW_LOCALITY_CANDIDATE_REVIEW",
            "confidence": "medium",
            "score": 0.55,
            "proofs": proofs + ["PARTIAL_EVIDENCE"],
            "reason_unmatched": "potential_new_needs_human_validation",
            "review_status": "human_review",
            "candidate_admin_id": None,
            "candidate_admin_name": None,
        }

    return {
        "enrichment_class": "UNRESOLVED_LOCALITY",
        "confidence": "low",
        "score": 0.1,
        "proofs": proofs or ["INSUFFICIENT_EVIDENCE"],
        "reason_unmatched": "insufficient_evidence",
        "review_status": "needs_data",
        "candidate_admin_id": None,
        "candidate_admin_name": None,
    }


def run_enrichment_audit(
    *,
    coverage_rows: list[dict[str, Any]] | None = None,
    covered_rows: list[dict[str, Any]] | None = None,
    uncovered_rows: list[dict[str, Any]] | None = None,
    admin_rows: list[dict[str, Any]] | None = None,
    run_coverage_if_needed: bool = True,
    write_cache: bool = False,
) -> EnrichmentAuditState:
    """Exécute l'audit d'enrichissement (lecture seule, aucune création référentiel)."""
    started = time.time()
    admin = admin_rows if admin_rows is not None else lc._load_admin_localities()

    if coverage_rows is None:
        if run_coverage_if_needed:
            cov_state = lc.run_locality_coverage(
                covered_rows=covered_rows,
                uncovered_rows=uncovered_rows,
                admin_rows=admin,
                write_cache=False,
            )
            coverage_rows = cov_state.rows
        else:
            coverage_rows = []

    # Index admin
    admin_by_name: dict[str, list[dict[str, Any]]] = defaultdict(list)
    admin_by_province: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for a in admin:
        nk = lc._norm(a.get("nom"))
        if nk:
            admin_by_name[nk].append(a)
        pk = lc._norm(a.get("province"))
        if pk:
            admin_by_province[pk].append(a)
    province_bboxes = _province_bboxes(admin)
    province_name_buckets = {pk: _name_buckets(rows) for pk, rows in admin_by_province.items()}
    province_geo_grids = {pk: _geo_grid(rows) for pk, rows in admin_by_province.items()}

    covered = covered_rows if covered_rows is not None else lc._load_jsonl(lc.COVERAGE_DIR / "localities_covered.jsonl")
    uncovered = (
        uncovered_rows
        if uncovered_rows is not None
        else lc._load_jsonl(lc.COVERAGE_DIR / "localities_uncovered.jsonl")
    )
    nci_by_id: dict[str, dict[str, Any]] = {str(row.get("id")): row for row in covered + uncovered}

    def _hydrate(r: dict[str, Any]) -> dict[str, Any]:
        src = nci_by_id.get(str(r.get("nci_id") or r.get("id") or ""))
        out = dict(r)
        if src:
            for key in (
                "latitude",
                "longitude",
                "destination",
                "name",
                "population",
                "project",
                "dataset",
                "province",
                "territoire",
            ):
                if out.get(key) in (None, "") and src.get(key) is not None:
                    out[key] = src.get(key)
            out.setdefault("nci_id", src.get("id"))
        out["toponym"] = out.get("toponym") or lc._nci_toponym(out)
        out["coverage_classification"] = out.get("classification") or out.get("coverage_classification")
        return out

    # Scope : non appariés + dual-source revue (covered absorbés inclus)
    in_scope = [_hydrate(r) for r in coverage_rows if r.get("classification") in IN_SCOPE_COVERAGE]
    unmatched_uncovered = [r for r in in_scope if r.get("classification") == "UNMATCHED_UNCOVERED"]
    covered_non_canonical = [
        r
        for r in in_scope
        if r.get("coverage_status") == "covered"
        or (r.get("dual_source_observation") and r.get("classification") == "COVERAGE_STATUS_REQUIRES_REVIEW")
    ]

    # Funnel prioritaire UNMATCHED_UNCOVERED
    funnel: dict[str, Any] = {
        "unmatched_uncovered_start": len(unmatched_uncovered),
        "name_exploitable": 0,
        "coords_valid": 0,
        "province_identifiable": 0,
        "territoire_identifiable": 0,
        "admin_context_sufficient": 0,
        "probable_existing_variants": 0,
        "nci_duplicates": 0,
        "homonyms": 0,
        "high_confidence_candidates": 0,
        "review_candidates": 0,
        "unresolved": 0,
        "ambiguous": 0,
        "principal_unmatched_cause": None,
    }

    # Grouper par identité canonique APRÈS hydratation (covered+uncovered = une localité)
    hydrated_groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for h in in_scope:
        hydrated_groups[identity_key(h)].append(h)

    results: list[dict[str, Any]] = []
    class_counts: Counter[str] = Counter()
    identity_class_counts: Counter[str] = Counter()
    population_by_class: Counter[str] = Counter()

    for ident, rows in hydrated_groups.items():
        # Prefer uncovered as primary representative when dual-source
        rows_sorted = sorted(
            rows,
            key=lambda x: (0 if x.get("coverage_status") == "uncovered" else 1, str(x.get("nci_id") or "")),
        )
        primary = rows_sorted[0]
        observation_ids = [str(r.get("nci_id")) for r in rows_sorted if r.get("nci_id")]
        coverage_statuses = sorted({str(r.get("coverage_status")) for r in rows_sorted})

        for idx, obs in enumerate(rows_sorted):
            is_extra = idx > 0
            decision = classify_enrichment_observation(
                obs,
                is_duplicate_extra=is_extra,
                admin_by_name=admin_by_name,
                admin_by_province=admin_by_province,
                province_bboxes=province_bboxes,
                province_name_buckets=province_name_buckets,
                province_geo_grids=province_geo_grids,
            )
            # Pour les extras : toujours DUPLICATE ; pour primary on garde la décision
            if is_extra:
                decision = {
                    "enrichment_class": "DUPLICATE_NCI_OBSERVATION",
                    "confidence": "high",
                    "score": 1.0,
                    "proofs": ["SAME_CANONICAL_IDENTITY_MULTIPLE_OBSERVATIONS"],
                    "reason_unmatched": "duplicate_nci_observation",
                    "review_status": "no_new_locality",
                    "candidate_admin_id": None,
                    "candidate_admin_name": None,
                }

            ecl = decision["enrichment_class"]
            class_counts[ecl] += 1
            if not is_extra:
                identity_class_counts[ecl] += 1
                try:
                    population_by_class[ecl] += int(obs.get("population") or 0)
                except (TypeError, ValueError):
                    pass

            record = {
                "nci_id": obs.get("nci_id"),
                "identity_key": ident,
                "is_canonical_representative": not is_extra,
                "observation_ids": observation_ids,
                "coverage_statuses": coverage_statuses,
                "coverage_classification": obs.get("coverage_classification"),
                "dual_source_observation": bool(obs.get("dual_source_observation")),
                "source": obs.get("dataset") or obs.get("coverage_status"),
                "source_id": obs.get("nci_id"),
                "toponym": obs.get("toponym"),
                "nci_destination": obs.get("nci_destination") or obs.get("destination"),
                "nci_name": obs.get("nci_name") or obs.get("name"),
                "nom_normalise": lc._norm(obs.get("toponym")),
                "province": obs.get("province"),
                "territoire": obs.get("territoire"),
                "collectivite": obs.get("collectivite"),
                "groupement": obs.get("groupement"),
                "latitude": obs.get("latitude"),
                "longitude": obs.get("longitude"),
                "population": obs.get("population"),
                "project": obs.get("project"),
                "enrichment_class": ecl,
                "classification": ecl,
                "confidence": decision["confidence"],
                "score": decision["score"],
                "proofs": decision["proofs"],
                "evidence": decision["proofs"],
                "reason_unmatched": decision["reason_unmatched"],
                "review_status": decision["review_status"],
                "candidate_admin_id": decision["candidate_admin_id"],
                "candidate_admin_name": decision["candidate_admin_name"],
                "future_canonical_id": future_canonical_id(obs) if ecl.startswith("NEW_LOCALITY") else None,
                "auto_created": False,
            }
            results.append(record)

    # Funnel UNMATCHED_UNCOVERED (observations, puis classes sur représentants de ce sous-ensemble)
    uu_ids = {str(r.get("nci_id")) for r in unmatched_uncovered}
    uu_results = [r for r in results if str(r.get("nci_id")) in uu_ids]
    uu_primary = [r for r in uu_results if r.get("is_canonical_representative")]

    for r in unmatched_uncovered:
        h = _hydrate(r)
        if _exploitable_name(h.get("toponym") or ""):
            funnel["name_exploitable"] += 1
        if _valid_coords(h):
            funnel["coords_valid"] += 1
        if lc._norm(h.get("province")):
            funnel["province_identifiable"] += 1
        if lc._norm(h.get("territoire")):
            funnel["territoire_identifiable"] += 1
        if (
            _exploitable_name(h.get("toponym") or "")
            and lc._norm(h.get("province"))
            and lc._norm(h.get("territoire"))
        ):
            funnel["admin_context_sufficient"] += 1

    for r in uu_primary:
        ecl = r["enrichment_class"]
        if ecl == "EXISTING_LOCALITY_VARIANT":
            funnel["probable_existing_variants"] += 1
        elif ecl == "DUPLICATE_NCI_OBSERVATION":
            funnel["nci_duplicates"] += 1
        elif ecl == "HOMONYM_DIFFERENT_LOCALITY":
            funnel["homonyms"] += 1
        elif ecl == "NEW_LOCALITY_CANDIDATE_HIGH_CONFIDENCE":
            funnel["high_confidence_candidates"] += 1
        elif ecl == "NEW_LOCALITY_CANDIDATE_REVIEW":
            funnel["review_candidates"] += 1
        elif ecl == "UNRESOLVED_LOCALITY":
            funnel["unresolved"] += 1
        elif ecl == "AMBIGUOUS_LOCALITY":
            funnel["ambiguous"] += 1
    funnel["nci_duplicate_observations"] = sum(
        1 for r in uu_results if r["enrichment_class"] == "DUPLICATE_NCI_OBSERVATION"
    )

    # Cause principale : parmi UU primary, répartition des reason_unmatched
    reason_counter = Counter(r.get("reason_unmatched") for r in uu_primary)
    funnel["principal_unmatched_cause"] = (
        reason_counter.most_common(1)[0][0] if reason_counter else None
    )
    funnel["reason_breakdown"] = dict(reason_counter)

    high_conf_ids = identity_class_counts.get("NEW_LOCALITY_CANDIDATE_HIGH_CONFIDENCE", 0)
    review_ids = identity_class_counts.get("NEW_LOCALITY_CANDIDATE_REVIEW", 0)
    admin_count = len(admin)
    potential_enriched = admin_count + high_conf_ids

    # Impact appariement potentiel (préparatoire) :
    # si high-conf étaient ajoutées et re-matchées exact → matched += high_conf covered by those identities
    matched_now = sum(
        1
        for r in coverage_rows
        if r.get("classification") in {"MATCHED_LOCALITY", "PROBABLE_MATCH"}
    )
    nci_obs = len(coverage_rows)
    high_conf_identity_keys = {
        r["identity_key"]
        for r in results
        if r.get("is_canonical_representative")
        and r.get("enrichment_class") == "NEW_LOCALITY_CANDIDATE_HIGH_CONFIDENCE"
    }
    high_conf_obs = sum(1 for r in results if r.get("identity_key") in high_conf_identity_keys)
    potential_match_rate = round((matched_now + high_conf_obs) / nci_obs, 4) if nci_obs else 0.0

    unique_nci_identities = len({identity_key(_hydrate(r)) for r in coverage_rows}) if coverage_rows else 0

    covered_audit = [
        r
        for r in results
        if "covered" in (r.get("coverage_statuses") or [])
        and r.get("is_canonical_representative")
    ]
    covered_new_high = sum(
        1 for r in covered_audit if r["enrichment_class"] == "NEW_LOCALITY_CANDIDATE_HIGH_CONFIDENCE"
    )
    covered_new_review = sum(
        1 for r in covered_audit if r["enrichment_class"] == "NEW_LOCALITY_CANDIDATE_REVIEW"
    )

    kpis = {
        "admin_localities_current": admin_count,
        "admin_source": {
            "table_or_file": "data/reports/locality_official/locality_referential_official.json",
            "authoritative": True,
            "identifier": "canonical_id",
            "fields": [
                "canonical_id",
                "nom",
                "province",
                "territoire",
                "collectivite",
                "groupement",
                "geometry",
                "provenance",
            ],
            "provenance_default": "Localités.kmz",
            "count": admin_count,
            "modified_during_audit": False,
        },
        "nci_unique_identities_estimated": unique_nci_identities,
        "in_scope_observations": len(in_scope),
        "unmatched_uncovered_observations": len(unmatched_uncovered),
        "covered_non_canonical_audited": len(covered_non_canonical),
        "by_enrichment_class_observations": {c: class_counts.get(c, 0) for c in ENRICHMENT_CLASSES},
        "by_enrichment_class_identities": {c: identity_class_counts.get(c, 0) for c in ENRICHMENT_CLASSES},
        "EXISTING_LOCALITY_VARIANT": identity_class_counts.get("EXISTING_LOCALITY_VARIANT", 0),
        "DUPLICATE_NCI_OBSERVATION": class_counts.get("DUPLICATE_NCI_OBSERVATION", 0),
        "HOMONYM_DIFFERENT_LOCALITY": identity_class_counts.get("HOMONYM_DIFFERENT_LOCALITY", 0),
        "AMBIGUOUS_LOCALITY": identity_class_counts.get("AMBIGUOUS_LOCALITY", 0),
        "NEW_LOCALITY_CANDIDATE_HIGH_CONFIDENCE": high_conf_ids,
        "NEW_LOCALITY_CANDIDATE_REVIEW": review_ids,
        "UNRESOLVED_LOCALITY": identity_class_counts.get("UNRESOLVED_LOCALITY", 0),
        "POTENTIAL_ENRICHED_LOCALITY_COUNT": potential_enriched,
        "potential_match_rate_if_high_conf_integrated": potential_match_rate,
        "current_match_rate_reference": round(matched_now / nci_obs, 4) if nci_obs else 0.0,
        "population_attachable_high_confidence": population_by_class.get(
            "NEW_LOCALITY_CANDIDATE_HIGH_CONFIDENCE", 0
        ),
        "population_attachable_review": population_by_class.get("NEW_LOCALITY_CANDIDATE_REVIEW", 0),
        "covered_absorbed_new_high_confidence": covered_new_high,
        "covered_absorbed_new_review": covered_new_review,
        "referential_not_modified": True,
        "auto_creation_disabled": True,
        "funnel_unmatched_uncovered": funnel,
    }

    kpis["nci_observations_raw"] = {
        "covered": len(covered),
        "uncovered": len(uncovered),
        "total": len(covered) + len(uncovered),
        "note": "Observations source — ≠ localités uniques",
    }

    integration_method = describe_integration_method()
    integration_method["sample_blueprints"] = [
        build_integration_blueprint(r)
        for r in results
        if r.get("is_canonical_representative")
        and r.get("enrichment_class") == "NEW_LOCALITY_CANDIDATE_HIGH_CONFIDENCE"
    ][:5]

    state = EnrichmentAuditState(
        executed=True,
        message=(
            "Audit enrichissement localités exécuté (lecture seule) — "
            "aucune intégration référentiel."
        ),
        meta={
            "engine": ENGINE_VERSION,
            "generated_at": _now(),
            "thresholds": THRESHOLDS,
            "classes": list(ENRICHMENT_CLASSES),
            "in_scope_coverage_classes": sorted(IN_SCOPE_COVERAGE),
        },
        kpis=kpis,
        rows=results,
        funnel=funnel,
        integration_method=integration_method,
        performance={"elapsed_ms": round((time.time() - started) * 1000, 1)},
    )

    global _STATE
    _STATE = state

    if write_cache:
        cache = lc.ROOT / "data" / "cache" / "nire_locality_enrichment_audit_v1.json"
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(
            json.dumps(
                {
                    "meta": state.meta,
                    "kpis": state.kpis,
                    "funnel": state.funnel,
                    "integration_method": {
                        k: v
                        for k, v in state.integration_method.items()
                        if k != "sample_blueprints"
                    },
                    "sample_high_confidence": [
                        r
                        for r in state.rows
                        if r.get("enrichment_class") == "NEW_LOCALITY_CANDIDATE_HIGH_CONFIDENCE"
                        and r.get("is_canonical_representative")
                    ][:30],
                    "note": "Derived cache — sources immuables — referential not modified",
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
    return state


def status_payload() -> dict[str, Any]:
    st = get_state()
    if not st.executed:
        return {
            "executed": False,
            "message": "Aucun audit enrichissement — POST /api/nire/locality-enrichment/run",
            "engine": ENGINE_VERSION,
        }
    return {
        "executed": True,
        "message": st.message,
        "meta": st.meta,
        "kpis": st.kpis,
        "funnel": st.funnel,
        "performance": st.performance,
        "referential_not_modified": True,
    }


def summary_payload() -> dict[str, Any]:
    st = get_state()
    if not st.executed:
        return status_payload()
    return {
        "executed": True,
        "kpis": st.kpis,
        "funnel": st.funnel,
        "integration_method": st.integration_method,
        "meta": st.meta,
        "module_impact_notes": {
            "cartographie": "Nouvelles localités apparaîtraient après intégration validée uniquement",
            "referentiel_hierarchique": "Attachement province/territoire/collectivité à valider",
            "nire": "Statut NIRE pending_human_validation puis matched",
            "nsme": "Relations spatiales sites↔localités élargies après intégration",
            "sdg": "Graphe relations localité enrichi — pas d'activation pendant audit",
            "intelligence_territoriale": "Population rattachable potentielle documentée, non recalculée KPI",
            "centre_decision": "Pas de nouveau score tant que non validé",
            "population_coverage_kpi": "Ne pas recalculer artificiellement les KPI nationaux",
        },
    }


def list_rows(
    *,
    enrichment_class: str | None = None,
    offset: int = 0,
    limit: int = 50,
) -> dict[str, Any]:
    st = get_state()
    rows = st.rows
    if enrichment_class:
        rows = [r for r in rows if r.get("enrichment_class") == enrichment_class]
    return {
        "total": len(rows),
        "offset": offset,
        "limit": limit,
        "rows": rows[offset : offset + limit],
        "classes": ENRICHMENT_CLASSES,
    }
