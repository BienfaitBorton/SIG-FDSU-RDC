"""SharedSpatialContext — résolution spatiale froide réutilisable.

Une seule résolution (site coords + version légère) alimente :
- Dossier de Décision (preuves telecom / éducation / CENI)
- NSME / impact / needs (via caches site_spatial_context_cache)
- SDG / DXL (consommateurs du même cache)

Clé typique : site_id | kind | lat/lon arrondis | radius | DATA_MODE
Invalidation : TTL (défaut 120 s) ou clear().
Désactivable : SIG_SHARED_SPATIAL=0
"""

from __future__ import annotations

import os
import threading
import time
from typing import Any, Callable, TypeVar

T = TypeVar("T")

_LOCK = threading.RLock()
_STORE: dict[str, tuple[float, Any]] = {}
_STATS = {"HIT": 0, "MISS": 0, "SET": 0, "EXPIRED": 0, "TELECOM_BUILDS": 0}

_TTL_S = float(os.environ.get("SIG_SHARED_SPATIAL_TTL_S", "120") or 120)
_ENABLED = os.environ.get("SIG_SHARED_SPATIAL", "1").strip().lower() not in {"0", "false", "no", "off"}

# One-shot FDSU MNO staging readiness (process-local)
_FDSU_READY = False
_FDSU_META: dict[str, Any] = {}
_FDSU_LOCK = threading.Lock()


def cache_enabled() -> bool:
    return _ENABLED


def set_cache_enabled(enabled: bool) -> None:
    global _ENABLED
    _ENABLED = bool(enabled)


def clear() -> None:
    with _LOCK:
        _STORE.clear()


def reset_stats() -> None:
    with _LOCK:
        for k in list(_STATS):
            _STATS[k] = 0


def stats() -> dict[str, Any]:
    with _LOCK:
        return {**_STATS, "fdsu_ready": _FDSU_READY, "fdsu_meta": dict(_FDSU_META)}


def reset_fdsu_ready_flag() -> None:
    """Tests only — force re-check of staging table."""
    global _FDSU_READY, _FDSU_META
    with _FDSU_LOCK:
        _FDSU_READY = False
        _FDSU_META = {}


def _round_coord(v: float) -> str:
    return f"{float(v):.5f}"


def make_geo_key(kind: str, lat: float, lon: float, *, radius_m: float = 25000) -> str:
    from api.config import DATA_MODE

    return "|".join(
        [
            "shared_spatial_v1",
            str(kind),
            _round_coord(lat),
            _round_coord(lon),
            str(int(radius_m)),
            str(DATA_MODE or "json"),
        ]
    )


def get_or_build(key: str, builder: Callable[[], T], *, ttl_s: float | None = None) -> T:
    if not _ENABLED:
        return builder()
    now = time.time()
    with _LOCK:
        item = _STORE.get(key)
        if item:
            expires_at, value = item
            if expires_at >= now:
                _STATS["HIT"] += 1
                return value  # type: ignore[return-value]
            _STORE.pop(key, None)
            _STATS["EXPIRED"] += 1
        _STATS["MISS"] += 1
    value = builder()
    if value is not None:
        ttl = _TTL_S if ttl_s is None else float(ttl_s)
        with _LOCK:
            _STORE[key] = (time.time() + ttl, value)
            _STATS["SET"] += 1
    return value


def ensure_fdsu_mno_staging_ready(*, sync_if_empty: bool = True) -> dict[str, Any]:
    """Garantit que telecom.fdsu_mno_sites est utilisable sans fallback audit à chaque appel.

    Si la table est vide et sync_if_empty=True, synchronise une fois depuis l'audit MNO.
    Coût froid unique amorti ensuite par PostGIS indexé.
    """
    global _FDSU_READY, _FDSU_META
    if _FDSU_READY:
        return {"ready": True, "cached": True, **_FDSU_META}

    with _FDSU_LOCK:
        if _FDSU_READY:
            return {"ready": True, "cached": True, **_FDSU_META}

        from api.services import telecom_service as ts

        t0 = time.perf_counter()
        ts.ensure_fdsu_staging_table()
        n = 0
        try:
            from api.config import connect_db

            with connect_db() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT COUNT(*) FROM telecom.fdsu_mno_sites")
                    n = int(cur.fetchone()[0] or 0)
        except Exception as exc:  # noqa: BLE001
            _FDSU_META = {"ready": False, "error": str(exc), "ensure_ms": round((time.perf_counter() - t0) * 1000, 1)}
            return dict(_FDSU_META)

        sync_result = None
        if n <= 0 and sync_if_empty:
            sync_result = ts.sync_fdsu_mno_staging_from_audit()
            n = int((sync_result or {}).get("synced") or 0)

        _FDSU_READY = True
        _FDSU_META = {
            "ready": True,
            "rows": n,
            "synced_now": bool(sync_result),
            "sync": sync_result,
            "elapsed_ms": round((time.perf_counter() - t0) * 1000, 1),
        }
        return dict(_FDSU_META)


def get_telecom_spatial_context(lat: float, lon: float, *, radius_m: float = 25000) -> dict[str, Any]:
    """Contexte télécom spatial partagé (MNO + fibre + MW)."""
    key = make_geo_key("telecom", lat, lon, radius_m=radius_m)

    def _build() -> dict[str, Any]:
        with _LOCK:
            _STATS["TELECOM_BUILDS"] += 1
        ensure_fdsu_mno_staging_ready(sync_if_empty=True)
        from api.services import telecom_service as ts

        return ts.spatial_context_around(float(lat), float(lon), radius_m=radius_m) or {}

    return get_or_build(key, _build)


def get_education_nearest(lat: float, lon: float, *, radius_m: float = 25000, limit: int = 10) -> dict[str, Any]:
    key = make_geo_key(f"education:{limit}", lat, lon, radius_m=radius_m)

    def _build() -> dict[str, Any]:
        from api.services import education_referential_service as edu

        return edu.nearest_establishment(float(lat), float(lon), radius_m=radius_m, limit=limit) or {}

    return get_or_build(key, _build)


def get_ceni_nearest(
    lat: float,
    lon: float,
    *,
    radius_m: float = 15000,
    limit: int = 10,
    exclude_schools: bool = True,
) -> dict[str, Any]:
    key = make_geo_key(f"ceni:{limit}:{int(exclude_schools)}", lat, lon, radius_m=radius_m)

    def _build() -> dict[str, Any]:
        from api.services import ceni_registry_service as ceni

        return ceni.nearest_signals(
            float(lat), float(lon), radius_m=radius_m, limit=limit, exclude_schools=exclude_schools
        ) or {}

    return get_or_build(key, _build)
