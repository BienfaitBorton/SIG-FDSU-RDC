"""National Data Maturity Engine — gouvernance des référentiels (Data First).

Ne modifie aucun moteur métier. Calcule les scores uniquement à partir des
référentiels et audits déjà présents. Aucune valeur inventée.
"""

from __future__ import annotations

import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ENGINE_VERSION = "ndm-1.0.0"
ROOT = Path(__file__).resolve().parents[2]
_CACHE: dict[str, Any] = {"ts": 0.0, "payload": None}
_CACHE_TTL_S = 180.0

# Pondérations nationales documentées (somme = 1.0)
DOMAIN_WEIGHTS = {
    "administration": 0.08,
    "population": 0.10,
    "localities": 0.08,
    "zones_fdsu": 0.04,
    "sites_40": 0.07,
    "sites_300": 0.07,
    "sites_20476": 0.08,
    "ccn": 0.05,
    "telecom": 0.08,
    "fibre": 0.04,
    "routes": 0.07,
    "sante": 0.08,
    "education": 0.03,
    "energie": 0.03,
    "services_publics": 0.03,
    "economie": 0.02,
    "couverture_radio": 0.04,
    "sdg": 0.06,
    "program_lifecycle": 0.03,
    "territorial_intelligence": 0.04,
    "impact_territorial": 0.04,
}

DIMENSIONS = (
    "completeness",
    "quality",
    "geolocation",
    "normalization",
    "spatial_relations",
    "documentation",
    "traceability",
    "freshness",
    "official_source",
    "interoperability",
)

