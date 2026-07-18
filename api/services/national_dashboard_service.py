"""Agrégats compacts de synthèse nationale pour le premier écran."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from api.config import connect_db
from api.services import education_referential_service

ROOT = Path(__file__).resolve().parents[2]
BASELINE_PATH = ROOT / "data" / "business" / "administrative_baseline_unsd_ungegn_v1.json"
COUNTERS_PATH = ROOT / "data" / "reports" / "national_counter_registry.json"


@lru_cache(maxsize=1)
def baseline() -> dict[str, Any]: return json.loads(BASELINE_PATH.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def counter_registry() -> dict[str, Any]: return json.loads(COUNTERS_PATH.read_text(encoding="utf-8"))["registre_national_des_compteurs"]


def _coverage(integrated: int | None, reference: int | None) -> float | None:
    return round(integrated * 100 / reference, 2) if integrated is not None and reference else None


def _db_counts() -> dict[str, int]:
    queries = {
        "zones": "SELECT COUNT(*) FROM zones", "provinces": "SELECT COUNT(*) FROM provinces", "villes": "SELECT COUNT(*) FROM villes",
        "territoires": "SELECT COUNT(*) FROM territoires", "collectivites": "SELECT COUNT(*) FROM collectivites",
        "groupements": "SELECT COUNT(*) FROM groupements", "localites": "SELECT COUNT(*) FROM localites",
        "sites": "SELECT COUNT(*) FROM sites", "missions": "SELECT COUNT(*) FROM missions",
        "health_facilities": "SELECT COUNT(*) FROM health.health_facilities",
        "telecom_infrastructure": "SELECT COUNT(*) FROM telecom.infrastructure",
        "telecom_network_lines": "SELECT COUNT(*) FROM telecom.network_lines",
        "telecom_coverage_polygons": "SELECT COUNT(*) FROM telecom.coverage_polygons",
    }
    values: dict[str, int] = {}
    with connect_db() as conn:
        with conn.cursor() as cur:
            for key, query in queries.items():
                try:
                    cur.execute(query); values[key] = int(cur.fetchone()[0])
                except Exception:
                    conn.rollback(); values[key] = 0
    counters = counter_registry()
    values["secteurs"] = int((counters.get("secteurs") or {}).get("nombre") or 0)
    values["chefferies"] = int((counters.get("chefferies") or {}).get("nombre") or 0)
    return values


def _file_counts() -> dict[str, int]:
    counters = counter_registry()
    value = lambda key, field="nombre": int((counters.get(key) or {}).get(field) or 0)
    return {"zones": 5, "provinces": value("provinces"), "villes": value("villes"), "territoires": value("territoires"), "secteurs": value("secteurs"), "chefferies": value("chefferies"), "collectivites": value("collectivites"), "groupements": value("groupements", "trouve"), "localites": value("localites"), "sites": 0, "missions": 0, "health_facilities": 37562, "telecom_infrastructure": 14580, "telecom_network_lines": 11357, "telecom_coverage_polygons": 5464}


def build_summary(*, use_database: bool) -> dict[str, Any]:
    counts, levels = (_db_counts() if use_database else _file_counts()), baseline()["levels"]
    education = education_referential_service.statistics()
    administrative = []
    for level in ("provinces", "villes", "territoires", "secteurs", "chefferies", "groupements", "villages"):
        definition, integrated_key = levels[level], levels[level]["comparable_with"]
        integrated, reference = counts.get(integrated_key), int(definition["reference"])
        administrative.append({"level": level, "label": definition["label"], "integrated": integrated, "reference": reference, "coverage_percent": _coverage(integrated, reference), "comparison_note": definition.get("comparison_note")})
    telecom_total = counts["telecom_infrastructure"] + counts["telecom_network_lines"] + counts["telecom_coverage_polygons"]
    return {
        "zones": counts["zones"], "provinces": counts["provinces"], "territories": counts["territoires"], "villes": counts["villes"],
        "collectivites": counts["collectivites"], "groupements": counts["groupements"], "localites": counts["localites"],
        "sites": counts["sites"], "missions": counts["missions"], "users": 0,
        "national_kpis": {
            "fdsu_sites": {"value": 20476, "program_40": 40, "program_300": 300, "national_program": 20476, "counting_rule": "Le programme national inclut la vague 300; les programmes ne sont pas additionnés.", "source": "data/programs/sites_20476/sites_20476.json"},
            "ceni_sites": {"value": 31956, "source_available": 32221, "integrated": 31956, "quarantined_coordinates": 265, "rejected_other": 0, "classified": 25262, "unclassified": 6959, "to_review": 19, "source": "Référentiel National CENI v1.0"},
            "education_establishments": {"value": education["establishments"], "source": "Sites CENI classifiés", "official_ministry_registry": False},
            "health_facilities": {"value": counts["health_facilities"], "source": "health.health_facilities"},
            "telecom_infrastructure": {"value": counts["telecom_infrastructure"], "definition": "Infrastructures ponctuelles intégrées", "geospatial_elements_total": telecom_total, "points": counts["telecom_infrastructure"], "lines": counts["telecom_network_lines"], "polygons": counts["telecom_coverage_polygons"], "source": "Schéma PostgreSQL telecom"}
        },
        "administrative_coverage": administrative,
        "administrative_baseline": {"registry_id": baseline()["_meta"]["registry_id"], "source": baseline()["provenance"], "non_comparable": baseline()["non_comparable"]},
        "_meta": {"payload_type": "aggregates_only", "massive_datasets_loaded_by_client": False}
    }
