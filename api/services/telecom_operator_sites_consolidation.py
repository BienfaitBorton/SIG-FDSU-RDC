"""Consolidation FDSU du référentiel des SITES OPÉRATEURS (pas les infrastructures physiques).

Règles institutionnelles :
- Traitement OPÉRATEUR PAR OPÉRATEUR.
- Aucune déduplication croisée entre opérateurs.
- Vodacom/Orange : mettre à jour + compléter DB avec MNO ; ne jamais supprimer l'absent du MNO.
- Airtel/Africell : intégrer la source MNO ; doublons uniquement intra-opérateur.
- Planned conservés ; compteurs ALL vs EXISTING séparés.
- Fibre / MW / Fiberco / FTTX exclus de TOTAL_MOBILE_OPERATOR_SITES.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from api.services.nire.mno_audit import (
    DEFAULT_SOURCE,
    _norm_text,
    haversine_m,
    ingest_mno_rows,
    name_similarity,
)
from api.services.telecom_geo_utils import coord_key, inventory_fiber_mw_assets

ENGINE = "telecom-operator-sites-consolidation-fdsu-1.0.0"
MOBILE_OPS = ("VODACOM", "ORANGE", "AIRTEL", "AFRICELL")
# Tolérance analytique pour petites différences GPS entre sources du MÊME opérateur
NEAR_SAME_SITE_M = 75.0
NAME_STRONG = 0.85


@dataclass
class OperatorSitesResult:
    by_operator: dict[str, dict[str, Any]] = field(default_factory=dict)
    totals: dict[str, Any] = field(default_factory=dict)
    fiber_mw_separate: dict[str, Any] = field(default_factory=dict)
    cartography: dict[str, Any] = field(default_factory=dict)
    nire_role: dict[str, Any] = field(default_factory=dict)
    method: dict[str, Any] = field(default_factory=dict)
    samples: dict[str, list] = field(default_factory=dict)


def _load_db_operator(operator_code: str) -> list[dict[str, Any]]:
    from api.config import connect_db
    from psycopg2.extras import RealDictCursor

    with connect_db() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                """
                SELECT i.id, i.infra_code, i.infra_name, i.infra_type, i.technology,
                       i.status, i.latitude, i.longitude, i.properties, i.source_file,
                       o.operator_code
                FROM telecom.infrastructure i
                JOIN telecom.operators o ON o.id = i.operator_id
                WHERE o.operator_code = %s
                """,
                (operator_code,),
            )
            return [dict(r) for r in cur.fetchall()]


def _is_planned(status: str | None) -> bool:
    s = (status or "").upper().replace(" ", "")
    return "PLAN" in s


def _db_name(row: dict[str, Any]) -> str:
    return str(row.get("infra_name") or "")


def _db_name_norm(row: dict[str, Any]) -> str:
    props = row.get("properties") if isinstance(row.get("properties"), dict) else {}
    for k in ("Site_Name", "site_name", "name"):
        if props.get(k):
            return _norm_text(str(props[k]))
    return _norm_text(_db_name(row))


def _same_operator_match(
    mno: dict[str, Any],
    db: dict[str, Any],
) -> tuple[bool, str, list[str]]:
    """Retourne (is_same_site, strength, evidence). Proximité seule → False."""
    evidence: list[str] = []
    name_m = mno.get("site_name_normalized") or _norm_text(mno.get("site_name_original"))
    name_d = _db_name_norm(db)
    sim = name_similarity(mno.get("site_name_original") or "", _db_name(db))
    if name_m and name_d and name_m == name_d:
        sim = 1.0
        evidence.append("normalized_name_identical")

    dist = None
    if (
        mno.get("geometry_valid")
        and db.get("latitude") is not None
        and db.get("longitude") is not None
        and not (float(db["latitude"]) == 0 and float(db["longitude"]) == 0)
    ):
        dist = haversine_m(
            (float(mno["latitude"]), float(mno["longitude"])),
            (float(db["latitude"]), float(db["longitude"])),
        )
        evidence.append(f"distance_m={dist:.2f}")

    exact = False
    if mno.get("geometry_valid") and db.get("latitude") is not None:
        exact = coord_key(float(mno["latitude"]), float(mno["longitude"])) == coord_key(
            float(db["latitude"]), float(db["longitude"])
        )
        if exact:
            evidence.append("exact_coord_6dp")

    # Identifiant / code compact
    code_m = (name_m or "").replace(" ", "")
    code_d = (name_d or "").replace(" ", "")
    if code_m and code_d and code_m == code_d and len(code_m) >= 4:
        evidence.append("identifier_name_compact_equal")

    # Règles SAME SITE (même opérateur uniquement — appelant garanti)
    if sim >= 1.0 and name_m:
        # Nom identique : petites différences GPS n'empêchent pas la reconnaissance
        evidence.append("same_site_by_identical_name")
        return True, "STRONG", evidence
    if exact and sim >= 0.40:
        evidence.append("same_site_by_exact_coord_and_name_signal")
        return True, "STRONG", evidence
    if exact and sim < 0.40:
        # Même cellule GPS + même opérateur : doublon fort métier FDSU intra-op
        evidence.append("same_site_by_exact_coord_same_operator")
        return True, "STRONG", evidence
    if sim >= NAME_STRONG and dist is not None and dist < NEAR_SAME_SITE_M:
        evidence.append("same_site_by_strong_name_and_near_coords")
        return True, "STRONG", evidence
    if sim >= NAME_STRONG and dist is None:
        # Nom très fort sans géométrie MNO valide — ne pas matcher automatiquement
        return False, "NONE", evidence + ["strong_name_but_invalid_or_missing_geom"]
    if dist is not None and dist < 25.0 and sim < NAME_STRONG:
        evidence.append("proximity_only_possible_duplicate")
        return False, "POSSIBLE", evidence
    return False, "NONE", evidence


def _index_db_for_match(db_rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_name: dict[str, list[dict[str, Any]]] = defaultdict(list)
    by_coord: dict[str, list[dict[str, Any]]] = defaultdict(list)
    grid: dict[tuple[int, int], list[tuple[float, float, dict]]] = defaultdict(list)
    cell = 0.001  # ~110 m
    for r in db_rows:
        nn = _db_name_norm(r)
        if nn:
            by_name[nn].append(r)
        if r.get("latitude") is None or r.get("longitude") is None:
            continue
        lat, lon = float(r["latitude"]), float(r["longitude"])
        if lat == 0.0 and lon == 0.0:
            continue
        by_coord[coord_key(lat, lon)].append(r)
        grid[(int(lat / cell), int(lon / cell))].append((lat, lon, r))
    return {"by_name": by_name, "by_coord": by_coord, "grid": grid, "cell": cell}


def _candidate_db_rows(mno: dict[str, Any], index: dict[str, Any]) -> list[dict[str, Any]]:
    seen: set[int] = set()
    out: list[dict[str, Any]] = []
    name = mno.get("site_name_normalized") or _norm_text(mno.get("site_name_original"))
    if name:
        for r in index["by_name"].get(name, []):
            rid = int(r["id"])
            if rid not in seen:
                seen.add(rid)
                out.append(r)
    if mno.get("geometry_valid"):
        key = coord_key(float(mno["latitude"]), float(mno["longitude"]))
        for r in index["by_coord"].get(key, []):
            rid = int(r["id"])
            if rid not in seen:
                seen.add(rid)
                out.append(r)
        lat, lon = float(mno["latitude"]), float(mno["longitude"])
        cell = index["cell"]
        gi, gj = int(lat / cell), int(lon / cell)
        for di in (-1, 0, 1):
            for dj in (-1, 0, 1):
                for dlat, dlon, r in index["grid"].get((gi + di, gj + dj), []):
                    if haversine_m((lat, lon), (dlat, dlon)) < NEAR_SAME_SITE_M:
                        rid = int(r["id"])
                        if rid not in seen:
                            seen.add(rid)
                            out.append(r)
    return out


def consolidate_operator_db_mno(
    operator: str,
    db_rows: list[dict[str, Any]],
    mno_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    """Consolide un opérateur déjà en DB (Vodacom/Orange) avec le fichier MNO."""
    op_mno = [r for r in mno_rows if r.get("operator") == operator]
    index = _index_db_for_match(db_rows)
    matched_db_ids: set[int] = set()
    matched_mno_ids: set[str] = set()
    matches: list[dict[str, Any]] = []
    possible: list[dict[str, Any]] = []
    added: list[dict[str, Any]] = []

    # Premier passage : matches STRONG
    for mno in op_mno:
        cands = _candidate_db_rows(mno, index)
        best = None
        best_ev: list[str] = []
        best_strength = "NONE"
        for db in cands:
            if int(db["id"]) in matched_db_ids:
                continue
            ok, strength, ev = _same_operator_match(mno, db)
            if strength == "STRONG" and ok:
                # Prefer identical name
                score = name_similarity(mno.get("site_name_original") or "", _db_name(db))
                if best is None or score > best[0]:
                    best = (score, db)
                    best_ev = ev
                    best_strength = strength
            elif strength == "POSSIBLE":
                possible.append(
                    {
                        "mno_row_id": mno.get("row_id"),
                        "mno_name": mno.get("site_name_original"),
                        "db_id": db.get("id"),
                        "db_name": _db_name(db),
                        "evidence": ev,
                    }
                )
        if best is not None:
            db = best[1]
            matched_db_ids.add(int(db["id"]))
            matched_mno_ids.add(str(mno["row_id"]))
            matches.append(
                {
                    "mno_row_id": mno.get("row_id"),
                    "mno_name": mno.get("site_name_original"),
                    "db_id": db.get("id"),
                    "db_name": _db_name(db),
                    "strength": best_strength,
                    "evidence": best_ev,
                    "status_mno": mno.get("status_normalized"),
                    "rat": (mno.get("rat") or {}).get("rat_normalized"),
                }
            )

    # Sites MNO non matchés → ajout (y compris Planned / invalid geom conservés)
    for mno in op_mno:
        if str(mno["row_id"]) in matched_mno_ids:
            continue
        added.append(mno)

    # Intra-MNO strong dups among added (same name norm + exact/near) — éviter double ajout
    added_kept: list[dict[str, Any]] = []
    seen_added_keys: set[str] = set()
    intra_mno_dups = 0
    for mno in added:
        name = mno.get("site_name_normalized") or ""
        if mno.get("geometry_valid"):
            key = f"{name}|{coord_key(float(mno['latitude']), float(mno['longitude']))}"
        else:
            key = f"{name}|INVALID|{mno.get('row_id')}"
        # Also collapse identical name within added if already kept with near coords
        collapse = False
        if name and mno.get("geometry_valid"):
            for kept in added_kept:
                kn = kept.get("site_name_normalized") or ""
                if kn != name:
                    continue
                if not kept.get("geometry_valid"):
                    continue
                d = haversine_m(
                    (float(mno["latitude"]), float(mno["longitude"])),
                    (float(kept["latitude"]), float(kept["longitude"])),
                )
                if d < NEAR_SAME_SITE_M or coord_key(
                    float(mno["latitude"]), float(mno["longitude"])
                ) == coord_key(float(kept["latitude"]), float(kept["longitude"])):
                    collapse = True
                    break
        if key in seen_added_keys or collapse:
            intra_mno_dups += 1
            continue
        seen_added_keys.add(key)
        added_kept.append(mno)

    kept_old_only = [r for r in db_rows if int(r["id"]) not in matched_db_ids]
    consolidated_count = len(db_rows) + len(added_kept)  # matched counted once via db_rows
    # Wait: formula = anciens + nouveaux - doublons
    # = len(db) + len(op_mno) - len(matches) - intra adjustments?
    # matched: one from db + one from mno → count 1 → contribute len(matches) once
    # old only: len(kept_old_only)
    # new only: len(added_kept)
    # total = matched + old_only + new_only = len(matches) + len(kept_old_only) + len(added_kept)
    # = len(db_rows) - 0 + len(added_kept) since matches + kept_old = db_rows
    assert len(matches) + len(kept_old_only) == len(db_rows)
    consolidated_count = len(matches) + len(kept_old_only) + len(added_kept)

    # Planned among consolidated entries
    planned = 0
    # Matched: use MNO status if Planned else DB
    for m in matches:
        if _is_planned(m.get("status_mno")):
            planned += 1
    for mno in added_kept:
        if _is_planned(mno.get("status_normalized")):
            planned += 1
    # old-only DB: check status field
    for r in kept_old_only:
        if _is_planned(r.get("status")):
            planned += 1

    existing = consolidated_count - planned

    return {
        "operator": operator,
        "ancien_db": len(db_rows),
        "nouveau_fichier": len(op_mno),
        "correspondances_doublons_ancien_nouveau": len(matches),
        "nouveaux_sites_ajoutes": len(added_kept),
        "anciens_conserves_absents_mno": len(kept_old_only),
        "intra_mno_duplicates_collapsed_among_added": intra_mno_dups,
        "possible_duplicates_kept_separate": len(possible),
        "total_consolide": consolidated_count,
        "planned_in_consolidated": planned,
        "existing_in_consolidated": existing,
        "control_formula": (
            f"total = ancien({len(db_rows)}) + ajoutes({len(added_kept)}) "
            f"= {consolidated_count} "
            f"[matches={len(matches)} comptés une fois via DB]"
        ),
        "alt_formula": (
            f"ancien + nouveau_fichier - correspondances - intra_mno_dups_added "
            f"= {len(db_rows)} + {len(op_mno)} - {len(matches)} - {intra_mno_dups} "
            f"= {len(db_rows) + len(op_mno) - len(matches) - intra_mno_dups}"
        ),
        "samples": {
            "matches": matches[:5],
            "added": [
                {
                    "row_id": r.get("row_id"),
                    "name": r.get("site_name_original"),
                    "status": r.get("status_normalized"),
                }
                for r in added_kept[:5]
            ],
            "possible_duplicate": possible[:5],
            "kept_old_only": [
                {"id": r.get("id"), "name": _db_name(r)} for r in kept_old_only[:5]
            ],
        },
    }


def consolidate_mno_only_operator(
    operator: str,
    mno_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    """Airtel / Africell — source MNO ; doublons uniquement intra-opérateur."""
    op_rows = [r for r in mno_rows if r.get("operator") == operator]
    kept: list[dict[str, Any]] = []
    intra_dups = 0
    possible = 0
    by_name: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for r in op_rows:
        name = r.get("site_name_normalized") or ""
        collapsed = False
        if name and r.get("geometry_valid"):
            for prev in by_name.get(name, []):
                if not prev.get("geometry_valid"):
                    continue
                d = haversine_m(
                    (float(r["latitude"]), float(r["longitude"])),
                    (float(prev["latitude"]), float(prev["longitude"])),
                )
                exact = coord_key(float(r["latitude"]), float(r["longitude"])) == coord_key(
                    float(prev["latitude"]), float(prev["longitude"])
                )
                if exact or (d < NEAR_SAME_SITE_M and name):
                    # Même site Airtel/Africell manifeste (nom identique + coords proches/exactes)
                    collapsed = True
                    intra_dups += 1
                    break
                if d < 25.0:
                    possible += 1
        if collapsed:
            continue
        kept.append(r)
        if name:
            by_name[name].append(r)

    planned = sum(1 for r in kept if _is_planned(r.get("status_normalized")))
    # Invalid geometry still counted in source integration (conserved)
    return {
        "operator": operator,
        "source": len(op_rows),
        "doublons_internes_collapsed": intra_dups,
        "possible_duplicates_kept_separate": possible,
        "total_consolide": len(kept),
        "nouveaux_sites_ajoutes": len(kept),  # tous issus du fichier
        "correspondances_doublons_ancien_nouveau": 0,
        "ancien_db": 0,
        "nouveau_fichier": len(op_rows),
        "planned_in_consolidated": planned,
        "existing_in_consolidated": len(kept) - planned,
        "control_formula": f"source({len(op_rows)}) - intra_dups({intra_dups}) = {len(kept)}",
        "samples": {
            "kept": [
                {
                    "row_id": r.get("row_id"),
                    "name": r.get("site_name_original"),
                    "status": r.get("status_normalized"),
                }
                for r in kept[:5]
            ]
        },
    }


def consolidate_mobile_operator_sites(
    source: Path | None = None,
    *,
    db_by_operator: dict[str, list[dict[str, Any]]] | None = None,
) -> OperatorSitesResult:
    meta, mno_rows = ingest_mno_rows(Path(source) if source else DEFAULT_SOURCE)

    if db_by_operator is None:
        vod_db = _load_db_operator("VODACOM")
        ora_db = _load_db_operator("ORANGE")
    else:
        vod_db = db_by_operator.get("VODACOM") or []
        ora_db = db_by_operator.get("ORANGE") or []

    vod = consolidate_operator_db_mno("VODACOM", vod_db, mno_rows)
    ora = consolidate_operator_db_mno("ORANGE", ora_db, mno_rows)
    airtel = consolidate_mno_only_operator("AIRTEL", mno_rows)
    africell = consolidate_mno_only_operator("AFRICELL", mno_rows)

    by_op = {
        "VODACOM": vod,
        "ORANGE": ora,
        "AIRTEL": airtel,
        "AFRICELL": africell,
    }

    total_all = sum(by_op[o]["total_consolide"] for o in MOBILE_OPS)
    total_planned = sum(by_op[o]["planned_in_consolidated"] for o in MOBILE_OPS)
    total_existing = sum(by_op[o]["existing_in_consolidated"] for o in MOBILE_OPS)

    # Source planned count from MNO (for cross-check)
    mno_planned = sum(1 for r in mno_rows if r.get("operator") in MOBILE_OPS and _is_planned(r.get("status_normalized")))

    fiber = inventory_fiber_mw_assets() if db_by_operator is None else {}

    return OperatorSitesResult(
        by_operator=by_op,
        totals={
            "TOTAL_MOBILE_OPERATOR_SITES_ALL": total_all,
            "TOTAL_EXISTING_MOBILE_OPERATOR_SITES": total_existing,
            "TOTAL_PLANNED": total_planned,
            "mno_planned_rows_in_source": mno_planned,
            "formula": (
                "TOTAL_ALL = VODACOM_CONSOLIDATED + ORANGE_CONSOLIDATED "
                "+ AIRTEL + AFRICELL "
                "(aucune soustraction de mutualisation inter-opérateurs)"
            ),
            "mno_source": {
                "file": meta.file_name,
                "sha256": meta.sha256,
                "total_rows": meta.total_rows,
                "operators_detected": meta.operators_detected,
            },
            "abandoned_physical_scenarios": [
                "12289",
                "15614",
                "minimum/maximum/conservative physical infrastructure counts",
            ],
            "note": (
                "Ce total compte des SITES OPÉRATEURS consolidés, "
                "pas des infrastructures physiques mutualisées."
            ),
        },
        fiber_mw_separate={
            "FIBERCO_nodes": (fiber.get("FIBER_NETWORK_ASSETS") or {}).get("nodes_by_operator", {}).get(
                "FIBERCO"
            ),
            "FTTX_nodes": (fiber.get("FIBER_NETWORK_ASSETS") or {}).get("nodes_by_operator", {}).get(
                "FTTX"
            ),
            "FIBER_nodes_total": (fiber.get("FIBER_NETWORK_ASSETS") or {}).get("nodes_in_infrastructure"),
            "FIBER_lines": (fiber.get("FIBER_NETWORK_ASSETS") or {}).get("lines_in_network_lines"),
            "MW_links": (fiber.get("MICROWAVE_ASSETS") or {}).get("links_in_network_lines"),
            "excluded_from_mobile_operator_sites": True,
        },
        cartography={
            "operator_layers": ["Vodacom", "Orange", "Airtel", "Africell"],
            "planned_layer": "MNO Planned",
            "independent_non_mobile": ["Fibre", "MW", "Fiberco", "FTTX"],
            "site_attributes": [
                "name",
                "operator",
                "coordinates",
                "status",
                "RAT",
                "provenance",
            ],
            "no_cross_operator_dedup": True,
        },
        nire_role={
            "helps_with": [
                "doublons Vodacom/Vodacom",
                "doublons Orange/Orange",
                "doublons Airtel/Airtel",
                "doublons Africell/Africell",
                "variantes de noms",
                "provenance",
                "anomalies / POSSIBLE_DUPLICATE",
            ],
            "must_not": [
                "remettre en cause l'intégration institutionnelle FDSU",
                "dédupliquer entre opérateurs",
                "supprimer automatiquement en cas d'incertitude",
            ],
        },
        method={
            "engine": ENGINE,
            "near_same_site_m": NEAR_SAME_SITE_M,
            "name_strong": NAME_STRONG,
            "proximity_alone_never_merges": True,
            "cross_operator_dedup": False,
        },
        samples={
            "VODACOM": vod.get("samples") or {},
            "ORANGE": ora.get("samples") or {},
            "AIRTEL": airtel.get("samples") or {},
            "AFRICELL": africell.get("samples") or {},
        },
    )


def build_consolidated_operator_geojson(
    operator: str,
    *,
    limit: int = 100000,
    source: Path | None = None,
) -> dict[str, Any]:
    """GeoJSON du référentiel consolidé Vodacom/Orange (DB + ajouts MNO, sans écriture)."""
    operator = (operator or "").upper()
    if operator not in {"VODACOM", "ORANGE"}:
        return {
            "type": "FeatureCollection",
            "features": [],
            "meta": {"error": "operator_not_supported_for_db_mno_merge", "operator": operator},
        }

    meta, mno_rows = ingest_mno_rows(Path(source) if source else DEFAULT_SOURCE)
    db_rows = _load_db_operator(operator)
    detail = consolidate_operator_db_mno(operator, db_rows, mno_rows)

    # Rejouer le matching pour récupérer les lignes MNO enrichissantes
    op_mno = [r for r in mno_rows if r.get("operator") == operator]
    index = _index_db_for_match(db_rows)
    matched_db_ids: set[int] = set()
    mno_by_db_id: dict[int, dict[str, Any]] = {}
    matched_mno_ids: set[str] = set()

    for mno in op_mno:
        cands = _candidate_db_rows(mno, index)
        best = None
        for db in cands:
            did = int(db["id"])
            if did in matched_db_ids:
                continue
            ok, strength, _ev = _same_operator_match(mno, db)
            if strength == "STRONG" and ok:
                score = name_similarity(mno.get("site_name_original") or "", _db_name(db))
                if best is None or score > best[0]:
                    best = (score, db, mno)
        if best is not None:
            db = best[1]
            mno = best[2]
            matched_db_ids.add(int(db["id"]))
            matched_mno_ids.add(str(mno["row_id"]))
            mno_by_db_id[int(db["id"])] = mno

    # Reconstruire added_kept comme dans consolidate_operator_db_mno
    added = [m for m in op_mno if str(m["row_id"]) not in matched_mno_ids]
    added_kept: list[dict[str, Any]] = []
    seen_added_keys: set[str] = set()
    for mno in added:
        name = mno.get("site_name_normalized") or ""
        if mno.get("geometry_valid"):
            key = f"{name}|{coord_key(float(mno['latitude']), float(mno['longitude']))}"
        else:
            key = f"{name}|INVALID|{mno.get('row_id')}"
        collapse = False
        if name and mno.get("geometry_valid"):
            for kept in added_kept:
                kn = kept.get("site_name_normalized") or ""
                if kn != name or not kept.get("geometry_valid"):
                    continue
                d = haversine_m(
                    (float(mno["latitude"]), float(mno["longitude"])),
                    (float(kept["latitude"]), float(kept["longitude"])),
                )
                if d < NEAR_SAME_SITE_M or coord_key(
                    float(mno["latitude"]), float(mno["longitude"])
                ) == coord_key(float(kept["latitude"]), float(kept["longitude"])):
                    collapse = True
                    break
        if key in seen_added_keys or collapse:
            continue
        seen_added_keys.add(key)
        added_kept.append(mno)

    features: list[dict[str, Any]] = []
    fid = 1

    for db in db_rows:
        if db.get("latitude") is None or db.get("longitude") is None:
            continue
        lat, lon = float(db["latitude"]), float(db["longitude"])
        if lat == 0.0 and lon == 0.0:
            continue
        mno = mno_by_db_id.get(int(db["id"]))
        props: dict[str, Any] = {
            "id": db.get("id"),
            "infra_code": db.get("infra_code"),
            "infra_name": _db_name(db),
            "site_name": _db_name(db),
            "name": _db_name(db),
            "operator_code": operator,
            "operator_name": "Vodacom" if operator == "VODACOM" else "Orange RDC",
            "operator": operator,
            "status": (mno.get("status_normalized") if mno else None) or db.get("status") or "IN_SERVICE",
            "status_normalized": mno.get("status_normalized") if mno else None,
            "technology": db.get("technology"),
            "rat": ((mno.get("rat") or {}).get("rat_normalized") if mno else None) or db.get("technology"),
            "infra_type": db.get("infra_type") or "mobile_site",
            "latitude": lat,
            "longitude": lon,
            "nire_quality_status": "VERIFIED" if mno else "HIGH_CONFIDENCE",
            "data_source": "OPERATOR_SITES_CONSOLIDATED",
            "source_label": "Référentiel consolidé FDSU",
            "provenance": {
                "db_id": db.get("id"),
                "db_source_file": db.get("source_file"),
                "mno_row_id": mno.get("row_id") if mno else None,
                "mno_source_file": mno.get("source_file") if mno else None,
                "sources": ["TELECOM_DB", "FDSU_MNO"] if mno else ["TELECOM_DB"],
            },
            "consolidation_status": "MATCHED_DB_MNO" if mno else "DB_ONLY_KEPT",
        }
        features.append(
            {
                "type": "Feature",
                "id": fid,
                "geometry": {"type": "Point", "coordinates": [lon, lat]},
                "properties": {k: v for k, v in props.items() if v not in (None, "")},
            }
        )
        fid += 1
        if len(features) >= limit:
            break

    if len(features) < limit:
        for mno in added_kept:
            if not mno.get("geometry_valid"):
                continue
            lat, lon = float(mno["latitude"]), float(mno["longitude"])
            rat = (mno.get("rat") or {}).get("rat_normalized") or mno.get("rat_original")
            props = {
                "row_id": mno.get("row_id"),
                "infra_name": mno.get("site_name_original"),
                "site_name": mno.get("site_name_original"),
                "name": mno.get("site_name_original"),
                "operator_code": operator,
                "operator_name": "Vodacom" if operator == "VODACOM" else "Orange RDC",
                "operator": operator,
                "status": mno.get("status_normalized"),
                "status_normalized": mno.get("status_normalized"),
                "rat": rat,
                "technology": rat,
                "infra_type": "mno_declared_site",
                "latitude": lat,
                "longitude": lon,
                "nire_quality_status": "PROVISIONAL",
                "data_source": "OPERATOR_SITES_CONSOLIDATED",
                "source_label": "FDSU MNO (ajout consolidé)",
                "provenance": {
                    "mno_row_id": mno.get("row_id"),
                    "mno_source_file": mno.get("source_file"),
                    "source_hash": mno.get("source_hash"),
                    "sources": ["FDSU_MNO"],
                },
                "consolidation_status": "MNO_NEW_ADDED",
                "planned": _is_planned(mno.get("status_normalized")),
            }
            features.append(
                {
                    "type": "Feature",
                    "id": fid,
                    "geometry": {"type": "Point", "coordinates": [lon, lat]},
                    "properties": {k: v for k, v in props.items() if v not in (None, "", False)},
                }
            )
            fid += 1
            if len(features) >= limit:
                break

    return {
        "type": "FeatureCollection",
        "features": features,
        "meta": {
            "source_kind": "OPERATOR_SITES_CONSOLIDATED",
            "operator": operator,
            "returned": len(features),
            "total_consolide": detail.get("total_consolide"),
            "matches": detail.get("correspondances_doublons_ancien_nouveau"),
            "nouveaux_ajoutes": detail.get("nouveaux_sites_ajoutes"),
            "mno_sha256": meta.sha256,
            "kpi_note": "Couche sites opérateurs consolidés — distincte du COUNT telecom.infrastructure",
        },
    }


def result_as_dict(result: OperatorSitesResult) -> dict[str, Any]:
    return {
        "by_operator": result.by_operator,
        "totals": result.totals,
        "fiber_mw_separate": result.fiber_mw_separate,
        "cartography": result.cartography,
        "nire_role": result.nire_role,
        "method": result.method,
        "samples": result.samples,
        "report_table": {
            "VODACOM": {
                "ancien": result.by_operator["VODACOM"]["ancien_db"],
                "nouveau_fichier": result.by_operator["VODACOM"]["nouveau_fichier"],
                "correspondances_doublons_ancien_nouveau": result.by_operator["VODACOM"][
                    "correspondances_doublons_ancien_nouveau"
                ],
                "nouveaux_sites_ajoutes": result.by_operator["VODACOM"]["nouveaux_sites_ajoutes"],
                "total_consolide": result.by_operator["VODACOM"]["total_consolide"],
            },
            "ORANGE": {
                "ancien": result.by_operator["ORANGE"]["ancien_db"],
                "nouveau_fichier": result.by_operator["ORANGE"]["nouveau_fichier"],
                "correspondances_doublons_ancien_nouveau": result.by_operator["ORANGE"][
                    "correspondances_doublons_ancien_nouveau"
                ],
                "nouveaux_sites_ajoutes": result.by_operator["ORANGE"]["nouveaux_sites_ajoutes"],
                "total_consolide": result.by_operator["ORANGE"]["total_consolide"],
            },
            "AIRTEL": {
                "source": result.by_operator["AIRTEL"]["source"],
                "doublons_internes": result.by_operator["AIRTEL"]["doublons_internes_collapsed"],
                "total_consolide": result.by_operator["AIRTEL"]["total_consolide"],
            },
            "AFRICELL": {
                "source": result.by_operator["AFRICELL"]["source"],
                "doublons_internes": result.by_operator["AFRICELL"]["doublons_internes_collapsed"],
                "total_consolide": result.by_operator["AFRICELL"]["total_consolide"],
            },
            "TOTAL_MOBILE_OPERATOR_SITES_ALL": result.totals["TOTAL_MOBILE_OPERATOR_SITES_ALL"],
            "TOTAL_EXISTING_MOBILE_OPERATOR_SITES": result.totals[
                "TOTAL_EXISTING_MOBILE_OPERATOR_SITES"
            ],
            "TOTAL_PLANNED": result.totals["TOTAL_PLANNED"],
        },
    }