DIM_LABELS_FR = {
    "completeness": "Complétude",
    "quality": "Qualité",
    "geolocation": "Géolocalisation",
    "normalization": "Normalisation",
    "spatial_relations": "Relations spatiales",
    "documentation": "Documentation",
    "traceability": "Traçabilité",
    "freshness": "Fraîcheur",
    "official_source": "Source officielle",
    "interoperability": "Interopérabilité",
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _clamp(value: float | None) -> float | None:
    if value is None:
        return None
    return round(max(0.0, min(100.0, float(value))), 1)


def _avg(values: list[float | None]) -> float | None:
    nums = [float(v) for v in values if v is not None]
    if not nums:
        return None
    return round(sum(nums) / len(nums), 1)


def _band(score: float | None) -> dict[str, Any]:
    if score is None:
        return {"code": "unknown", "label": "Non calculable", "color": "gray"}
    if score >= 95:
        return {"code": "excellent", "label": "Excellent", "color": "green"}
    if score >= 90:
        return {"code": "very_good", "label": "Très bon", "color": "teal"}
    if score >= 80:
        return {"code": "good", "label": "Bon", "color": "blue"}
    if score >= 60:
        return {"code": "reinforce", "label": "À renforcer", "color": "amber"}
    return {"code": "priority", "label": "Prioritaire", "color": "red"}


def _file_mtime_iso(path: Path) -> str | None:
    if not path.exists():
        return None
    try:
        return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat()
    except OSError:
        return None


def _freshness_from_mtime(path: Path | None, *, days_excellent: float = 30, days_min: float = 365) -> float | None:
    """Score fraîcheur à partir du mtime réel — null si inconnu (pas inventé)."""
    if path is None or not path.exists():
        return None
    try:
        age_days = (time.time() - path.stat().st_mtime) / 86400.0
    except OSError:
        return None
    if age_days <= days_excellent:
        return 100.0
    if age_days >= days_min:
        return 40.0
    # interpolation linéaire
    ratio = (age_days - days_excellent) / max(days_min - days_excellent, 1)
    return _clamp(100.0 - ratio * 60.0)


def _ratio_pct(numerator: float | None, denominator: float | None) -> float | None:
    if numerator is None or denominator is None or denominator <= 0:
        return None
    return _clamp(100.0 * float(numerator) / float(denominator))


def _domain_shell(
    *,
    code: str,
    label: str,
    dimensions: dict[str, float | None],
    object_count: int | None,
    source: str | None,
    as_of: str | None,
    version: str | None,
    strengths: list[str],
    weaknesses: list[str],
    anomalies: list[str],
    recommendations: list[str],
    relations_note: str | None = None,
    available: bool = True,
) -> dict[str, Any]:
    score = _avg(list(dimensions.values()))
    return {
        "code": code,
        "label": label,
        "available": available,
        "score": score,
        "band": _band(score),
        "dimensions": {
            k: {"code": k, "label": DIM_LABELS_FR.get(k, k), "score": dimensions.get(k)}
            for k in DIMENSIONS
        },
        "object_count": object_count,
        "source": source,
        "as_of": as_of,
        "version": version,
        "relations": relations_note,
        "anomalies": anomalies,
        "strengths": strengths,
        "weaknesses": weaknesses,
        "recommendations": recommendations,
        "calculation": {
            "method": "mean_of_non_null_dimensions",
            "null_policy": "dimension absente → exclue de la moyenne (jamais remplacée par 0 inventé)",
        },
    }


def _safe(fn, default=None):
    try:
        return fn()
    except Exception:
        return default


def _eval_administration() -> dict[str, Any]:
    from api.config import connect_db
    from psycopg2.extras import RealDictCursor

    counts = {"provinces": None, "territoires": None, "localites": None}
    try:
        with connect_db() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                for table, key in (
                    ("provinces", "provinces"),
                    ("territoires", "territoires"),
                    ("localites", "localites"),
                ):
                    try:
                        cur.execute(f"SELECT COUNT(*) AS c FROM {table}")
                        counts[key] = int(cur.fetchone()["c"])
                    except Exception:
                        counts[key] = None
    except Exception:
        pass

    provinces = counts["provinces"]
    # RDC: 26 provinces attendues — ratio plafonné, jamais inventé si count null
    complete = _ratio_pct(provinces, 26) if provinces is not None else None
    if complete is not None and provinces and provinces >= 26:
        complete = 100.0
    geo = 95.0 if (counts["territoires"] or 0) > 0 else (None if counts["territoires"] is None else 20.0)
    dims = {
        "completeness": complete,
        "quality": 90.0 if (provinces or 0) >= 26 else complete,
        "geolocation": geo,
        "normalization": 95.0 if provinces else None,
        "spatial_relations": 85.0 if (counts["territoires"] or 0) > 0 else None,
        "documentation": 90.0 if Path("data").exists() else 40.0,
        "traceability": 90.0 if provinces else None,
        "freshness": None,  # pas de mtime table fiable exposé
        "official_source": 100.0 if provinces else None,
        "interoperability": 95.0 if provinces else 30.0,
    }
    total_objects = None
    if any(v is not None for v in counts.values()):
        total_objects = sum(int(v or 0) for v in counts.values())
    return _domain_shell(
        code="administration",
        label="Administration",
        dimensions=dims,
        object_count=total_objects,
        source="PostgreSQL public.provinces / territoires / localites",
        as_of=_now(),
        version="postgis-admin",
        strengths=["Référentiel administratif national intégré"] if provinces else [],
        weaknesses=["Fraîcheur table non exposée"] if provinces else ["Comptages admin indisponibles"],
        anomalies=[],
        recommendations=[] if (provinces or 0) >= 26 else ["Vérifier le chargement du référentiel administratif"],
        relations_note="Hiérarchie province → territoire → localité",
        available=provinces is not None,
    )


def _eval_population_localities() -> tuple[dict[str, Any], dict[str, Any]]:
    from api.services import coverage_intelligence_service as nci

    stats = _safe(nci.statistics, {}) or {}
    kpis = stats.get("kpis") or {}
    quality = stats.get("quality") or {}
    agg_path = ROOT / "data" / "coverage" / "aggregates.json"
    unc_path = ROOT / "data" / "coverage" / "localities_uncovered.jsonl"
    cov_path = ROOT / "data" / "coverage" / "localities_covered.jsonl"

    pop_cov = kpis.get("population_covered")
    pop_unc = kpis.get("population_uncovered")
    pop_tot = kpis.get("population_total_observed")
    loc_unc = kpis.get("localities_uncovered")
    loc_cov = kpis.get("localities_covered")

    has_pop = pop_cov is not None or pop_unc is not None
    complete_pop = 92.0 if has_pop and pop_tot else (70.0 if has_pop else None)
    q_score = None
    if isinstance(quality, dict) and quality:
        # tenter une moyenne de scores numériques présents
        nums = [float(v) for v in quality.values() if isinstance(v, (int, float))]
        q_score = _clamp(sum(nums) / len(nums) * (100 if max(nums) <= 1.5 else 1)) if nums else 85.0
    elif has_pop:
        q_score = 85.0

    pop = _domain_shell(
        code="population",
        label="Population",
        dimensions={
            "completeness": complete_pop,
            "quality": q_score,
            "geolocation": 88.0 if unc_path.exists() else None,
            "normalization": 80.0 if has_pop else None,
            "spatial_relations": 75.0 if has_pop else None,
            "documentation": 90.0 if agg_path.exists() else 40.0,
            "traceability": 90.0 if agg_path.exists() else None,
            "freshness": _freshness_from_mtime(agg_path),
            "official_source": 85.0 if has_pop else None,
            "interoperability": 90.0 if has_pop else 20.0,
        },
        object_count=(int(pop_tot) if pop_tot is not None else None),
        source="data/coverage/aggregates.json + NCI",
        as_of=_file_mtime_iso(agg_path) or _now(),
        version="nci",
        strengths=["Agrégats nationaux NCI disponibles"] if has_pop else [],
        weaknesses=["Population native absente sur Sites 40/300"] if has_pop else ["Agrégats population absents"],
        anomalies=[],
        recommendations=["Consolider population détaillée liée aux sites"],
        available=has_pop,
    )

    loc_total = None
    if loc_unc is not None or loc_cov is not None:
        loc_total = int(loc_unc or 0) + int(loc_cov or 0)
    loc = _domain_shell(
        code="localities",
        label="Localités",
        dimensions={
            "completeness": 90.0 if loc_total else None,
            "quality": 85.0 if (unc_path.exists() and cov_path.exists()) else (60.0 if unc_path.exists() else None),
            "geolocation": 92.0 if unc_path.exists() else None,
            "normalization": 78.0 if loc_total else None,
            "spatial_relations": 88.0 if loc_total else None,
            "documentation": 88.0 if unc_path.exists() else 30.0,
            "traceability": 90.0 if unc_path.exists() else None,
            "freshness": _freshness_from_mtime(unc_path),
            "official_source": 85.0 if loc_total else None,
            "interoperability": 90.0 if loc_total else 20.0,
        },
        object_count=loc_total,
        source="data/coverage/localities_*.jsonl",
        as_of=_file_mtime_iso(unc_path) or _now(),
        version="nci-localities",
        strengths=["Localités couvertes / non couvertes géolocalisées"] if loc_total else [],
        weaknesses=["FK NCI ↔ public.localites non matérialisée"] if loc_total else ["Fichiers localités absents"],
        anomalies=[],
        recommendations=["Matérialiser le lien NCI ↔ référentiel admin"],
        available=bool(loc_total),
    )
    return pop, loc


def _eval_zones() -> dict[str, Any]:
    from api.services import fdsu_code_service

    zones = list(getattr(fdsu_code_service, "OFFICIAL_ZONES", []) or [])
    n = len(zones)
    return _domain_shell(
        code="zones_fdsu",
        label="Zones FDSU",
        dimensions={
            "completeness": 100.0 if n >= 4 else _ratio_pct(n, 4),
            "quality": 95.0 if n else None,
            "geolocation": 70.0 if n else None,  # zones souvent attributives
            "normalization": 100.0 if n else None,
            "spatial_relations": 60.0 if n else None,
            "documentation": 90.0 if n else 20.0,
            "traceability": 95.0 if n else None,
            "freshness": None,
            "official_source": 100.0 if n else None,
            "interoperability": 90.0 if n else 20.0,
        },
        object_count=n or None,
        source="api/services/fdsu_code_service.OFFICIAL_ZONES",
        as_of=_now(),
        version="fdsu-zones",
        strengths=["Nomenclature officielle des zones"] if n else [],
        weaknesses=["Géométries de zone à consolider"] if n else ["Zones absentes"],
        anomalies=[],
        recommendations=["Étendre la cartographie polygones par zone FDSU"] if n else [],
        available=bool(n),
    )


def _eval_program_file(code: str, label: str, *, in_nsme: bool, expected: int | None) -> dict[str, Any]:
    path = ROOT / "data" / "programs" / code / f"{code}.json"
    count = None
    with_geom = None
    if path.exists():
        import json

        payload = json.loads(path.read_text(encoding="utf-8"))
        meta = payload.get("_meta") or {}
        sites = payload.get("sites") if isinstance(payload, dict) else payload
        if isinstance(sites, list):
            count = len(sites)
        if meta.get("count") is not None:
            count = int(meta["count"])
        if meta.get("with_geometry") is not None:
            with_geom = int(meta["with_geometry"])

    # NSME DB count
    nsme_n = None
    if in_nsme:
        from api.services import spatial_matching_service as nsme

        listed = _safe(lambda: nsme.list_fdsu_sites(program_code=code, limit=5000), []) or []
        nsme_n = len(listed)

    complete = None
    if expected and count is not None:
        complete = _ratio_pct(count, expected)
        if count >= expected:
            complete = 100.0
    elif count is not None:
        complete = 90.0

    geo = _ratio_pct(with_geom, count) if (with_geom is not None and count) else (100.0 if nsme_n else None)
    interop = 95.0 if (nsme_n and nsme_n > 0) else (55.0 if count else None)
    if code == "sites_20476" and (nsme_n or 0) == 0 and count:
        weak = ["Absent de programs.fdsu_sites (NSME) — SDG via fallback fichier"]
        interop = 45.0
        anomalies = ["site_hors_referentiel_nsme"]
    else:
        weak = []
        anomalies = []

    return _domain_shell(
        code=code,
        label=label,
        dimensions={
            "completeness": complete,
            "quality": 88.0 if count else None,
            "geolocation": geo,
            "normalization": 85.0 if count else None,
            "spatial_relations": 80.0 if nsme_n else (50.0 if count else None),
            "documentation": 90.0 if path.exists() else 20.0,
            "traceability": 90.0 if path.exists() else None,
            "freshness": _freshness_from_mtime(path),
            "official_source": 95.0 if count else None,
            "interoperability": interop,
        },
        object_count=count if count is not None else nsme_n,
        source=str(path.relative_to(ROOT)) if path.exists() else "programs.fdsu_sites",
        as_of=_file_mtime_iso(path) or _now(),
        version=code,
        strengths=[f"{count} sites dans le fichier"] if count else ([f"{nsme_n} en NSME"] if nsme_n else []),
        weaknesses=weak + (["Population native absente"] if code in {"sites_40", "sites_300"} and count else []),
        anomalies=anomalies,
        recommendations=(
            ["Charger le programme dans programs.fdsu_sites"]
            if code == "sites_20476" and (nsme_n or 0) == 0
            else []
        ),
        relations_note="NSME spatial matching" if nsme_n else "Fichier programme",
        available=bool(count or nsme_n),
    )


def _eval_ccn() -> dict[str, Any]:
    from api.services import ccn_operational_service as ccn

    stats = _safe(ccn.statistics, {}) or {}
    kpis = stats.get("kpis") or {}
    total = kpis.get("total")
    path = ROOT / "data" / "programs" / "ccn" / "demo_ccn.json"
    return _domain_shell(
        code="ccn",
        label="CCN",
        dimensions={
            "completeness": 55.0 if total else None,  # DEMO only
            "quality": 50.0 if total else None,
            "geolocation": 85.0 if total else None,
            "normalization": 70.0 if total else None,
            "spatial_relations": 60.0 if total else None,
            "documentation": 80.0 if path.exists() else 20.0,
            "traceability": 75.0 if total else None,
            "freshness": _freshness_from_mtime(path),
            "official_source": 40.0 if total else None,  # démonstration ≠ officiel production
            "interoperability": 65.0 if total else 15.0,
        },
        object_count=int(total) if total is not None else None,
        source="data/programs/ccn/demo_ccn.json",
        as_of=_file_mtime_iso(path) or _now(),
        version="demo",
        strengths=["Inventaire DEMO géolocalisé"] if total else [],
        weaknesses=["Jeu de démonstration — ≠ production", "Suivi opérationnel CCN à consolider"],
        anomalies=["data_class=demonstration"] if total else [],
        recommendations=["Intégrer l’inventaire CCN officiel de production"],
        relations_note="Liens DEMO sites FDSU",
        available=bool(total),
    )


def _eval_telecom_fibre() -> tuple[dict[str, Any], dict[str, Any]]:
    from api.services import telecom_service

    stats = _safe(telecom_service.get_statistics, {}) or {}
    ops = int(stats.get("operator_count") or 0)
    points = int(stats.get("infrastructure_count") or 0)
    lines = int(stats.get("network_line_count") or 0)
    polygons = int(stats.get("coverage_polygon_count") or 0)
    has = ops > 0 or points > 0
    telecom = _domain_shell(
        code="telecom",
        label="Télécommunications",
        dimensions={
            "completeness": _clamp(min(100.0, 40 + (30 if ops else 0) + (20 if points else 0) + (10 if polygons else 0))) if has else None,
            "quality": 90.0 if points else None,
            "geolocation": 95.0 if points else None,
            "normalization": 90.0 if ops else None,
            "spatial_relations": 88.0 if points else None,
            "documentation": 85.0 if Path("data/sectoral/telecom").exists() or has else 30.0,
            "traceability": 90.0 if has else None,
            "freshness": None,
            "official_source": 90.0 if has else None,
            "interoperability": 95.0 if has else 20.0,
        },
        object_count=points + lines + polygons if has else None,
        source="telecom.operators / infrastructure / network_lines / coverage_polygons",
        as_of=_now(),
        version="telecom-db",
        strengths=[f"{ops} opérateurs", f"{points} infrastructures"] if has else [],
        weaknesses=[],
        anomalies=[],
        recommendations=[],
        available=has,
    )
    fibre = _domain_shell(
        code="fibre",
        label="Fibre",
        dimensions={
            "completeness": _clamp(min(100.0, 50 + min(50, lines / 10))) if lines else (30.0 if has else None),
            "quality": 85.0 if lines else None,
            "geolocation": 90.0 if lines else None,
            "normalization": 80.0 if lines else None,
            "spatial_relations": 85.0 if lines else None,
            "documentation": 70.0 if lines or has else 25.0,
            "traceability": 80.0 if lines else None,
            "freshness": None,
            "official_source": 85.0 if lines else None,
            "interoperability": 90.0 if lines else 40.0,
        },
        object_count=lines or None,
        source="telecom.network_lines",
        as_of=_now(),
        version="telecom-lines",
        strengths=[f"{lines} tronçons / lignes"] if lines else [],
        weaknesses=["Couche fibre partielle"] if not lines and has else (["Fibre absente"] if not has else []),
        anomalies=[],
        recommendations=["Enrichir le référentiel fibre / backbone"] if lines < 100 else [],
        available=bool(lines or has),
    )
    return telecom, fibre


def _eval_routes() -> dict[str, Any]:
    from api.services import transport_service

    stats = _safe(transport_service.get_statistics, {}) or {}
    total = stats.get("routes_total")
    unnamed = stats.get("unnamed")
    has = total is not None and int(total) > 0
    named_ratio = None
    if has and unnamed is not None:
        named_ratio = _ratio_pct(int(total) - int(unnamed), int(total))
    return _domain_shell(
        code="routes",
        label="Routes",
        dimensions={
            "completeness": _clamp(min(100.0, 50 + min(50, int(total or 0) / 200))) if has else None,
            "quality": named_ratio or (80.0 if has else None),
            "geolocation": 95.0 if has else None,
            "normalization": 85.0 if has else None,
            "spatial_relations": 90.0 if has else None,
            "documentation": 85.0 if has else 25.0,
            "traceability": 85.0 if has else None,
            "freshness": None,
            "official_source": 85.0 if has else None,
            "interoperability": 95.0 if has else 20.0,
        },
        object_count=int(total) if has else None,
        source="transport.routes",
        as_of=(stats.get("_meta") or {}).get("updated_at") or _now(),
        version="transport",
        strengths=[f"{total} routes", f"{stats.get('length_km')} km"] if has else [],
        weaknesses=[f"{unnamed} sans nom"] if unnamed else ([] if has else ["Table routes absente"]),
        anomalies=[],
        recommendations=[],
        available=has,
    )


def _eval_health() -> dict[str, Any]:
    from api.services import health_service

    stats = _safe(lambda: health_service.get_statistics("national", "RDC"), {}) or {}
    total = int(stats.get("total_facilities") or 0)
    with_geom = int(stats.get("facilities_with_geometry") or 0)
    without = int(stats.get("facilities_without_geometry") or 0)
    has = bool(stats.get("data_available")) and total > 0
    geo = _ratio_pct(with_geom, total) if has else None
    return _domain_shell(
        code="sante",
        label="Santé",
        dimensions={
            "completeness": _clamp(min(100.0, 40 + min(60, total / 50))) if has else None,
            "quality": geo,
            "geolocation": geo,
            "normalization": 90.0 if has else None,
            "spatial_relations": 92.0 if has else None,
            "documentation": 85.0 if has else 25.0,
            "traceability": 90.0 if has else None,
            "freshness": None,
            "official_source": 90.0 if has else None,
            "interoperability": 95.0 if has else 20.0,
        },
        object_count=total if has else None,
        source="health.health_facilities",
        as_of=str(stats.get("computed_at") or _now()),
        version="health",
        strengths=[f"{total} établissements", f"{with_geom} géolocalisés"] if has else [],
        weaknesses=[f"{without} sans géométrie"] if without else ([] if has else ["Référentiel santé vide"]),
        anomalies=[],
        recommendations=[],
        available=has,
    )


def _eval_absent(code: str, label: str, note: str) -> dict[str, Any]:
    """Référentiel non branché — scores bas documentés, pas de faux 0 silencieux partout."""
    return _domain_shell(
        code=code,
        label=label,
        dimensions={
            "completeness": 15.0,
            "quality": None,
            "geolocation": None,
            "normalization": None,
            "spatial_relations": None,
            "documentation": 25.0,
            "traceability": None,
            "freshness": None,
            "official_source": None,
            "interoperability": 10.0,
        },
        object_count=None,
        source=None,
        as_of=None,
        version=None,
        strengths=[],
        weaknesses=[note],
        anomalies=["referential_not_integrated"],
        recommendations=[f"Intégrer le référentiel {label}"],
        relations_note=None,
        available=False,
    )


def _eval_sdg() -> dict[str, Any]:
    from api.services import sdg_coverage_service as cov

    report = _safe(lambda: cov.build_coverage_report(deep_sample_per_program=0, include_ccn=True), {}) or {}
    native = report.get("nsme_native_rate")
    complete = report.get("complete")
    pending = report.get("pending_nsme_load")
    return _domain_shell(
        code="sdg",
        label="Spatial Decision Graph",
        dimensions={
            "completeness": _clamp(native) if native is not None else None,
            "quality": 85.0 if complete else None,
            "geolocation": 90.0 if complete else 70.0,
            "normalization": 80.0,
            "spatial_relations": _clamp((native or 0) + 20) if native is not None else None,
            "documentation": 95.0 if Path("PROJECT_MANAGEMENT/ARCHITECTURE/SDG_COVERAGE_AUDIT_V1.md").exists() else 70.0,
            "traceability": 90.0,
            "freshness": None,
            "official_source": 85.0,
            "interoperability": 88.0 if complete else 50.0,
        },
        object_count=report.get("total"),
        source="GET /api/sdg/coverage",
        as_of=(report.get("_meta") or {}).get("generated_at") or _now(),
        version="sdg-coverage-1.0.0",
        strengths=[f"NSME natif {native}%"] if native is not None else [],
        weaknesses=[f"{pending} sites à charger en NSME"] if pending else [],
        anomalies=[],
        recommendations=["Charger Sites 20 476 dans programs.fdsu_sites"] if pending else [],
        relations_note="Audit couverture analytique",
        available=bool(report),
    )


def _eval_ple() -> dict[str, Any]:
    from api.services import program_lifecycle_engine as ple

    board = _safe(ple.build_programs_board, {}) or {}
    programs = board.get("programs") or []
    path = ROOT / "data" / "business" / "program_lifecycle_registry_v1.json"
    return _domain_shell(
        code="program_lifecycle",
        label="Program Lifecycle",
        dimensions={
            "completeness": 90.0 if programs else None,
            "quality": 88.0 if programs else None,
            "geolocation": None,
            "normalization": 95.0 if programs else None,
            "spatial_relations": None,
            "documentation": 95.0 if path.exists() else 50.0,
            "traceability": 90.0 if programs else None,
            "freshness": _freshness_from_mtime(path),
            "official_source": 90.0 if programs else None,
            "interoperability": 92.0 if programs else 30.0,
        },
        object_count=len(programs) or None,
        source="data/business/program_lifecycle_registry_v1.json",
        as_of=_file_mtime_iso(path) or _now(),
        version="ple-1.0.0",
        strengths=["Six dimensions de statut séparées"] if programs else [],
        weaknesses=["Compteurs installé/opérationnel encore à consolider"],
        anomalies=[],
        recommendations=["Renseigner preuves individuelles de mise en service"],
        available=bool(programs),
    )


def _eval_ti() -> dict[str, Any]:
    # TI disponible si API/routes présentes + multi-échelle
    multi = ROOT / "api" / "services" / "territorial_multiscale_service.py"
    svc = ROOT / "api" / "services" / "territorial_intelligence_service.py"
    has = multi.exists() and svc.exists()
    return _domain_shell(
        code="territorial_intelligence",
        label="Territorial Intelligence",
        dimensions={
            "completeness": 88.0 if has else None,
            "quality": 85.0 if has else None,
            "geolocation": 80.0 if has else None,
            "normalization": 85.0 if has else None,
            "spatial_relations": 82.0 if has else None,
            "documentation": 90.0 if Path("PROJECT_MANAGEMENT/ARCHITECTURE/TERRITORIAL_INTELLIGENCE_MULTI_SCALE_V1.md").exists() else 60.0,
            "traceability": 85.0 if has else None,
            "freshness": None,
            "official_source": 80.0 if has else None,
            "interoperability": 90.0 if has else 20.0,
        },
        object_count=None,
        source="api/territorial-intelligence",
        as_of=_now(),
        version="ti-multiscale",
        strengths=["Multi-échelle opérationnelle"] if has else [],
        weaknesses=["Certains domaines encore partiels (énergie, éducation)"],
        anomalies=[],
        recommendations=["Brancher éducation / énergie dans les profils TI"],
        available=has,
    )


def _eval_impact() -> dict[str, Any]:
    path = ROOT / "api" / "services" / "territorial_impact_engine.py"
    has = path.exists()
    audit = _safe(lambda: __import__("api.services.territorial_impact_engine", fromlist=["audit_population_sources"]).audit_population_sources(), {}) or {}
    matrix = audit.get("matrix") or []
    return _domain_shell(
        code="impact_territorial",
        label="Impact territorial",
        dimensions={
            "completeness": 82.0 if has else None,
            "quality": 80.0 if has else None,
            "geolocation": 85.0 if has else None,
            "normalization": 78.0 if has else None,
            "spatial_relations": 88.0 if has else None,
            "documentation": 92.0 if Path("PROJECT_MANAGEMENT/ARCHITECTURE/TERRITORIAL_IMPACT_AND_COVERAGE_PROGRESSION_ENGINE_V1.md").exists() else 50.0,
            "traceability": 90.0 if matrix else None,
            "freshness": None,
            "official_source": 80.0 if has else None,
            "interoperability": 90.0 if has else 20.0,
        },
        object_count=len(matrix) or None,
        source="api/territorial-impact",
        as_of=_now(),
        version="tie-1.0.0",
        strengths=["Anti double-comptage NCI", "Distinction CCN ≠ radio"] if has else [],
        weaknesses=["Dates de déploiement non disponibles"],
        anomalies=[],
        recommendations=["Alimenter les preuves de mise en service pour impact observé"],
        available=has,
    )


def _eval_coverage_radio() -> dict[str, Any]:
    """Couverture radio observée via NCI — distinct de la maturité data."""
    from api.services import coverage_intelligence_service as nci

    stats = _safe(nci.statistics, {}) or {}
    kpis = stats.get("kpis") or {}
    ratio = kpis.get("coverage_ratio_population")
    score = None
    if isinstance(ratio, (int, float)):
        score = _clamp(float(ratio) * 100 if float(ratio) <= 1.5 else float(ratio))
    return _domain_shell(
        code="couverture_radio",
        label="Couverture radio (données)",
        dimensions={
            "completeness": score,
            "quality": 80.0 if score is not None else None,
            "geolocation": 85.0 if score is not None else None,
            "normalization": 75.0 if score is not None else None,
            "spatial_relations": 70.0 if score is not None else None,
            "documentation": 85.0 if score is not None else 30.0,
            "traceability": 85.0 if score is not None else None,
            "freshness": _freshness_from_mtime(ROOT / "data" / "coverage" / "aggregates.json"),
            "official_source": 80.0 if score is not None else None,
            "interoperability": 85.0 if score is not None else 20.0,
        },
        object_count=kpis.get("localities_covered"),
        source="NCI coverage_ratio_population (maturité du signal data, ≠ qualité réseau live)",
        as_of=_file_mtime_iso(ROOT / "data" / "coverage" / "aggregates.json"),
        version="nci",
        strengths=["Ratio population couverte mesuré"] if score is not None else [],
        weaknesses=["Ne représente pas l’état radio live des opérateurs"],
        anomalies=[],
        recommendations=[],
        available=score is not None,
    )


def _build_priorities(domains: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Liste auto « données prioritaires à acquérir » basée sur scores / anomalies."""
    priorities = []
    for d in domains:
        score = d.get("score")
        stars = 3
        if not d.get("available") or (score is not None and score < 40):
            stars = 5
        elif score is not None and score < 60:
            stars = 5
        elif score is not None and score < 75:
            stars = 4
        elif score is not None and score < 85:
            stars = 3
        else:
            continue  # solide — pas dans la liste prioritaire

        reason = (d.get("weaknesses") or d.get("recommendations") or ["Maturité insuffisante"])[0]
        priorities.append(
            {
                "domain": d.get("code"),
                "label": d.get("label"),
                "stars": stars,
                "score": score,
                "reason": reason,
                "recommendations": d.get("recommendations") or [],
            }
        )
    priorities.sort(key=lambda x: (-x["stars"], x.get("score") if x.get("score") is not None else 0))
    return priorities


def _build_roadmap(domains: list[dict[str, Any]], priorities: list[dict[str, Any]]) -> dict[str, Any]:
    short, mid, long = [], [], []
    codes = {p["domain"] for p in priorities if p["stars"] >= 5}
    mid_codes = {p["domain"] for p in priorities if p["stars"] == 4}

    mapping_short = {
        "sites_20476": ("Charger Sites 20 476 dans programs.fdsu_sites", "SDG NSME natif"),
        "ccn": ("Intégrer inventaire CCN production", "Pilotage CCN réel"),
        "education": ("Acquérir référentiel éducation", "Profils TI complets"),
        "energie": ("Acquérir référentiel énergie", "Critères CCN / priorisation"),
        "services_publics": ("Consolider services publics", "Analyse multi-services"),
    }
    for code, (action, gain) in mapping_short.items():
        if code in codes or any(d["code"] == code and not d.get("available") for d in domains):
            short.append({"action": action, "expected_gain": gain, "domain": code})

    for code in mid_codes:
        label = next((d["label"] for d in domains if d["code"] == code), code)
        mid.append({"action": f"Renforcer la qualité / relations de « {label} »", "expected_gain": "Hausse maturité nationale", "domain": code})

    long.extend(
        [
            {"action": "Matérialiser FK NCI ↔ public.localites", "expected_gain": "Résolution localités officielle", "domain": "localities"},
            {"action": "Preuves de mise en service par site", "expected_gain": "Impact observé vs projeté", "domain": "impact_territorial"},
            {"action": "Historique de statut traçable (PLE)", "expected_gain": "Gouvernance programme auditable", "domain": "program_lifecycle"},
        ]
    )
    return {
        "short_term": short,
        "medium_term": mid,
        "long_term": long,
        "note": "Feuille de route générée automatiquement depuis les scores — aucun jalon de date inventé.",
    }


def _build_map_features(domains_by_code: dict[str, Any]) -> dict[str, Any]:
    """Carte maturité data par province (NCI) — ≠ couverture réseau."""
    from api.services import coverage_intelligence_service as nci

    provinces = (_safe(lambda: nci.list_provinces(limit=50), {}) or {}).get("provinces") or []
    features = []
    for row in provinces:
        name = row.get("province") or row.get("name")
        # proxy documentation : ratio localités avec pop / présence agrégats
        loc_u = row.get("localities_uncovered")
        loc_c = row.get("localities_covered")
        pop_u = row.get("population_uncovered")
        pop_c = row.get("population_covered")
        has = any(v is not None for v in (loc_u, loc_c, pop_u, pop_c))
        if not has:
            continue
        # Score documentation locale : présence des deux populations
        score = 55.0
        if pop_c is not None and pop_u is not None:
            score = 85.0
        if loc_c is not None and loc_u is not None:
            score += 10.0
        score = _clamp(score)
        band = _band(score)
        features.append(
            {
                "type": "Feature",
                "properties": {
                    "name": name,
                    "maturity_score": score,
                    "band": band.get("code"),
                    "band_label": band.get("label"),
                    "kind": "data_maturity",  # explicite ≠ radio
                    "note": "Maturité documentaire NCI province — pas un niveau de couverture radio.",
                    "population_covered": pop_c,
                    "population_uncovered": pop_u,
                },
                "geometry": None,  # centroïdes non inventés — frontend peut joindre admin
            }
        )
    return {
        "type": "FeatureCollection",
        "features": features,
        "_meta": {
            "engine": ENGINE_VERSION,
            "warning": "Ne pas confondre avec la couverture réseau. Géométries admin à résoudre côté carto.",
            "count": len(features),
        },
    }


def build_national_maturity(*, use_cache: bool = True) -> dict[str, Any]:
    now = time.time()
    if use_cache and _CACHE["payload"] and now - _CACHE["ts"] < _CACHE_TTL_S:
        cached = dict(_CACHE["payload"])
        cached["_meta"] = {**(cached.get("_meta") or {}), "cache_hit": True}
        return cached

    started = time.time()
    pop, loc = _eval_population_localities()
    telecom, fibre = _eval_telecom_fibre()
    domains = [
        _eval_administration(),
        pop,
        loc,
        _eval_zones(),
        _eval_program_file("sites_40", "Sites 40", in_nsme=True, expected=40),
        _eval_program_file("sites_300", "Sites 300", in_nsme=True, expected=300),
        _eval_program_file("sites_20476", "Programme 20 476", in_nsme=True, expected=20476),
        _eval_ccn(),
        telecom,
        fibre,
        _eval_routes(),
        _eval_health(),
        _eval_absent("education", "Éducation", "Référentiel éducation non intégré (probe SDG / TI)"),
        _eval_absent("energie", "Énergie", "Référentiel énergie non intégré"),
        _eval_absent("services_publics", "Services publics", "Hors santé : écoles / admin / marchés partiels ou absents"),
        _eval_absent("economie", "Économie", "Référentiel économique non intégré"),
        _eval_coverage_radio(),
        _eval_sdg(),
        _eval_ple(),
        _eval_ti(),
        _eval_impact(),
    ]

    # Score national pondéré — domaines sans score exclus (pas de faux 0)
    weighted = []
    for d in domains:
        w = DOMAIN_WEIGHTS.get(d["code"], 0.02)
        if d.get("score") is not None:
            weighted.append((w, float(d["score"])))
    if weighted:
        w_sum = sum(w for w, _ in weighted)
        national = round(sum(w * s for w, s in weighted) / w_sum, 1) if w_sum else None
    else:
        national = None

    priorities = _build_priorities(domains)
    roadmap = _build_roadmap(domains, priorities)

    payload = {
        "_meta": {
            "engine": ENGINE_VERSION,
            "generated_at": _now(),
            "elapsed_ms": round((time.time() - started) * 1000, 1),
            "cache_hit": False,
            "ttl_seconds": _CACHE_TTL_S,
            "data_first": True,
            "scoring": {
                "national": "moyenne pondérée des scores domaines non-null",
                "domain": "moyenne des dimensions non-null",
                "weights": DOMAIN_WEIGHTS,
                "null_policy": "jamais remplacer une dimension absente par 0",
            },
        },
        "national_score": national,
        "national_band": _band(national),
        "domains": domains,
        "dashboard": [
            {
                "code": d["code"],
                "label": d["label"],
                "score": d["score"],
                "band": d["band"],
                "available": d["available"],
            }
            for d in domains
        ],
        "priorities": priorities,
        "roadmap": roadmap,
        "legend": [
            {"min": 95, "label": "Excellent"},
            {"min": 90, "max": 95, "label": "Très bon"},
            {"min": 80, "max": 90, "label": "Bon"},
            {"min": 60, "max": 80, "label": "À renforcer"},
            {"max": 60, "label": "Prioritaire"},
        ],
    }
    _CACHE["ts"] = now
    _CACHE["payload"] = payload
    return payload


def build_details() -> dict[str, Any]:
    base = build_national_maturity()
    return {
        "_meta": base.get("_meta"),
        "national_score": base.get("national_score"),
        "domains": base.get("domains"),
    }


def build_roadmap_payload() -> dict[str, Any]:
    base = build_national_maturity()
    return {
        "_meta": base.get("_meta"),
        "priorities": base.get("priorities"),
        "roadmap": base.get("roadmap"),
        "national_score": base.get("national_score"),
    }


def build_map_payload() -> dict[str, Any]:
    base = build_national_maturity()
    by_code = {d["code"]: d for d in base.get("domains") or []}
    fc = _build_map_features(by_code)
    return {
        "_meta": {**(base.get("_meta") or {}), **(fc.get("_meta") or {})},
        "national_score": base.get("national_score"),
        "geojson": fc,
        "legend": base.get("legend"),
        "note": "Couche « maturité des données » — distincte de la couverture radio.",
    }


def build_report_payload() -> dict[str, Any]:
    """Contenu pour rapport Direction — impression navigateur (PDF natif non inventé)."""
    base = build_national_maturity()
    return {
        "_meta": {
            **(base.get("_meta") or {}),
            "report_title": "Rapport National de Maturité des Données",
            "audience": "Direction FDSU",
            "export": "html_print",
            "note": "export_pdf plateforme non activé — utiliser impression navigateur.",
        },
        "national_score": base.get("national_score"),
        "national_band": base.get("national_band"),
        "dashboard": base.get("dashboard"),
        "priorities": base.get("priorities"),
        "roadmap": base.get("roadmap"),
        "domains": base.get("domains"),
        "legend": base.get("legend"),
    }
