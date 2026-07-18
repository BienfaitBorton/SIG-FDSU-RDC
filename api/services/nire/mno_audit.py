"""NIRE Phase 5 — audit MNO contrôlé (ingestion, normalisation, rapprochement lecture seule).

Aucune modification du fichier source ni du référentiel telecom.infrastructure.
Le KPI national (COUNT telecom.infrastructure) n'est jamais altéré.
"""
from __future__ import annotations

import hashlib
import math
import re
import time
import unicodedata
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

ENGINE_VERSION = "nire-mno-audit-5.0.0"
RULE_VERSION = "nire-mno-rules-5.0.0"

DEFAULT_SOURCE = (
    Path(__file__).resolve().parents[3]
    / "data"
    / "raw"
    / "Operators existing and planned sites_20260713.xlsx"
)

OPERATOR_PARTITIONS = {
    "VODACOM": "MNO_VODACOM",
    "AIRTEL": "MNO_AIRTEL",
    "ORANGE": "MNO_ORANGE",
    "AFRICELL": "MNO_AFRICELL",
}

STATUS_MAP = {
    "ONLINE": "ONLINE",
    "IN SERVICE": "IN_SERVICE",
    "INSERVICE": "IN_SERVICE",
    "PLANNED": "PLANNED",
    "OUT SERVICE": "OUT_OF_SERVICE",
    "OUT OF SERVICE": "OUT_OF_SERVICE",
    "OUTSERVICE": "OUT_OF_SERVICE",
    "ONLY TX": "TX_ONLY",
    "ONLYTX": "TX_ONLY",
}

CLASSIFICATIONS = (
    "MATCH_EXISTING_INFRASTRUCTURE",
    "OPERATOR_PRESENCE_ON_EXISTING_INFRASTRUCTURE",
    "NEW_INFRASTRUCTURE_CANDIDATE",
    "PLANNED_SITE",
    "POSSIBLE_DUPLICATE",
    "COLOCATED_MULTI_OPERATOR",
    "AMBIGUOUS",
    "CONFLICT",
    "INVALID_GEOMETRY",
    "UNRESOLVED",
)

# Seuils configurables (mètres) — non figés comme vérité métier absolue.
THRESHOLDS_M = {
    "exact": 1.0,
    "very_close": 50.0,
    "nearby": 250.0,
}

# Classes historiquement listées pour la Review Queue (documentation / filtre UI).
# L’éligibilité technique réelle est : requires_human_review=true
# (voir is_review_queue_eligible) — y compris MATCH Planned et OPERATOR_PRESENCE+coloc.
REVIEW_CLASSIFICATIONS = {
    "AMBIGUOUS",
    "CONFLICT",
    "POSSIBLE_DUPLICATE",
    "INVALID_GEOMETRY",
    "NEW_INFRASTRUCTURE_CANDIDATE",
    "COLOCATED_MULTI_OPERATOR",
    "UNRESOLVED",
    "OPERATOR_PRESENCE_ON_EXISTING_INFRASTRUCTURE",
    "MATCH_EXISTING_INFRASTRUCTURE",
}

# Classification opérationnelle analytique (n’altère aucune décision métier).
FAST_REVIEW_CLASSES = frozenset(
    {
        "NEW_INFRASTRUCTURE_CANDIDATE",
        "MATCH_EXISTING_INFRASTRUCTURE",
        "OPERATOR_PRESENCE_ON_EXISTING_INFRASTRUCTURE",
        "POSSIBLE_DUPLICATE",
        "INVALID_GEOMETRY",
    }
)
COMPLEX_REVIEW_CLASSES = frozenset(
    {
        "CONFLICT",
        "AMBIGUOUS",
        "COLOCATED_MULTI_OPERATOR",
        "UNRESOLVED",
    }
)


def is_review_queue_eligible(row: dict[str, Any]) -> bool:
    """Éligibilité Review Queue = requires_human_review, sauf exclusion métier explicite.

    Aucune exclusion métier n’est actuellement configurée : toute ligne marquée
    requires_human_review=true doit pouvoir être enfilée (sous plafond max_items).
    """
    if not row.get("requires_human_review"):
        return False
    # Hook documenté pour exclusions futures (ex. : statut institutionnel gelé).
    if row.get("review_queue_excluded") is True:
        return False
    return True


def operational_review_lane(row: dict[str, Any]) -> str | None:
    """Bande analytique FAST_REVIEW_CANDIDATE | COMPLEX_REVIEW (non métier)."""
    if not row.get("requires_human_review"):
        return None
    cls = row.get("classification")
    if cls in FAST_REVIEW_CLASSES:
        return "FAST_REVIEW_CANDIDATE"
    if cls in COMPLEX_REVIEW_CLASSES:
        return "COMPLEX_REVIEW"
    return "COMPLEX_REVIEW"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _norm_text(value: Any) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return re.sub(r"[^A-Z0-9]+", " ", text.upper()).strip()


def _norm_operator(value: Any) -> str:
    t = _norm_text(value)
    for key in OPERATOR_PARTITIONS:
        if key in t:
            return key
    return t or "UNKNOWN"


def normalize_status(value: Any) -> tuple[str, str]:
    original = "" if value is None else str(value).strip()
    key = re.sub(r"\s+", " ", original.upper()).strip()
    key_compact = key.replace(" ", "")
    mapped = STATUS_MAP.get(key) or STATUS_MAP.get(key_compact)
    if mapped:
        return original, mapped
    if "PLAN" in key:
        return original, "PLANNED"
    if "OUT" in key and "SERVICE" in key:
        return original, "OUT_OF_SERVICE"
    if "TX" in key:
        return original, "TX_ONLY"
    if "ONLINE" in key:
        return original, "ONLINE"
    if "SERVICE" in key:
        return original, "IN_SERVICE"
    return original, "UNKNOWN"


def normalize_rat(value: Any) -> dict[str, Any]:
    original = "" if value is None else str(value).strip()
    upper = original.upper().replace("+", "/").replace("_", "/").replace("-", "/")
    tokens = re.findall(r"2G|3G|4G|5G|FDD|TDD|RCS", upper)
    # Also catch glued forms like 2G3G4G
    if not tokens and upper:
        tokens = re.findall(r"2G|3G|4G|5G|FDD|TDD|RCS", re.sub(r"([^A-Z0-9])", "", upper))
        glued = re.sub(r"[^A-Z0-9]", "", upper)
        for tech in ("2G", "3G", "4G", "5G"):
            if tech in glued and tech not in tokens:
                tokens.append(tech)
        for tech in ("FDD", "TDD", "RCS"):
            if tech in glued and tech not in tokens:
                tokens.append(tech)
    uniq = []
    for t in tokens:
        if t not in uniq:
            uniq.append(t)
    return {
        "rat_original": original,
        "rat_normalized": "/".join(uniq) if uniq else "",
        "has_2g": "2G" in uniq,
        "has_3g": "3G" in uniq,
        "has_4g": "4G" in uniq,
        "has_5g": "5G" in uniq,
        "has_fdd": "FDD" in uniq,
        "has_tdd": "TDD" in uniq,
        "has_rcs": "RCS" in uniq,
    }


