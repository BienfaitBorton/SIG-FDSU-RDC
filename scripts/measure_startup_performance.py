"""Benchmark démarrage / premières requêtes référentiels (mesure réelle, ms).

Usage:
  .\\.venv\\Scripts\\python.exe scripts/measure_startup_performance.py

Variables:
  SIG_REF_CACHE=0  → désactive le cache (baseline)
  SIG_STARTUP_TRACE=1 → logs lecture JSON
"""

from __future__ import annotations

import json
import os
import statistics
import sys
import time
import tracemalloc
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT = ROOT / "data" / "cache" / "startup_performance_benchmark_v1.json"


def _ms(t0: float) -> float:
    return round((time.perf_counter() - t0) * 1000.0, 1)


def run_once(label: str, *, cache_enabled: bool) -> dict:
    os.environ["SIG_REF_CACHE"] = "1" if cache_enabled else "0"
    os.environ["SIG_STARTUP_TRACE"] = "1"
    os.environ.setdefault("DATA_MODE", "json")

    # Fresh interpreter modules for fair runs — caller should use subprocess.
    from api.services import referential_runtime_cache as rrc

    rrc.set_cache_enabled(cache_enabled)
    rrc.clear_all_caches()
    rrc.reset_stats()
    rrc.set_trace(True)

    tracemalloc.start()
    t_all = time.perf_counter()

    t0 = time.perf_counter()
    import api.main as main_mod  # noqa: F401

    import_ms = _ms(t0)

    t0 = time.perf_counter()
    from api.services.nire import locality_controlled_integration as lci
    from api.services.nire import groupement_controlled_integration as gci

    loc_count = lci.national_locality_count(include_enrichment=True)
    first_loc_count_ms = _ms(t0)

    t0 = time.perf_counter()
    loc_count2 = lci.national_locality_count(include_enrichment=True)
    second_loc_count_ms = _ms(t0)

    t0 = time.perf_counter()
    grp = gci.national_groupement_counts(include_enrichment=True)
    first_grp_count_ms = _ms(t0)

    t0 = time.perf_counter()
    grp2 = gci.national_groupement_counts(include_enrichment=True)
    second_grp_count_ms = _ms(t0)

    t0 = time.perf_counter()
    from api.services import ceni_registry_service

    ceni = ceni_registry_service.registry()
    first_ceni_ms = _ms(t0)
    ceni_assets = len(ceni.get("assets") or [])

    t0 = time.perf_counter()
    ceni2 = ceni_registry_service.registry()
    second_ceni_ms = _ms(t0)

    t0 = time.perf_counter()
    from api.services import spatial_matching_service as sms

    rules = sms.get_rules()
    spatial_rules_ms = _ms(t0)
    _ = rules  # silence unused

    t0 = time.perf_counter()
    summary = main_mod.dashboard_summary()
    summary_ms = _ms(t0)

    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    stats = rrc.file_stats_snapshot()
    total_ms = _ms(t_all)

    return {
        "label": label,
        "cache_enabled": cache_enabled,
        "import_api_main_ms": import_ms,
        "STARTUP_READY_MS": import_ms,  # API import+routes utilisable (sans preload lourds)
        "first_localites_count_ms": first_loc_count_ms,
        "second_localites_count_ms": second_loc_count_ms,
        "first_groupements_count_ms": first_grp_count_ms,
        "second_groupements_count_ms": second_grp_count_ms,
        "first_ceni_ms": first_ceni_ms,
        "second_ceni_ms": second_ceni_ms,
        "spatial_matching_rules_ms": spatial_rules_ms,
        "dashboard_summary_ms": summary_ms,
        "TOTAL_PROBE_MS": total_ms,
        "locality_count": loc_count,
        "locality_count_warm": loc_count2,
        "groupement_counts": grp,
        "groupement_counts_warm": grp2,
        "ceni_assets": ceni_assets,
        "ceni_warm_same_object": ceni is ceni2,
        "memory_current_mb": round(current / (1024 * 1024), 1),
        "memory_peak_mb": round(peak / (1024 * 1024), 1),
        "file_stats": stats,
    }


def main() -> None:
    # This script expects to be invoked twice via subprocess for clean imports.
    mode = os.environ.get("SIG_BENCH_MODE", "after")
    cache = mode != "before"
    result = run_once(mode, cache_enabled=cache)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    OUT.parent.mkdir(parents=True, exist_ok=True)
    prev = {}
    if OUT.exists():
        try:
            prev = json.loads(OUT.read_text(encoding="utf-8"))
        except Exception:
            prev = {}
    prev[mode] = result
    prev["updated_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    OUT.write_text(json.dumps(prev, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
