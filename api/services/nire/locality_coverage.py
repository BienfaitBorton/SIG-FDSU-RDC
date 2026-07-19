"""NIRE Localités — rapprochement NCI ↔ référentiel administratif (lecture seule).

Ne force pas l'égalité des univers (26 710 admin ≠ 29 568 observations NCI).
Ne modifie aucune source brute ni jsonl.
"""

from __future__ import annotations

import json
import math
import re
import time
import unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ENGINE_VERSION = "nire-locality-coverage-1.0.0"
ROOT = Path(__file__).resolve().parents[3]
COVERAGE_DIR = ROOT / "data" / "coverage"
ADMIN_JSON = ROOT / "data" / "reports" / "locality_official" / "locality_referential_official.json"
CACHE_PATH = ROOT / "data" / "cache" / "nire_locality_coverage_v1.json"

CLASSIFICATIONS = (
    "MATCHED_LOCALITY",
    "PROBABLE_MATCH",
    "AMBIGUOUS_LOCALITY",
    "UNMATCHED_COVERED",
    "UNMATCHED_UNCOVERED",
    "DUPLICATE_LOCALITY",
    # Dual observation covered+uncovered — pas une contradiction métier prouvée
    "COVERAGE_STATUS_REQUIRES_REVIEW",
    # Conservé pour compatibilité / cas réellement contradictoires (non utilisé par défaut)
    "CONFLICTING_COVERAGE_STATUS",
)

# Sémantique NCI (deux fichiers Excel indépendants, pas un booléen exclusif) :
# - covered  = observation du fichier « Population coverage »
# - uncovered = observation du fichier « Localités non couvertes »
# Statut = par observation / source fichier, PAS global ni par opérateur/techno.
COVERAGE_SEMANTICS = {
    "covered_dataset": "population_coverage",
    "uncovered_dataset": "localities_uncovered",
    "status_scope": "per_source_observation",
    "not_global_binary": True,
    "not_per_operator": True,
    "not_per_technology": True,
    "dual_list_overlap_is_not_automatic_contradiction": True,
}

THRESHOLDS = {
    "matched_min": 0.85,
    "probable_min": 0.65,
    "ambiguous_gap": 0.08,
    "geo_exact_m": 250.0,
    "geo_near_m": 1500.0,
}


@dataclass
class LocalityCoverageState:
    executed: bool = False
    message: str = ""
    meta: dict[str, Any] = field(default_factory=dict)
    kpis: dict[str, Any] = field(default_factory=dict)
    rows: list[dict[str, Any]] = field(default_factory=list)
    conflicts: list[dict[str, Any]] = field(default_factory=list)
    performance: dict[str, Any] = field(default_factory=dict)


_STATE = LocalityCoverageState()


def get_state() -> LocalityCoverageState:
    return _STATE