def parse_coordinate(value: Any) -> tuple[float | None, str | None]:
    """Return (float_or_None, quarantine_reason_or_None)."""
    if value is None:
        return None, "missing"
    if isinstance(value, (int, float)):
        if isinstance(value, float) and math.isnan(value):
            return None, "nan"
        return float(value), None
    text = str(value).strip()
    if not text:
        return None, "empty"
    if "REF!" in text.upper() or text.startswith("#"):
        return None, "excel_error_ref"
    try:
        return float(text.replace(",", ".")), None
    except ValueError:
        return None, "non_numeric"


def validate_lonlat(lat: float | None, lon: float | None, lat_reason: str | None, lon_reason: str | None) -> dict[str, Any]:
    reasons = [r for r in (lat_reason, lon_reason) if r]
    if lat is None or lon is None:
        return {"valid": False, "latitude": lat, "longitude": lon, "reasons": reasons or ["incomplete"]}
    if (lat, lon) == (0.0, 0.0):
        return {"valid": False, "latitude": lat, "longitude": lon, "reasons": ["zero_zero_rejected"]}
    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        return {"valid": False, "latitude": lat, "longitude": lon, "reasons": ["out_of_bounds"]}
    # Soft RDC envelope (not deletion — flag only when outside loose box)
    if not (-14.0 <= lat <= 6.0 and 11.0 <= lon <= 32.0):
        return {"valid": True, "latitude": lat, "longitude": lon, "reasons": ["outside_rdc_soft_bounds"], "soft_warning": True}
    return {"valid": True, "latitude": lat, "longitude": lon, "reasons": []}


def haversine_m(a: tuple[float, float], b: tuple[float, float]) -> float:
    x1, y1, x2, y2 = map(math.radians, (a[0], a[1], b[0], b[1]))
    v = math.sin((x2 - x1) / 2) ** 2 + math.cos(x1) * math.cos(x2) * math.sin((y2 - y1) / 2) ** 2
    return 6371000.0 * 2 * math.asin(min(1.0, math.sqrt(v)))


def name_similarity(a: str, b: str) -> float:
    na, nb = _norm_text(a), _norm_text(b)
    if not na or not nb:
        return 0.0
    if na == nb:
        return 1.0
    ta, tb = set(na.split()), set(nb.split())
    if not ta or not tb:
        return 0.0
    inter = len(ta & tb)
    return inter / max(len(ta), len(tb))


@dataclass
class MnoSourceMeta:
    file_name: str
    file_path: str
    file_size: int
    sha256: str
    ingested_at: str
    total_rows: int
    columns: list[str]
    operators_detected: dict[str, int]
    statuses_detected: dict[str, int]
    rats_detected: dict[str, int]
    valid_coordinates: int
    invalid_coordinates: int
    quarantined_rows: int
    engine_version: str = ENGINE_VERSION
    rule_version: str = RULE_VERSION


@dataclass
class MnoAuditState:
    executed: bool = False
    source_loaded: bool = False
    message: str = "Aucun audit MNO n’a encore été exécuté. Chargez une source MNO validée pour démarrer une analyse."
    automatic_replacement: bool = False
    physical_deletion: bool = False
    meta: dict[str, Any] | None = None
    kpis: dict[str, Any] = field(default_factory=dict)
    operators: list[dict[str, Any]] = field(default_factory=list)
    rows: list[dict[str, Any]] = field(default_factory=list)
    colocations: list[dict[str, Any]] = field(default_factory=list)
    performance: dict[str, Any] = field(default_factory=dict)
    national_infra_count: int | None = None
    potential_kpi_estimate: dict[str, Any] = field(default_factory=dict)
    coherence: dict[str, Any] = field(default_factory=dict)
    review_enqueued: int = 0


_STATE = MnoAuditState()


def get_state() -> MnoAuditState:
    return _STATE


def reset_state() -> None:
    global _STATE
    _STATE = MnoAuditState()


def fingerprint_source(path: Path) -> dict[str, Any]:
    data = path.read_bytes()
    return {
        "file_name": path.name,
        "file_path": str(path.resolve()),
        "file_size": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
        "ingested_at": _now(),
    }


def _load_excel_rows(path: Path) -> tuple[list[str], list[tuple[Any, ...]]]:
    import openpyxl

    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    try:
        ws = wb.active
        it = ws.iter_rows(values_only=True)
        header = [str(c).strip() if c is not None else "" for c in next(it)]
        rows = [tuple(r) for r in it]
        return header, rows
    finally:
        wb.close()


def _col_index(header: list[str], *aliases: str) -> int | None:
    normalized = {_norm_text(h): i for i, h in enumerate(header)}
    for alias in aliases:
        idx = normalized.get(_norm_text(alias))
        if idx is not None:
            return idx
    return None


