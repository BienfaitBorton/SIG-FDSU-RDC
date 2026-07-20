"""Cache partagé court-TTL pour le contexte décisionnel / spatial d'un site.

Évite les recalculs dupliqués entre :
- Dossier de Décision (explainable_decision_service)
- NSME (spatial_matching_service)
- SDG (spatial_decision_graph_service)
- Territorial Impact

Clé : site_id + program_code + kind + data_mode + version légère des règles NSME.
Invalidation : TTL (défaut 90 s) ou clear explicite.
Désactivable : SIG_SITE_CTX_CACHE=0
"""

from __future__ import annotations

import os
import threading
import time
from concurrent.futures import Future
from pathlib import Path
from typing import Any, Callable, TypeVar

T = TypeVar("T")

_LOCK = threading.RLock()
_STORE: dict[str, tuple[float, Any]] = {}
_INFLIGHT: dict[str, Future] = {}
_STATS: dict[str, int] = {"HIT": 0, "MISS": 0, "SET": 0, "EXPIRED": 0}

_TTL_S = float(os.environ.get("SIG_SITE_CTX_TTL_S", "90") or 90)
_ENABLED = os.environ.get("SIG_SITE_CTX_CACHE", "1").strip().lower() not in {"0", "false", "no", "off"}

ROOT = Path(__file__).resolve().parents[2]
RULES_PATH = ROOT / "data" / "business" / "spatial_matching_rules.json"


def cache_enabled() -> bool:
    return _ENABLED


def set_cache_enabled(enabled: bool) -> None:
    global _ENABLED
    _ENABLED = bool(enabled)


def reset_stats() -> None:
    with _LOCK:
        for k in list(_STATS):
            _STATS[k] = 0


def clear() -> None:
    with _LOCK:
        _STORE.clear()
        _INFLIGHT.clear()


def stats() -> dict[str, int]:
    with _LOCK:
        return dict(_STATS)


def _rules_ver() -> str:
    if not RULES_PATH.exists():
        return "missing"
    st = RULES_PATH.stat()
    return f"{int(st.st_mtime)}-{int(st.st_size)}"


def make_key(
    kind: str,
    site_id: str | int,
    *,
    program_code: str | None = None,
    asset_type: str | None = None,
    lat: float | None = None,
    lon: float | None = None,
) -> str:
    from api.config import DATA_MODE

    parts = [
        "site_ctx_v2",
        str(kind),
        str(site_id),
        str(program_code or ""),
        str(asset_type or "site"),
        str(DATA_MODE or "json"),
        _rules_ver(),
    ]
    if lat is not None and lon is not None:
        try:
            parts.append(f"{float(lat):.5f}:{float(lon):.5f}")
        except (TypeError, ValueError):
            parts.append("nocoord")
    return "|".join(parts)


def get(key: str) -> Any | None:
    if not _ENABLED:
        return None
    now = time.time()
    with _LOCK:
        item = _STORE.get(key)
        if not item:
            _STATS["MISS"] += 1
            return None
        expires_at, value = item
        if expires_at < now:
            _STORE.pop(key, None)
            _STATS["EXPIRED"] += 1
            _STATS["MISS"] += 1
            return None
        _STATS["HIT"] += 1
        return value


def set_value(key: str, value: Any, *, ttl_s: float | None = None) -> Any:
    if not _ENABLED:
        return value
    ttl = _TTL_S if ttl_s is None else float(ttl_s)
    with _LOCK:
        _STORE[key] = (time.time() + ttl, value)
        _STATS["SET"] += 1
    return value


def get_or_build(key: str, builder: Callable[[], T], *, ttl_s: float | None = None) -> T:
    """Retourne la valeur cache, sinon exécute builder() avec single-flight par clé.

    Plusieurs threads sur la même clé froide : un seul builder ; les autres
    attendent le Future. Le builder ne tourne jamais sous ``_LOCK``.
    """
    if not _ENABLED:
        return builder()

    cached = get(key)
    if cached is not None:
        return cached  # type: ignore[return-value]

    leader = False
    future: Future
    with _LOCK:
        # Relecture sous lock : un autre thread a pu remplir le store.
        item = _STORE.get(key)
        if item is not None:
            expires_at, value = item
            if expires_at >= time.time():
                _STATS["HIT"] += 1
                return value  # type: ignore[return-value]
            _STORE.pop(key, None)
            _STATS["EXPIRED"] += 1

        existing = _INFLIGHT.get(key)
        if existing is not None:
            future = existing
        else:
            future = Future()
            _INFLIGHT[key] = future
            leader = True

    if not leader:
        return future.result()  # type: ignore[return-value]

    try:
        value = builder()
        if value is not None:
            set_value(key, value, ttl_s=ttl_s)
        future.set_result(value)
        return value
    except BaseException as exc:
        future.set_exception(exc)
        raise
    finally:
        with _LOCK:
            if _INFLIGHT.get(key) is future:
                _INFLIGHT.pop(key, None)