def reset_state() -> None:
    global _STATE
    _STATE = LocalityCoverageState()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _norm(text: str | None) -> str:
    s = (text or "").strip().lower()
    s = "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))
    s = re.sub(r"[^a-z0-9]+", " ", s).strip()
    return s


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * r * math.asin(min(1.0, math.sqrt(a)))


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def _load_admin_localities() -> list[dict[str, Any]]:
    """Préférer JSON officiel (+ enrichissement NCI) ; fallback PostGIS si disponible."""
    try:
        from api.services.nire import locality_controlled_integration as lci

        items = lci.load_national_locality_items(include_enrichment=True)
        if items:
            return lci._admin_from_items(items)
    except Exception:
        pass

    if ADMIN_JSON.exists():
        doc = json.loads(ADMIN_JSON.read_text(encoding="utf-8"))
        items = doc.get("locality_referential") or doc.get("localites") or doc.get("items") or []
        out = []
        for item in items:
            hierarchy = item.get("hierarchy") or item.get("administrative_attachment") or {}
            geom = item.get("geometry") or {}
            coords = geom.get("coordinates") if isinstance(geom, dict) else None
            lon = lat = None
            if isinstance(coords, (list, tuple)) and len(coords) >= 2:
                lon, lat = coords[0], coords[1]
            meta = item.get("metadata") or {}
            ext = meta.get("extended_data") if isinstance(meta, dict) else {}
            if not isinstance(ext, dict):
                ext = {}
            # Clés accentuées possibles selon encodage JSON
            collectivite = (
                item.get("collectivité")
                or item.get("collectivite")
                or hierarchy.get("collectivité")
                or hierarchy.get("collectivite")
                or ext.get("COLLECTIV")
                or ""
            )
            groupement = item.get("groupement") or hierarchy.get("groupement") or ""
            provenance = item.get("source") or meta.get("source_file") or "Localités.kmz"
            out.append(
                {
                    "admin_id": item.get("canonical_id") or item.get("id") or item.get("code"),
                    "nom": item.get("nom") or item.get("name"),
                    "province": hierarchy.get("province") or item.get("province"),
                    "territoire": hierarchy.get("territoire") or hierarchy.get("territory") or item.get("territoire"),
                    "collectivite": collectivite,
                    "groupement": groupement,
                    "latitude": lat if lat is not None else item.get("latitude"),
                    "longitude": lon if lon is not None else item.get("longitude"),
                    "source": "locality_referential_official.json",
                    "provenance": provenance,
                    "statut": item.get("statut"),
                }
            )
        if out:
            return out

    try:
        from api.config import connect_db, use_database
        from psycopg2.extras import RealDictCursor

        if not use_database():
            return []
        with connect_db() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT l.id, l.code, l.nom, l.latitude, l.longitude,
                           t.nom AS territoire, p.nom AS province
                    FROM localites l
                    LEFT JOIN groupements g ON g.id = l.parent_id
                    LEFT JOIN collectivites c ON c.id = g.parent_id
                    LEFT JOIN territoires t ON t.id = c.parent_id
                    LEFT JOIN provinces p ON p.id = t.parent_id
                    """
                )
                return [
                    {
                        "admin_id": r.get("code") or r.get("id"),
                        "nom": r.get("nom"),
                        "province": r.get("province"),
                        "territoire": r.get("territoire"),
                        "latitude": r.get("latitude"),
                        "longitude": r.get("longitude"),
                        "source": "public.localites",
                    }
                    for r in cur.fetchall()
                ]
    except Exception:
        return []


def _nci_toponym(row: dict[str, Any]) -> str:
    dest = str(row.get("destination") or "").strip()
    name = str(row.get("name") or "").strip()
    # Prefer human destination; fall back to name when alphabetic
    if dest and re.search(r"[A-Za-zÀ-ÿ]", dest):
        return dest
    if name and re.search(r"[A-Za-zÀ-ÿ]", name):
        return name
    return dest or name


def _score_pair(nci: dict[str, Any], admin: dict[str, Any]) -> tuple[float, list[str]]:
    evidence: list[str] = []
    score = 0.0
    n_name = _norm(_nci_toponym(nci))
    a_name = _norm(admin.get("nom"))
    if not n_name or not a_name:
        return 0.0, evidence

    n_prov, a_prov = _norm(nci.get("province")), _norm(admin.get("province"))
    # Homonymes inter-provinces : jamais fusionnés
    if n_prov and a_prov and n_prov != a_prov:
        return 0.0, ["PROVINCE_MISMATCH_BLOCKED"]

    n_terr, a_terr = _norm(nci.get("territoire")), _norm(admin.get("territoire"))
    if n_prov and a_prov and n_terr and a_terr and n_terr != a_terr:
        # Même province, territoires différents → candidat rejeté (homonyme territorial)
        return 0.0, ["TERRITORY_MISMATCH_BLOCKED"]

    if n_name == a_name:
        score += 0.55
        evidence.append("NORMALIZED_NAME_EXACT")
    elif n_name in a_name or a_name in n_name:
        score += 0.35
        evidence.append("NORMALIZED_NAME_PARTIAL")
    else:
        return 0.0, evidence

    if n_prov and a_prov and n_prov == a_prov:
        score += 0.2
        evidence.append("PROVINCE_MATCH")
    if n_terr and a_terr and n_terr == a_terr:
        score += 0.15
        evidence.append("TERRITORY_MATCH")

    try:
        nlat, nlon = float(nci["latitude"]), float(nci["longitude"])
        alat, alon = float(admin["latitude"]), float(admin["longitude"])
        dist = haversine_m(nlat, nlon, alat, alon)
        if dist <= THRESHOLDS["geo_exact_m"]:
            score += 0.25
            evidence.append("GEOGRAPHIC_NEAR_EXACT")
        elif dist <= THRESHOLDS["geo_near_m"]:
            score += 0.12
            evidence.append("GEOGRAPHIC_NEAR")
    except (TypeError, ValueError, KeyError):
        pass

    # MATCHED exige au minimum un ancrage administratif (province) — pas le nom seul
    if score >= THRESHOLDS["matched_min"] and "PROVINCE_MATCH" not in evidence:
        score = min(score, THRESHOLDS["probable_min"] - 0.01)
        evidence.append("MATCHED_DOWNGRADED_NO_PROVINCE")

    return min(1.0, score), evidence


def _classify_match(
    coverage_status: str,
    candidates: list[tuple[float, dict[str, Any], list[str]]],
    *,
    is_duplicate: bool,
) -> str:
    if is_duplicate:
        return "DUPLICATE_LOCALITY"
    if not candidates:
        return "UNMATCHED_COVERED" if coverage_status == "covered" else "UNMATCHED_UNCOVERED"
    best_score, _, _ = candidates[0]
    if len(candidates) > 1:
        second = candidates[1][0]
        if best_score >= THRESHOLDS["probable_min"] and (best_score - second) < THRESHOLDS["ambiguous_gap"]:
            return "AMBIGUOUS_LOCALITY"
    if best_score >= THRESHOLDS["matched_min"]:
        return "MATCHED_LOCALITY"
    if best_score >= THRESHOLDS["probable_min"]:
        return "PROBABLE_MATCH"
    return "UNMATCHED_COVERED" if coverage_status == "covered" else "UNMATCHED_UNCOVERED"


def _apply_dual_source_policy(classification: str, *, dual_source: bool) -> str:
    """Chevauchement covered∩uncovered = revue neutre, pas contradiction automatique."""
    if not dual_source:
        return classification
    if classification in {"MATCHED_LOCALITY", "PROBABLE_MATCH", "AMBIGUOUS_LOCALITY", "DUPLICATE_LOCALITY"}:
        # Conserver le rapprochement admin ; le dual-source est signalé à part
        return classification
    # Sans match admin fiable → revue de statut de couverture (neutre)
    return "COVERAGE_STATUS_REQUIRES_REVIEW"


def run_locality_coverage(
    *,
    max_rows: int | None = None,
    write_cache: bool = False,
    covered_rows: list[dict[str, Any]] | None = None,
    uncovered_rows: list[dict[str, Any]] | None = None,
    admin_rows: list[dict[str, Any]] | None = None,
) -> LocalityCoverageState:
    started = time.time()
    covered = covered_rows if covered_rows is not None else _load_jsonl(COVERAGE_DIR / "localities_covered.jsonl")
    uncovered = (
        uncovered_rows if uncovered_rows is not None else _load_jsonl(COVERAGE_DIR / "localities_uncovered.jsonl")
    )
    admin = admin_rows if admin_rows is not None else _load_admin_localities()

    # Index admin by normalized name (+ province bucket)
    by_name: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for a in admin:
        key = _norm(a.get("nom"))
        if key:
            by_name[key].append(a)

    def _identity_key(row: dict[str, Any]) -> str:
        """Identité stricte : toponyme + admin + cellule géo ~100 m (évite homonymes seuls)."""
        try:
            geo = f"{round(float(row['latitude']), 3)}|{round(float(row['longitude']), 3)}"
        except (TypeError, ValueError, KeyError):
            geo = "nogeo"
        return "|".join(
            [
                _norm(_nci_toponym(row)),
                _norm(row.get("province")),
                _norm(row.get("territoire")),
                geo,
            ]
        )

    # Dual-source = même identité spatiale dans les deux fichiers (revue neutre, pas conflit auto)
    identity_map: dict[str, set[str]] = defaultdict(set)
    for row in covered + uncovered:
        ident = _identity_key(row)
        if ident.strip("|"):
            identity_map[ident].add(str(row.get("coverage_status") or "unknown"))

    dual_source_ids = {
        k for k, statuses in identity_map.items() if "covered" in statuses and "uncovered" in statuses
    }
    dual_source_rows: list[dict[str, Any]] = []

    def _dup_keys(rows: list[dict[str, Any]]) -> set[str]:
        counter: Counter[str] = Counter()
        for r in rows:
            key = str(r.get("id") or "") or "|".join(
                [_norm(_nci_toponym(r)), _norm(r.get("province")), _norm(r.get("territoire"))]
            )
            counter[key] += 1
        return {k for k, v in counter.items() if v > 1}

    dup_covered = _dup_keys(covered)
    dup_uncovered = _dup_keys(uncovered)

    # Funnel d’appariement (observations NCI)
    funnel = {
        "population_nci_observations": 0,
        "toponym_exploitable": 0,
        "province_identifiable": 0,
        "territoire_identifiable": 0,
        "coords_exploitable": 0,
        "name_hit_in_admin_index": 0,
        "exact_match": 0,
        "probable_match": 0,
        "ambiguous": 0,
        "unmatched": 0,
        "dual_source_observations": 0,
        "principal_unmatched_factor": None,
    }

    results: list[dict[str, Any]] = []
    streams = [("covered", covered), ("uncovered", uncovered)]
    for status, rows in streams:
        iterable = rows[:max_rows] if max_rows else rows
        for row in iterable:
            funnel["population_nci_observations"] += 1
            toponym = _nci_toponym(row)
            nkey = _norm(toponym)
            if nkey and re.search(r"[a-z]", nkey):
                funnel["toponym_exploitable"] += 1
            if _norm(row.get("province")):
                funnel["province_identifiable"] += 1
            if _norm(row.get("territoire")):
                funnel["territoire_identifiable"] += 1
            try:
                if row.get("coords_valid") or (
                    float(row["latitude"]) != 0 and float(row["longitude"]) != 0
                ):
                    funnel["coords_exploitable"] += 1
            except (TypeError, ValueError, KeyError):
                pass

            ident = _identity_key(row)
            dual_source = ident in dual_source_ids
            if dual_source:
                funnel["dual_source_observations"] += 1
            row_key = str(row.get("id") or "") or ident
            is_dup = row_key in (dup_covered if status == "covered" else dup_uncovered) or bool(
                row.get("duplicate")
            )

            # Candidats : même nom normalisé, province filtrée si disponible
            prov = _norm(row.get("province"))
            candidates_raw = []
            for cand in by_name.get(nkey) or []:
                cprov = _norm(cand.get("province"))
                if prov and cprov and prov != cprov:
                    continue
                candidates_raw.append(cand)
            if nkey and candidates_raw:
                funnel["name_hit_in_admin_index"] += 1

            scored: list[tuple[float, dict[str, Any], list[str]]] = []
            seen_admin: set[str] = set()
            for cand in candidates_raw:
                aid = str(cand.get("admin_id"))
                if aid in seen_admin:
                    continue
                seen_admin.add(aid)
                sc, evidence = _score_pair(row, cand)
                if sc > 0:
                    scored.append((sc, cand, evidence))
            scored.sort(key=lambda x: -x[0])
            top = scored[:5]
            base_class = _classify_match(status, top, is_duplicate=is_dup)
            classification = _apply_dual_source_policy(base_class, dual_source=dual_source)

            if classification == "MATCHED_LOCALITY":
                funnel["exact_match"] += 1
            elif classification == "PROBABLE_MATCH":
                funnel["probable_match"] += 1
            elif classification == "AMBIGUOUS_LOCALITY":
                funnel["ambiguous"] += 1
            elif classification in {
                "UNMATCHED_COVERED",
                "UNMATCHED_UNCOVERED",
                "COVERAGE_STATUS_REQUIRES_REVIEW",
            }:
                funnel["unmatched"] += 1

            best = top[0] if top else None
            result = {
                "nci_id": row.get("id"),
                "coverage_status": status,
                "dataset": row.get("dataset"),
                "project": row.get("project"),
                "nci_name": row.get("name"),
                "nci_destination": row.get("destination"),
                "toponym": toponym,
                "province": row.get("province"),
                "territoire": row.get("territoire"),
                "population": row.get("population"),
                "fdsu_zone": row.get("fdsu_zone"),
                "classification": classification,
                "base_classification": base_class,
                "dual_source_observation": dual_source,
                "score": round(best[0], 4) if best else None,
                "evidence": best[2] if best else [],
                "admin_id": (best[1].get("admin_id") if best else None),
                "admin_name": (best[1].get("nom") if best else None),
                "admin_province": (best[1].get("province") if best else None),
                "admin_territoire": (best[1].get("territoire") if best else None),
                "candidate_count": len(top),
                "requires_human_review": classification
                in {
                    "AMBIGUOUS_LOCALITY",
                    "PROBABLE_MATCH",
                    "COVERAGE_STATUS_REQUIRES_REVIEW",
                    "CONFLICTING_COVERAGE_STATUS",
                }
                or dual_source,
                "source_values": {
                    "name": row.get("name"),
                    "destination": row.get("destination"),
                    "coverage_status": status,
                    "population": row.get("population"),
                    "project": row.get("project"),
                    "dataset": row.get("dataset"),
                },
            }
            results.append(result)
            if dual_source:
                dual_source_rows.append(
                    {
                        "identity_key": ident,
                        "nci_id": row.get("id"),
                        "toponym": toponym,
                        "statuses": sorted(identity_map[ident]),
                        "projects": row.get("project"),
                        "note": "Observation présente dans les deux fichiers sources — revue neutre",
                    }
                )

    # Cause principale des non-appariés (hors dual-source revue)
    unmatched_reasons = Counter()
    for r in results:
        if r["classification"] not in {
            "UNMATCHED_COVERED",
            "UNMATCHED_UNCOVERED",
            "COVERAGE_STATUS_REQUIRES_REVIEW",
        }:
            continue
        if not _norm(r.get("toponym")) or not re.search(r"[a-z]", _norm(r.get("toponym"))):
            unmatched_reasons["toponym_technique_ou_absent"] += 1
        elif r.get("dual_source_observation"):
            unmatched_reasons["dual_source_sans_match_admin"] += 1
        elif not _norm(r.get("province")):
            unmatched_reasons["province_absente"] += 1
        else:
            unmatched_reasons["toponyme_absent_du_referentiel_admin"] += 1
    funnel["principal_unmatched_factor"] = (
        unmatched_reasons.most_common(1)[0][0] if unmatched_reasons else None
    )
    funnel["unmatched_reason_breakdown"] = dict(unmatched_reasons)

    counts = Counter(r["classification"] for r in results)
    matched = counts.get("MATCHED_LOCALITY", 0) + counts.get("PROBABLE_MATCH", 0)
    nci_total = len(results)
    match_rate = round(matched / nci_total, 4) if nci_total else 0.0

    try:
        from api.services import coverage_intelligence_service as nci

        agg = nci.get_aggregates() or {}
        pop_by_province = agg.get("by_province") or {}
        pop_by_territory = agg.get("by_territory") or {}
        national = agg.get("national") or {}
    except Exception:
        pop_by_province, pop_by_territory, national = {}, {}, {}

    # Cohérence population province vs national
    pop_cov_sum = sum(int(p.get("population_covered") or 0) for p in pop_by_province.values())
    pop_unc_sum = sum(int(p.get("population_uncovered") or 0) for p in pop_by_province.values())

    kpis = {
        "admin_localities": len(admin),
        "nci_covered": len(covered),
        "nci_uncovered": len(uncovered),
        "nci_observations": len(covered) + len(uncovered),
        "rows_classified": nci_total,
        "match_rate_confident_or_probable": match_rate,
        "by_classification": {c: counts.get(c, 0) for c in CLASSIFICATIONS},
        "dual_source_identity_count": len(dual_source_ids),
        "dual_source_row_count": len(dual_source_rows),
        "confirmed_conflicts_count": counts.get("CONFLICTING_COVERAGE_STATUS", 0),
        "coverage_semantics": COVERAGE_SEMANTICS,
        "funnel": funnel,
        "universes_not_forced_equal": True,
        "population_national": {
            "population_covered": national.get("population_covered"),
            "population_uncovered": national.get("population_uncovered"),
            "source": "data/coverage/aggregates.json",
        },
        "population_province_sums": {
            "population_covered_sum": pop_cov_sum,
            "population_uncovered_sum": pop_unc_sum,
            "matches_national_covered": pop_cov_sum == int(national.get("population_covered") or -1),
            "matches_national_uncovered": pop_unc_sum == int(national.get("population_uncovered") or -1),
        },
        "population_by_province_available": bool(pop_by_province),
        "population_by_territory_available": bool(pop_by_territory),
    }

    state = LocalityCoverageState(
        executed=True,
        message="Rapprochement NIRE localités exécuté (lecture seule).",
        meta={
            "engine": ENGINE_VERSION,
            "generated_at": _now(),
            "thresholds": THRESHOLDS,
            "classifications": list(CLASSIFICATIONS),
            "admin_source": admin[0].get("source") if admin else None,
        },
        kpis=kpis,
        rows=results,
        conflicts=dual_source_rows[:500],
        performance={"elapsed_ms": round((time.time() - started) * 1000, 1)},
    )

    global _STATE
    _STATE = state

    if write_cache:
        CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        CACHE_PATH.write_text(
            json.dumps(
                {
                    "meta": state.meta,
                    "kpis": state.kpis,
                    "conflicts": state.conflicts,
                    "rows_sample": state.rows[:200],
                    "note": "Derived cache — sources immuables",
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
            "message": "Aucun rapprochement localités exécuté — POST /api/nire/locality-coverage/run",
            "engine": ENGINE_VERSION,
        }
    return {
        "executed": True,
        "message": st.message,
        "meta": st.meta,
        "kpis": st.kpis,
        "performance": st.performance,
        "conflicts_count": len(st.conflicts),
    }


def summary_payload() -> dict[str, Any]:
    st = get_state()
    if not st.executed:
        return status_payload()
    # Attach NCI territorial population without inventing joins
    try:
        from api.services import coverage_intelligence_service as nci

        provinces = nci.list_provinces(limit=30).get("provinces") or []
        territories = nci.list_territories(limit=50).get("territories") or []
    except Exception:
        provinces, territories = [], []
    return {
        "executed": True,
        "kpis": st.kpis,
        "meta": st.meta,
        "population_by_province_top": [
            {
                "province": p.get("province"),
                "population_covered": p.get("population_covered"),
                "population_uncovered": p.get("population_uncovered"),
                "localities_covered": p.get("localities_covered"),
                "localities_uncovered": p.get("localities_uncovered"),
            }
            for p in provinces[:15]
        ],
        "population_by_territory_top": [
            {
                "territoire": t.get("territoire") or t.get("territory"),
                "province": t.get("province"),
                "population_covered": t.get("population_covered"),
                "population_uncovered": t.get("population_uncovered"),
            }
            for t in territories[:15]
        ],
        "note": "Population territoriale issue des agrégats NCI — pas d'invention via jointure forcée.",
    }


def list_rows(
    *,
    classification: str | None = None,
    coverage_status: str | None = None,
    province: str | None = None,
    offset: int = 0,
    limit: int = 50,
) -> dict[str, Any]:
    st = get_state()
    rows = st.rows
    if classification:
        rows = [r for r in rows if r.get("classification") == classification]
    if coverage_status:
        rows = [r for r in rows if r.get("coverage_status") == coverage_status]
    if province:
        needle = province.casefold()
        rows = [r for r in rows if str(r.get("province") or "").casefold() == needle]
    total = len(rows)
    return {
        "total": total,
        "offset": offset,
        "limit": limit,
        "rows": rows[offset : offset + limit],
        "classifications": CLASSIFICATIONS,
    }