def ingest_mno_rows(path: Path | None = None) -> tuple[MnoSourceMeta, list[dict[str, Any]]]:
    source = Path(path) if path else DEFAULT_SOURCE
    if not source.is_file():
        raise FileNotFoundError(f"Source MNO introuvable: {source}")
    fp = fingerprint_source(source)
    header, raw_rows = _load_excel_rows(source)
    i_name = _col_index(header, "Site Name", "site_name", "name") or 0
    i_lat = _col_index(header, "Latitude", "lat") or 1
    i_lon = _col_index(header, "Longitude", "lon", "lng") or 2
    i_rat = _col_index(header, "RAT", "technology") or 3
    i_status = _col_index(header, "Status", "statut") or 4
    i_op = _col_index(header, "Operator name", "Operator", "opérateur") or 5

    rows: list[dict[str, Any]] = []
    ops_c: Counter[str] = Counter()
    st_c: Counter[str] = Counter()
    rat_c: Counter[str] = Counter()
    valid = invalid = quarantined = 0

    for row_num, raw in enumerate(raw_rows, start=2):
        site_name = raw[i_name] if i_name < len(raw) else None
        lat_raw = raw[i_lat] if i_lat < len(raw) else None
        lon_raw = raw[i_lon] if i_lon < len(raw) else None
        rat_raw = raw[i_rat] if i_rat < len(raw) else None
        status_raw = raw[i_status] if i_status < len(raw) else None
        op_raw = raw[i_op] if i_op < len(raw) else None

        lat, lat_reason = parse_coordinate(lat_raw)
        lon, lon_reason = parse_coordinate(lon_raw)
        geom = validate_lonlat(lat, lon, lat_reason, lon_reason)
        status_original, status_norm = normalize_status(status_raw)
        rat = normalize_rat(rat_raw)
        operator = _norm_operator(op_raw)
        partition = OPERATOR_PARTITIONS.get(operator, f"MNO_{operator}")

        if geom["valid"]:
            valid += 1
        else:
            invalid += 1
            quarantined += 1

        ops_c[operator] += 1
        st_c[status_norm] += 1
        if rat["rat_normalized"]:
            rat_c[rat["rat_normalized"]] += 1
        elif rat["rat_original"]:
            rat_c[str(rat["rat_original"])[:48]] += 1

        rows.append(
            {
                "row_id": f"MNO-R{row_num}",
                "source_file": fp["file_name"],
                "source_row": row_num,
                "source_hash": fp["sha256"],
                "partition": partition,
                "operator": operator,
                "operator_original": "" if op_raw is None else str(op_raw),
                "site_name_original": "" if site_name is None else str(site_name),
                "site_name_normalized": _norm_text(site_name),
                "latitude_original": lat_raw if not isinstance(lat_raw, float) else lat_raw,
                "longitude_original": lon_raw if not isinstance(lon_raw, float) else lon_raw,
                "latitude": geom["latitude"],
                "longitude": geom["longitude"],
                "geometry_valid": geom["valid"],
                "quarantine": not geom["valid"],
                "quarantine_reasons": list(geom["reasons"]),
                "status_original": status_original,
                "status_normalized": status_norm,
                "rat_original": rat["rat_original"],
                "rat": rat,
                "classification": "INVALID_GEOMETRY" if not geom["valid"] else "UNRESOLVED",
                "secondary_flags": [],
                "confidence": 0.0,
                "score": 0.0,
                "match": None,
                "collocation_group_id": None,
                "evidence": [],
                "rules_applied": [],
                "requires_human_review": not geom["valid"],
                "engine_version": ENGINE_VERSION,
                "rule_version": RULE_VERSION,
            }
        )

    meta = MnoSourceMeta(
        file_name=fp["file_name"],
        file_path=fp["file_path"],
        file_size=fp["file_size"],
        sha256=fp["sha256"],
        ingested_at=fp["ingested_at"],
        total_rows=len(rows),
        columns=header,
        operators_detected=dict(ops_c),
        statuses_detected=dict(st_c),
        rats_detected=dict(rat_c.most_common(40)),
        valid_coordinates=valid,
        invalid_coordinates=invalid,
        quarantined_rows=quarantined,
    )
    return meta, rows


def load_telecom_infrastructure(limit: int | None = None) -> list[dict[str, Any]]:
    """Lecture seule du référentiel national actuel (KPI 14 580 en mode DB)."""
    try:
        from api.config import DATA_MODE, connect_db
        from psycopg2.extras import RealDictCursor
    except Exception:
        return []
    if DATA_MODE != "db":
        return []
    sql = """
        SELECT i.id, i.infra_code, i.infra_name, i.infra_type, i.technology,
               i.province, i.territoire, i.status, i.latitude, i.longitude,
               o.operator_code, o.operator_name
        FROM telecom.infrastructure i
        JOIN telecom.operators o ON o.id = i.operator_id
        WHERE i.latitude IS NOT NULL AND i.longitude IS NOT NULL
          AND NOT (i.latitude = 0 AND i.longitude = 0)
    """
    if limit:
        sql += f" LIMIT {int(limit)}"
    try:
        with connect_db() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(sql)
                return [dict(r) for r in cur.fetchall()]
    except Exception:
        return []


def count_telecom_infrastructure() -> int | None:
    try:
        from api.config import DATA_MODE, connect_db
    except Exception:
        return None
    if DATA_MODE != "db":
        return 14580  # fallback documenté (mode JSON)
    try:
        with connect_db() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM telecom.infrastructure")
                return int(cur.fetchone()[0])
    except Exception:
        return None


class SpatialGrid:
    def __init__(self, points: Iterable[dict[str, Any]], cell_deg: float = 0.02):
        self.cell = cell_deg
        self.items = list(points)
        self.grid: dict[tuple[int, int], list[int]] = defaultdict(list)
        for i, p in enumerate(self.items):
            try:
                lat, lon = float(p["latitude"]), float(p["longitude"])
            except (TypeError, ValueError, KeyError):
                continue
            self.grid[(math.floor(lat / cell_deg), math.floor(lon / cell_deg))].append(i)

    def nearby(self, lat: float, lon: float, radius_m: float) -> list[tuple[dict[str, Any], float]]:
        # ~111 km per degree
        n = max(1, math.ceil((radius_m / 1000.0) / (111 * self.cell)))
        cell = (math.floor(lat / self.cell), math.floor(lon / self.cell))
        out: list[tuple[dict[str, Any], float]] = []
        for dx in range(cell[0] - n, cell[0] + n + 1):
            for dy in range(cell[1] - n, cell[1] + n + 1):
                for i in self.grid.get((dx, dy), ()):
                    p = self.items[i]
                    d = haversine_m((lat, lon), (float(p["latitude"]), float(p["longitude"])))
                    if d <= radius_m:
                        out.append((p, d))
        out.sort(key=lambda x: x[1])
        return out


def _classify_row(
    row: dict[str, Any],
    matches: list[tuple[dict[str, Any], float]],
    coloc_ops: set[str],
    same_op_dupes: int,
) -> None:
    evidence: list[dict[str, Any]] = []
    rules: list[str] = []
    flags: list[str] = []

    if row["quarantine"]:
        row["classification"] = "INVALID_GEOMETRY"
        row["confidence"] = 1.0
        row["score"] = 0.0
        row["requires_human_review"] = True
        row["evidence"] = [{"type": "QUARANTINE", "reasons": row["quarantine_reasons"]}]
        row["rules_applied"] = ["REJECT_INVALID_GEOMETRY", "REJECT_ZERO_ZERO"]
        return

    best = matches[0] if matches else None
    distance = best[1] if best else None
    infra = best[0] if best else None
    op = row["operator"]
    status = row["status_normalized"]
    name_sim = name_similarity(row["site_name_original"], infra.get("infra_name") if infra else "") if infra else 0.0

    if infra and distance is not None:
        evidence.append(
            {
                "type": "SPATIAL_MATCH",
                "infra_id": infra.get("id"),
                "infra_name": infra.get("infra_name"),
                "infra_operator": infra.get("operator_code") or infra.get("operator_name"),
                "distance_m": round(distance, 2),
                "name_similarity": round(name_sim, 3),
            }
        )
        row["match"] = {
            "infra_id": infra.get("id"),
            "infra_name": infra.get("infra_name"),
            "infra_operator": infra.get("operator_code") or infra.get("operator_name"),
            "distance_m": round(distance, 2),
            "name_similarity": round(name_sim, 3),
            "province": infra.get("province"),
            "territoire": infra.get("territoire"),
        }

    infra_op = _norm_operator((infra or {}).get("operator_code") or (infra or {}).get("operator_name"))
    operator_agree = bool(infra and op and infra_op and op == infra_op)

    if distance is not None and distance <= THRESHOLDS_M["exact"]:
        rules.append("EXACT_COORDINATE_MATCH")
    elif distance is not None and distance <= THRESHOLDS_M["very_close"]:
        rules.append("VERY_CLOSE_SPATIAL_MATCH")
    elif distance is not None and distance <= THRESHOLDS_M["nearby"]:
        rules.append("NEARBY_SPATIAL_CANDIDATE")

    if name_sim >= 0.75:
        rules.append("NAME_SIMILARITY_HIGH")
    elif name_sim >= 0.4:
        rules.append("NAME_SIMILARITY_PARTIAL")

    if operator_agree:
        rules.append("OPERATOR_AGREEMENT")
    elif infra and op and infra_op and op != infra_op:
        rules.append("OPERATOR_DIFFERENT_ON_NEAR_INFRA")

    if len(coloc_ops) >= 2:
        flags.append("COLOCATED_MULTI_OPERATOR")
        rules.append("COLLOCATION_MULTI_OPERATOR")

    if same_op_dupes >= 2:
        flags.append("POSSIBLE_DUPLICATE")
        rules.append("INTRA_OPERATOR_SAME_COORD")

    if status == "PLANNED":
        flags.append("PLANNED_SITE")
        rules.append("STATUS_PLANNED")

    # Conflit : proximité forte mais noms très différents + opérateurs incompatibles sans co-loc claire
    conflict = (
        distance is not None
        and distance <= THRESHOLDS_M["very_close"]
        and name_sim < 0.2
        and not operator_agree
        and len(coloc_ops) < 2
    )
    if conflict:
        row["classification"] = "CONFLICT"
        row["confidence"] = 0.55
        row["score"] = 40
        row["requires_human_review"] = True
        row["secondary_flags"] = flags
        row["evidence"] = evidence
        row["rules_applied"] = rules + ["CONFLICT_NEAR_DISSIMILAR"]
        return

    if same_op_dupes >= 2 and (distance is None or distance <= THRESHOLDS_M["very_close"]):
        row["classification"] = "POSSIBLE_DUPLICATE"
        row["confidence"] = 0.7
        row["score"] = 55
        row["requires_human_review"] = True
        sec = [f for f in flags if f != "POSSIBLE_DUPLICATE"]
        if status == "PLANNED" and "PLANNED_SITE" not in sec:
            sec.append("PLANNED_SITE")
        row["secondary_flags"] = sec
        row["evidence"] = evidence
        row["rules_applied"] = rules
        return

    if distance is not None and distance <= THRESHOLDS_M["very_close"]:
        if operator_agree or name_sim >= 0.5:
            row["classification"] = "MATCH_EXISTING_INFRASTRUCTURE"
            row["confidence"] = 0.9 if distance <= THRESHOLDS_M["exact"] else 0.8
            row["score"] = 92 if distance <= THRESHOLDS_M["exact"] else 85
            row["requires_human_review"] = False
        else:
            row["classification"] = "OPERATOR_PRESENCE_ON_EXISTING_INFRASTRUCTURE"
            row["confidence"] = 0.78
            row["score"] = 80
            row["requires_human_review"] = len(coloc_ops) >= 2
        if "COLOCATED_MULTI_OPERATOR" in flags:
            row["secondary_flags"] = flags
            if row["classification"] != "OPERATOR_PRESENCE_ON_EXISTING_INFRASTRUCTURE":
                # Promote co-loc awareness without losing match
                row["secondary_flags"] = list(dict.fromkeys(flags + ["MATCH_WITH_COLLOCATION"]))
        if status == "PLANNED":
            row["secondary_flags"] = list(dict.fromkeys((row.get("secondary_flags") or []) + ["PLANNED_SITE"]))
            row["requires_human_review"] = True
        row["evidence"] = evidence
        row["rules_applied"] = rules
        return

    if distance is not None and distance <= THRESHOLDS_M["nearby"]:
        row["classification"] = "AMBIGUOUS"
        row["confidence"] = 0.45 + 0.2 * name_sim
        row["score"] = 50
        row["requires_human_review"] = True
        row["secondary_flags"] = flags
        row["evidence"] = evidence
        row["rules_applied"] = rules + ["WEAK_SPATIAL_CANDIDATE"]
        return

    if status == "PLANNED":
        row["classification"] = "PLANNED_SITE"
        row["confidence"] = 0.85
        row["score"] = 70
        row["requires_human_review"] = False
        row["secondary_flags"] = flags
        row["evidence"] = evidence
        row["rules_applied"] = rules
        return

    if len(coloc_ops) >= 2:
        row["classification"] = "COLOCATED_MULTI_OPERATOR"
        row["confidence"] = 0.75
        row["score"] = 65
        row["requires_human_review"] = True
        row["secondary_flags"] = flags
        row["evidence"] = evidence
        row["rules_applied"] = rules
        return

    # Pas de voisin infrastructure → nouvelle infrastructure candidate (opérationnelle)
    if status in {"ONLINE", "IN_SERVICE", "TX_ONLY"}:
        row["classification"] = "NEW_INFRASTRUCTURE_CANDIDATE"
        row["confidence"] = 0.6
        row["score"] = 60
        row["requires_human_review"] = True
        row["secondary_flags"] = flags
        row["evidence"] = evidence
        row["rules_applied"] = rules + ["NO_NEARBY_INFRASTRUCTURE"]
        return

    row["classification"] = "UNRESOLVED"
    row["confidence"] = 0.3
    row["score"] = 20
    row["requires_human_review"] = True
    row["secondary_flags"] = flags
    row["evidence"] = evidence
    row["rules_applied"] = rules + ["FALLBACK_UNRESOLVED"]


def _coord_group_stats(rows: list[dict[str, Any]], *, mode: str) -> dict[str, int]:
    """Statistiques de groupes de coordonnées (mode exact_float | round_6dp)."""
    groups: dict[Any, list[dict[str, Any]]] = defaultdict(list)
    for r in rows:
        if not r.get("geometry_valid"):
            continue
        lat, lon = float(r["latitude"]), float(r["longitude"])
        if mode == "exact_float":
            key: Any = (lat, lon)
        else:
            key = f"{lat:.6f}|{lon:.6f}"
        groups[key].append(r)
    dup = {k: v for k, v in groups.items() if len(v) >= 2}
    multi = [v for v in dup.values() if len({x["operator"] for x in v}) >= 2]
    same = [v for v in dup.values() if len({x["operator"] for x in v}) == 1]
    return {
        "groups": len(dup),
        "multi_operator_groups": len(multi),
        "same_operator_groups": len(same),
        "member_rows": sum(len(v) for v in dup.values()),
        "multi_operator_member_rows": sum(len(v) for v in multi),
    }


def build_colocations(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Groupes de co-localisation MNO.

    Règle Phase 5 : égalité après arrondi lat/lon à 6 décimales (~0,11 m).
    Pas de rayon PostGIS ni de tolérance spatiale au-delà de cet arrondi.
    Les groupes « exact_float » (égalité Python stricte) sont documentés à part.
    """
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for r in rows:
        if not r.get("geometry_valid"):
            continue
        key = f"{float(r['latitude']):.6f}|{float(r['longitude']):.6f}"
        groups[key].append(r)

    colocations = []
    gid = 0
    for key, members in groups.items():
        if len(members) < 2:
            continue
        ops = sorted({m["operator"] for m in members})
        gid += 1
        group_id = f"COLLOC-{gid:04d}"
        for m in members:
            m["collocation_group_id"] = group_id
        lat, lon = key.split("|")
        colocations.append(
            {
                "collocation_group_id": group_id,
                "geometry": {"type": "Point", "coordinates": [float(lon), float(lat)]},
                "operator_count": len(ops),
                "operators": ops,
                "member_count": len(members),
                "member_sites": [
                    {
                        "row_id": m["row_id"],
                        "site_name_original": m["site_name_original"],
                        "operator": m["operator"],
                        "status_normalized": m["status_normalized"],
                        "classification": m.get("classification"),
                    }
                    for m in members
                ],
                "confidence": 0.95 if len(ops) >= 2 else 0.7,
                "multi_operator": len(ops) >= 2,
                "coordinate_rule": "round_6_decimal_places",
                "existing_infrastructure_candidate": next(
                    (m.get("match") for m in members if m.get("match")),
                    None,
                ),
            }
        )
    return colocations


def reconcile(rows: list[dict[str, Any]], telecom: list[dict[str, Any]]) -> dict[str, Any]:
    t0 = time.perf_counter()
    grid = SpatialGrid(telecom, cell_deg=0.02) if telecom else None
    # Intra-operator exact coord counts
    op_coord: Counter[tuple[str, str]] = Counter()
    for r in rows:
        if r.get("geometry_valid"):
            key = (r["operator"], f"{float(r['latitude']):.6f}|{float(r['longitude']):.6f}")
            op_coord[key] += 1

    # Precompute multi-op coloc sets
    coord_ops: dict[str, set[str]] = defaultdict(set)
    for r in rows:
        if r.get("geometry_valid"):
            key = f"{float(r['latitude']):.6f}|{float(r['longitude']):.6f}"
            coord_ops[key].add(r["operator"])

    matched = 0
    for r in rows:
        if not r.get("geometry_valid"):
            _classify_row(r, [], set(), 0)
            continue
        key = f"{float(r['latitude']):.6f}|{float(r['longitude']):.6f}"
        matches = grid.nearby(float(r["latitude"]), float(r["longitude"]), THRESHOLDS_M["nearby"]) if grid else []
        same_dupes = op_coord[(r["operator"], key)]
        _classify_row(r, matches, coord_ops.get(key, set()), same_dupes)
        if r.get("match"):
            matched += 1

    colocations = build_colocations(rows)
    # After colocations, promote secondary flag for multi-op groups without overwriting stronger classes
    multi_ids = {c["collocation_group_id"] for c in colocations if c["multi_operator"]}
    for r in rows:
        if r.get("collocation_group_id") in multi_ids:
            flags = list(r.get("secondary_flags") or [])
            if "COLOCATED_MULTI_OPERATOR" not in flags and r["classification"] != "COLOCATED_MULTI_OPERATOR":
                flags.append("COLOCATED_MULTI_OPERATOR")
                r["secondary_flags"] = flags

    return {
        "telecom_indexed": len(telecom),
        "rows_with_match_payload": matched,
        "reconcile_ms": round((time.perf_counter() - t0) * 1000, 2),
        "colocations": colocations,
    }


def _build_coherence(
    rows: list[dict[str, Any]],
    by_class: Counter,
    colocations: list[dict[str, Any]],
) -> dict[str, Any]:
    """Classification exclusive vs indicateurs transversaux (anti double-comptage)."""
    exclusive_rows = [{"classification": c, "count": int(by_class.get(c, 0))} for c in CLASSIFICATIONS]
    exclusive_sum = sum(x["count"] for x in exclusive_rows)
    planned_status = sum(1 for r in rows if r.get("status_normalized") == "PLANNED")
    review_rows = [r for r in rows if r.get("requires_human_review")]
    review_by_class = Counter(r["classification"] for r in review_rows)
    secondary = Counter()
    for r in rows:
        for f in r.get("secondary_flags") or []:
            secondary[f] += 1

    coloc_flag_rows = sum(
        1
        for r in rows
        if r["classification"] == "COLOCATED_MULTI_OPERATOR"
        or "COLOCATED_MULTI_OPERATOR" in (r.get("secondary_flags") or [])
    )
    planned_flag_rows = sum(
        1
        for r in rows
        if r["classification"] == "PLANNED_SITE" or "PLANNED_SITE" in (r.get("secondary_flags") or [])
    )
    new_rows = [r for r in rows if r["classification"] == "NEW_INFRASTRUCTURE_CANDIDATE"]
    exact_float = _coord_group_stats(rows, mode="exact_float")
    round_6 = _coord_group_stats(rows, mode="round_6dp")
    multi_coloc = sum(1 for c in colocations if c["multi_operator"])

    return {
        "population_total": len(rows),
        "exclusive_classification": {
            "rule": "Chaque ligne MNO a exactement une classification primaire finale.",
            "rows": exclusive_rows,
            "checksum": exclusive_sum,
            "checksum_ok": exclusive_sum == len(rows),
        },
        "transversal_indicators": {
            "rule": (
                "Indicateurs non exclusifs : une même ligne peut apparaître dans plusieurs "
                "compteurs. Ne pas additionner avec la classification primaire pour retrouver 12 615."
            ),
            "planned_status_normalized": planned_status,
            "planned_primary_or_flag": planned_flag_rows,
            "colocated_multi_operator_flag_rows": coloc_flag_rows,
            "possible_duplicate_primary": by_class["POSSIBLE_DUPLICATE"],
            "ambiguous_primary": by_class["AMBIGUOUS"],
            "conflict_primary": by_class["CONFLICT"],
            "needs_human_review_unique_rows": len(review_rows),
            "invalid_geometry_primary": by_class["INVALID_GEOMETRY"],
            "secondary_flags": dict(secondary),
            "planned_status_by_primary_classification": dict(
                Counter(r["classification"] for r in rows if r.get("status_normalized") == "PLANNED")
            ),
        },
        "human_review": {
            "unique_rows_requiring_review": len(review_rows),
            "unique_rows_review_queue_eligible": count_review_eligible(rows),
            "eligibility_equals_requires_human_review": count_review_eligible(rows) == len(review_rows),
            "by_primary_classification": dict(review_by_class),
            "operational_lanes": {
                "FAST_REVIEW_CANDIDATE": sum(
                    1 for r in review_rows if operational_review_lane(r) == "FAST_REVIEW_CANDIDATE"
                ),
                "COMPLEX_REVIEW": sum(1 for r in review_rows if operational_review_lane(r) == "COMPLEX_REVIEW"),
                "definition_fast": sorted(FAST_REVIEW_CLASSES),
                "definition_complex": sorted(COMPLEX_REVIEW_CLASSES),
                "analytical_only": True,
            },
            "note": (
                "Compte unique de lignes (requires_human_review=true). "
                "Éligibilité Review Queue = même ensemble (is_review_queue_eligible). "
                "Ne pas additionner ambiguïtés+conflits+doublons : chevauchement possible via flags."
            ),
        },
        "colocation_metrics": {
            "phase5_rule": "round_6_decimal_places",
            "phase5_uses_postgis_radius": False,
            "phase5_uses_spatial_tolerance_beyond_rounding": False,
            "exact_coordinate_groups_float_equality": exact_float,
            "spatial_colocation_groups_round_6dp": round_6,
            "phase5_groups_total": len(colocations),
            "phase5_groups_multi_operator": multi_coloc,
            "exploratory_vs_phase5": (
                "L’audit exploratoire (~721 groupes / ~712 multi-op) se rapproche de l’égalité "
                f"float stricte ({exact_float['groups']} / {exact_float['multi_operator_groups']}). "
                f"Phase 5 publie {len(colocations)} / {multi_coloc} via arrondi à 6 décimales, "
                "qui fusionne des couples non bit-identiques mais géographiquement indistinguables."
            ),
        },
        "new_infrastructure_candidates": {
            "count": len(new_rows),
            "none_also_classified_as_existing_match": all(
                r["classification"] == "NEW_INFRASTRUCTURE_CANDIDATE" and not r.get("match") for r in new_rows
            ),
            "theoretical_kpi_if_all_validated": None,  # filled by caller with national
            "official_kpi_remains_national_count": True,
        },
    }


def _aggregate(rows: list[dict[str, Any]], meta: MnoSourceMeta, national_count: int | None, colocations: list[dict[str, Any]]) -> dict[str, Any]:
    by_class = Counter(r["classification"] for r in rows)
    by_op = Counter(r["operator"] for r in rows)
    by_status = Counter(r.get("status_normalized") or "UNKNOWN" for r in rows)
    op_stats = []
    for op in ("VODACOM", "AIRTEL", "ORANGE", "AFRICELL"):
        subset = [r for r in rows if r["operator"] == op]
        op_stats.append(
            {
                "operator": op,
                "partition": OPERATOR_PARTITIONS[op],
                "total": len(subset),
                "match_existing": sum(1 for r in subset if r["classification"] == "MATCH_EXISTING_INFRASTRUCTURE"),
                "operator_presence": sum(1 for r in subset if r["classification"] == "OPERATOR_PRESENCE_ON_EXISTING_INFRASTRUCTURE"),
                "new_candidates": sum(1 for r in subset if r["classification"] == "NEW_INFRASTRUCTURE_CANDIDATE"),
                "planned": sum(1 for r in subset if r.get("status_normalized") == "PLANNED"),
                "ambiguous": sum(1 for r in subset if r["classification"] == "AMBIGUOUS"),
                "conflict": sum(1 for r in subset if r["classification"] == "CONFLICT"),
                "duplicates": sum(1 for r in subset if r["classification"] == "POSSIBLE_DUPLICATE"),
                "invalid_geometry": sum(1 for r in subset if r["classification"] == "INVALID_GEOMETRY"),
            }
        )

    match_existing = by_class["MATCH_EXISTING_INFRASTRUCTURE"]
    presence = by_class["OPERATOR_PRESENCE_ON_EXISTING_INFRASTRUCTURE"]
    new_cand = by_class["NEW_INFRASTRUCTURE_CANDIDATE"]
    # Sites planifiés = statut MNO normalisé PLANNED (transversal, non exclusif).
    planned = sum(1 for r in rows if r.get("status_normalized") == "PLANNED")
    multi_coloc = sum(1 for c in colocations if c["multi_operator"])
    coherence = _build_coherence(rows, by_class, colocations)
    review_unique = coherence["human_review"]["unique_rows_requiring_review"]
    coherence["new_infrastructure_candidates"]["theoretical_kpi_if_all_validated"] = (
        (national_count + new_cand) if national_count is not None else None
    )
    coherence["new_infrastructure_candidates"]["formula"] = (
        f"{national_count} + {new_cand} = {national_count + new_cand}" if national_count is not None else None
    )

    # Estimation KPI potentielle — NON APPLIQUÉE / non officielle
    potential_new = new_cand
    estimate = {
        "current_national_infrastructure_kpi": national_count,
        "mno_rows_analyzed": len(rows),
        "must_not_replace_kpi_with_mno_rows": True,
        "must_not_sum_14580_plus_12615": True,
        "is_theoretical_scenario_only": True,
        "is_official_kpi": False,
        "potential_additional_physical_infrastructures_if_all_new_validated": potential_new,
        "potential_kpi_if_all_new_validated": (national_count + potential_new) if national_count is not None else None,
        "planned_sites_excluded_from_existing_kpi": planned,
        "operator_presence_does_not_create_new_infrastructure": presence,
        "new_candidates_exclusive_of_existing_match": coherence["new_infrastructure_candidates"][
            "none_also_classified_as_existing_match"
        ],
        "explanation": (
            "14 580 compte des infrastructures physiques dans telecom.infrastructure. "
            "12 615 sont des déclarations MNO (présence / site / projet). "
            "Une co-localisation multi-opérateurs n'ajoute pas N infrastructures. "
            "Les sites Planned n'augmentent pas le KPI « existantes ». "
            "14 580 + 943 = 15 523 est un scénario maximal théorique avant validation humaine, "
            "pas un nouveau KPI officiel."
        ),
    }

    kpis = {
        "mno_rows_analyzed": len(rows),
        "vodacom": by_op.get("VODACOM", 0),
        "airtel": by_op.get("AIRTEL", 0),
        "orange": by_op.get("ORANGE", 0),
        "africell": by_op.get("AFRICELL", 0),
        "by_status_normalized": dict(by_status),
        # Classification exclusive (somme = population)
        "match_existing_infrastructure": match_existing,
        "operator_presence_on_existing": presence,
        "new_infrastructure_candidates": new_cand,
        "planned_site_primary": by_class["PLANNED_SITE"],
        "possible_duplicates": by_class["POSSIBLE_DUPLICATE"],
        "colocated_classification": by_class["COLOCATED_MULTI_OPERATOR"],
        "ambiguous": by_class["AMBIGUOUS"],
        "conflicts": by_class["CONFLICT"],
        "invalid_geometry": by_class["INVALID_GEOMETRY"],
        "unresolved": by_class["UNRESOLVED"],
        "by_classification": dict(by_class),
        "exclusive_classification_checksum": sum(by_class.values()),
        # Transversal — ne pas sommer avec exclusive
        "planned_sites": planned,
        "planned_sites_is_transversal": True,
        "requires_human_review_unique": review_unique,
        "review_queue_eligible_unique": count_review_eligible(rows),
        "colocations_multi_operator": multi_coloc,
        "colocations_total_groups": len(colocations),
        "colocations_are_groups_not_rows": True,
        "national_infrastructure_kpi_unchanged": national_count,
        "source_sha256": meta.sha256,
        "valid_coordinates": meta.valid_coordinates,
        "invalid_coordinates": meta.invalid_coordinates,
    }
    return {
        "kpis": kpis,
        "operators": op_stats,
        "potential_kpi_estimate": estimate,
        "coherence": coherence,
    }


def count_review_eligible(rows: list[dict[str, Any]]) -> int:
    """Nombre unique de lignes techniquement éligibles à la Review Queue."""
    return sum(1 for r in rows if is_review_queue_eligible(r))


def enqueue_review_items(rows: list[dict[str, Any]], service=None, *, max_items: int = 500) -> int:
    """Réutilise la Review Queue Phase 4 pour les cas à revue humaine.

    Éligibilité = is_review_queue_eligible (requires_human_review=true).
    Ne crée jamais plus de max_items dossiers (défaut 500) — pas d’enqueue massif implicite.
    """
    if service is None:
        return 0
    from .operational import StoredCandidate, StoredDecision, StoredEvidence
    from .operational_service import sid

    run = service.start_run(
        f"mno-audit-{ENGINE_VERSION}",
        "MNO_OPERATORS_XLSX",
        "TELECOM_INFRASTRUCTURE",
        batch_size=100,
        max_candidates=max_items,
        timeout_seconds=600,
    )
    count = 0
    for r in rows:
        if not is_review_queue_eligible(r):
            continue
        if count >= max_items:
            break
        cid = sid("CAN", run.run_id, r["row_id"])
        payload = {
            "domain": "TELECOM_MNO",
            "ambiguity": "HIGH" if r["classification"] in {"AMBIGUOUS", "CONFLICT", "UNRESOLVED"} else "MEDIUM",
            "mno_classification": r["classification"],
            "operational_review_lane": operational_review_lane(r),
            "secondary_flags": r.get("secondary_flags") or [],
            "source_entity": {
                "entity_type": "MNO_SITE",
                "attributes": {
                    "name": r["site_name_original"],
                    "normalized_name": r["site_name_normalized"],
                    "latitude": r.get("latitude"),
                    "longitude": r.get("longitude"),
                    "operator": r["operator"],
                    "status": r["status_normalized"],
                    "quality_status": "QUARANTINE" if r.get("quarantine") else "MNO_DECLARED",
                    "provenance": {
                        "source_file": r["source_file"],
                        "source_row": r["source_row"],
                        "source_hash": r["source_hash"],
                    },
                },
            },
            "target_entity": {
                "entity_type": "TELECOM_INFRASTRUCTURE",
                "attributes": (r.get("match") or {}),
            },
            "evidence": r.get("evidence") or [],
            "rules_applied": r.get("rules_applied") or [],
        }
        candidate = StoredCandidate(
            cid,
            run.run_id,
            "MNO_OPERATORS_XLSX",
            r["row_id"],
            "TELECOM_INFRASTRUCTURE",
            str((r.get("match") or {}).get("infra_id") or "NONE"),
            float(r.get("score") or 0),
            float(r.get("confidence") or 0),
            "AMBIGUOUS" if r["classification"] in {"AMBIGUOUS", "CONFLICT", "UNRESOLVED"} else "PROBABLE_MATCH",
            f"Phase 5 MNO: {r['classification']} — revue humaine requise.",
            True,
            payload,
        )
        decision = StoredDecision(
            sid("DEC", cid, r["classification"]),
            cid,
            r["classification"],
            float(r.get("score") or 0),
            ENGINE_VERSION,
            RULE_VERSION,
            f"Classification MNO {r['classification']} soumise à revue (aucune fusion automatique).",
        )
        ev = (
            StoredEvidence(
                sid("E", cid, "CLASS"),
                cid,
                "MNO_CLASSIFICATION",
                "MNO_OPERATORS_XLSX",
                r["row_id"],
                [r["classification"]],
                10,
                float(r.get("confidence") or 0),
                0.9,
                {"status": "NEUTRAL", "method": "mno_audit_phase5", "extractor_version": ENGINE_VERSION},
            ),
        )
        service.persist_resolution(run, candidate, decision, ev)
        count += 1
    return count


def run_mno_audit(
    path: Path | None = None,
    *,
    telecom_points: list[dict[str, Any]] | None = None,
    enqueue_reviews: bool = False,
    review_service=None,
    max_review_items: int = 500,
) -> MnoAuditState:
    global _STATE
    t0 = time.perf_counter()
    meta, rows = ingest_mno_rows(path)
    t_ingest = time.perf_counter()
    telecom = telecom_points if telecom_points is not None else load_telecom_infrastructure()
    national = count_telecom_infrastructure()
    t_load = time.perf_counter()
    recon = reconcile(rows, telecom)
    colocations = recon["colocations"]
    t_recon = time.perf_counter()
    agg = _aggregate(rows, meta, national, colocations)
    review_count = 0
    if enqueue_reviews:
        review_count = enqueue_review_items(rows, review_service, max_items=max_review_items)
    t_end = time.perf_counter()

    state = MnoAuditState(
        executed=True,
        source_loaded=True,
        message=(
            "Audit MNO Phase 5 exécuté en lecture seule. "
            "Le KPI national d’infrastructures existantes n’a pas été modifié."
        ),
        automatic_replacement=False,
        physical_deletion=False,
        meta=asdict(meta),
        kpis=agg["kpis"],
        operators=agg["operators"],
        rows=rows,
        colocations=colocations,
        performance={
            "ingest_ms": round((t_ingest - t0) * 1000, 2),
            "telecom_load_ms": round((t_load - t_ingest) * 1000, 2),
            "reconcile_ms": recon["reconcile_ms"],
            "total_ms": round((t_end - t0) * 1000, 2),
            "telecom_indexed": recon["telecom_indexed"],
            "review_enqueue_ms": round((t_end - t_recon) * 1000, 2) if enqueue_reviews else 0,
        },
        national_infra_count=national,
        potential_kpi_estimate=agg["potential_kpi_estimate"],
        coherence=agg.get("coherence") or {},
        review_enqueued=review_count,
    )
    _STATE = state
    return state


def status_payload() -> dict[str, Any]:
    s = _STATE
    if not s.executed:
        return {
            "executed": False,
            "source_loaded": False,
            "operators": [],
            "message": s.message,
            "automatic_replacement": False,
            "physical_deletion": False,
            "engine_version": ENGINE_VERSION,
            "rule_version": RULE_VERSION,
        }
    return {
        "executed": True,
        "source_loaded": True,
        "message": s.message,
        "automatic_replacement": False,
        "physical_deletion": False,
        "engine_version": ENGINE_VERSION,
        "rule_version": RULE_VERSION,
        "meta": s.meta,
        "kpis": s.kpis,
        "operators": s.operators,
        "national_infra_count": s.national_infra_count,
        "potential_kpi_estimate": s.potential_kpi_estimate,
        "coherence": s.coherence,
        "performance": s.performance,
        "review_enqueued": s.review_enqueued,
        "paradox_explanation": (s.potential_kpi_estimate or {}).get("explanation"),
        "thresholds_m": THRESHOLDS_M,
    }


def list_rows(
    *,
    operator: str | None = None,
    classification: str | None = None,
    status: str | None = None,
    quarantine: bool | None = None,
    offset: int = 0,
    limit: int = 50,
) -> dict[str, Any]:
    rows = _STATE.rows
    if operator:
        op = _norm_operator(operator)
        rows = [r for r in rows if r["operator"] == op]
    if classification:
        rows = [r for r in rows if r["classification"] == classification]
    if status:
        rows = [r for r in rows if r["status_normalized"] == status.upper().replace(" ", "_")]
    if quarantine is not None:
        rows = [r for r in rows if bool(r.get("quarantine")) is quarantine]
    total = len(rows)
    page = rows[offset : offset + limit]
    return {"total": total, "offset": offset, "limit": limit, "items": page}


def list_colocations(*, multi_operator_only: bool = False, offset: int = 0, limit: int = 50) -> dict[str, Any]:
    rows = _STATE.colocations
    if multi_operator_only:
        rows = [c for c in rows if c.get("multi_operator")]
    return {"total": len(rows), "offset": offset, "limit": limit, "items": rows[offset : offset + limit]}


def nire_quality_status(row: dict[str, Any]) -> str:
    """Statut qualité cartographique — n'altère pas la classification métier.

    Une donnée NEEDS_REVIEW / CONFLICT reste visible (NIRE non bloquant).
    """
    cls = row.get("classification") or ""
    if cls == "INVALID_GEOMETRY":
        return "NEEDS_REVIEW"
    if cls == "CONFLICT":
        return "CONFLICT"
    if cls in {"AMBIGUOUS", "UNRESOLVED", "POSSIBLE_DUPLICATE"}:
        return "NEEDS_REVIEW"
    if cls == "NEW_INFRASTRUCTURE_CANDIDATE":
        return "PROVISIONAL"
    if cls == "MATCH_EXISTING_INFRASTRUCTURE" and not row.get("requires_human_review"):
        conf = float(row.get("confidence") or 0)
        return "VERIFIED" if conf >= 0.9 else "HIGH_CONFIDENCE"
    if cls == "MATCH_EXISTING_INFRASTRUCTURE":
        return "HIGH_CONFIDENCE"  # Planned match — visible, validation institutionnelle
    if cls in {"OPERATOR_PRESENCE_ON_EXISTING_INFRASTRUCTURE", "COLOCATED_MULTI_OPERATOR", "PLANNED_SITE"}:
        return "PROVISIONAL" if not row.get("requires_human_review") else "NEEDS_REVIEW"
    if row.get("requires_human_review"):
        return "NEEDS_REVIEW"
    return "PROVISIONAL"


def _feature_from_mno_row(r: dict[str, Any]) -> dict[str, Any]:
    rat = r.get("rat_normalized") or r.get("rat_original")
    return {
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [r["longitude"], r["latitude"]]},
        "properties": {
            "row_id": r["row_id"],
            "infra_name": r["site_name_original"],
            "site_name": r["site_name_original"],
            "name": r["site_name_original"],
            "operator": r["operator"],
            "operator_code": r["operator"],
            "operator_name": r["operator"].title() if r.get("operator") else None,
            "status": r.get("status_normalized"),
            "status_normalized": r.get("status_normalized"),
            "technology": rat,
            "rat": rat,
            "infra_type": "mno_declared_site",
            "nire_classification": r.get("classification"),
            "classification": r.get("classification"),
            "nire_quality_status": nire_quality_status(r),
            "requires_human_review": bool(r.get("requires_human_review")),
            "secondary_flags": r.get("secondary_flags") or [],
            "quarantine": r.get("quarantine"),
            "collocation_group_id": r.get("collocation_group_id"),
            "confidence": r.get("confidence"),
            "score": r.get("score"),
            "source_label": "FDSU MNO",
            "data_source": "FDSU_MNO_AUDIT",
            "provenance": {
                "source_file": r.get("source_file"),
                "source_row": r.get("source_row"),
                "source_hash": r.get("source_hash"),
            },
            "kpi_excluded": True,
        },
    }


def layer_geojson(
    operator: str | None = None,
    *,
    limit: int = 2000,
    include_planned: bool = True,
    planned_only: bool = False,
    ensure_loaded: bool = False,
) -> dict[str, Any]:
    """GeoJSON FDSU MNO pour Smart Map — visible même si NIRE NEEDS_REVIEW/CONFLICT."""
    if ensure_loaded and not _STATE.executed:
        try:
            run_mno_audit(enqueue_reviews=False)
        except Exception as exc:  # noqa: BLE001 — surface empty meta, don't crash map
            return {
                "type": "FeatureCollection",
                "features": [],
                "meta": {
                    "error": str(exc),
                    "source_immutable": True,
                    "kpi_national_untouched": True,
                    "audit_required": True,
                },
            }

    op = _norm_operator(operator) if operator else None
    features = []
    for r in _STATE.rows:
        if not r.get("geometry_valid"):
            continue
        if op and r["operator"] != op:
            continue
        if planned_only and r.get("status_normalized") != "PLANNED":
            continue
        if not include_planned and not planned_only and r.get("status_normalized") == "PLANNED":
            continue
        features.append(_feature_from_mno_row(r))
        if len(features) >= limit:
            break
    return {
        "type": "FeatureCollection",
        "features": features,
        "meta": {
            "operator": op,
            "partition": OPERATOR_PARTITIONS.get(op) if op else None,
            "returned": len(features),
            "capped": len(features) >= limit,
            "planned_only": planned_only,
            "source_immutable": True,
            "kpi_national_untouched": True,
            "nire_non_blocking": True,
            "audit_executed": _STATE.executed,
        },
    }
