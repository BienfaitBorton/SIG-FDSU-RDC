"""Cache runtime partagé + instrumentation des lectures JSON lourdes.

Objectifs startup :
- éviter les relectures disque / reparses JSON pour localités, groupements, liens RGC ;
- instrumenter READ/PARSE/BYTES/MS (activable via SIG_STARTUP_TRACE=1) ;
- invalidation basée sur mtime des fichiers sources ;
- désactivable via SIG_REF_CACHE=0 (mesure baseline).

CENI reste géré par api.services.ceni_registry_service.registry (@lru_cache).
"""

from __future__ import annotations

import json
import logging
import os
import threading
import time
from pathlib import Path
from typing import Any, Callable, TypeVar

logger = logging.getLogger("sig.startup")

T = TypeVar("T")

_LOCK = threading.RLock()
_JSON_CACHE: dict[str, tuple[int, int, Any]] = {}  # path -> (mtime_ns, size, data)
_VALUE_CACHE: dict[str, tuple[tuple[Any, ...], Any]] = {}  # key -> (signature, value)

_STATS: dict[str, dict[str, Any]] = {}
_TRACE = os.environ.get("SIG_STARTUP_TRACE", "").strip().lower() in {"1", "true", "yes", "on"}
_CACHE_ENABLED = os.environ.get("SIG_REF_CACHE", "1").strip().lower() not in {"0", "false", "no", "off"}


def cache_enabled() -> bool:
    return _CACHE_ENABLED


def set_cache_enabled(enabled: bool) -> None:
    global _CACHE_ENABLED
    _CACHE_ENABLED = bool(enabled)


def set_trace(enabled: bool) -> None:
    global _TRACE
    _TRACE = bool(enabled)


def reset_stats() -> None:
    with _LOCK:
        _STATS.clear()


def clear_all_caches() -> None:
    with _LOCK:
        _JSON_CACHE.clear()
        _VALUE_CACHE.clear()


def invalidate_paths(*paths: Path | str) -> None:
    with _LOCK:
        for path in paths:
            key = str(Path(path).resolve()) if path else ""
            _JSON_CACHE.pop(key, None)
        # value caches depend on mtime signatures — clear all derived values
        _VALUE_CACHE.clear()


def _stat_bucket(label: str) -> dict[str, Any]:
    bucket = _STATS.get(label)
    if bucket is None:
        bucket = {
            "READ_COUNT": 0,
            "PARSE_COUNT": 0,
            "CACHE_HIT": 0,
            "BYTES_READ": 0,
            "TOTAL_READ_MS": 0.0,
            "TOTAL_PARSE_MS": 0.0,
        }
        _STATS[label] = bucket
    return bucket


def file_stats_snapshot() -> dict[str, Any]:
    with _LOCK:
        return {k: dict(v) for k, v in _STATS.items()}


def _label_for(path: Path) -> str:
    name = path.name
    return name


def load_json_file(path: Path, *, label: str | None = None) -> Any:
    """Charge un JSON avec cache mtime + stats optionnelles."""
    resolved = path.resolve()
    key = str(resolved)
    tag = label or _label_for(path)
    if not path.exists():
        raise FileNotFoundError(path)

    st = path.stat()
    mtime_ns = getattr(st, "st_mtime_ns", int(st.st_mtime * 1_000_000_000))
    size = int(st.st_size)

    with _LOCK:
        if _CACHE_ENABLED:
            cached = _JSON_CACHE.get(key)
            if cached and cached[0] == mtime_ns and cached[1] == size:
                bucket = _stat_bucket(tag)
                bucket["CACHE_HIT"] += 1
                if _TRACE:
                    logger.info("[CACHE HIT] %s", tag)
                return cached[2]

    t0 = time.perf_counter()
    raw = path.read_bytes()
    read_ms = (time.perf_counter() - t0) * 1000.0
    t1 = time.perf_counter()
    data = json.loads(raw.decode("utf-8"))
    parse_ms = (time.perf_counter() - t1) * 1000.0

    with _LOCK:
        bucket = _stat_bucket(tag)
        bucket["READ_COUNT"] += 1
        bucket["PARSE_COUNT"] += 1
        bucket["BYTES_READ"] += len(raw)
        bucket["TOTAL_READ_MS"] += read_ms
        bucket["TOTAL_PARSE_MS"] += parse_ms
        if _CACHE_ENABLED:
            _JSON_CACHE[key] = (mtime_ns, size, data)
        if _TRACE:
            logger.info(
                "[JSON] %s read=%.1fms parse=%.1fms bytes=%s hits=%s",
                tag,
                read_ms,
                parse_ms,
                len(raw),
                bucket["CACHE_HIT"],
            )
    return data


def file_signature(*paths: Path) -> tuple[Any, ...]:
    sig: list[Any] = []
    for path in paths:
        if path is None:
            sig.append(None)
            continue
        if not path.exists():
            sig.append(("missing", str(path)))
            continue
        st = path.stat()
        sig.append(
            (
                str(path.resolve()),
                getattr(st, "st_mtime_ns", int(st.st_mtime * 1_000_000_000)),
                int(st.st_size),
            )
        )
    return tuple(sig)


def get_or_build(cache_key: str, signature: tuple[Any, ...], builder: Callable[[], T]) -> T:
    """Cache de valeurs dérivées (fusions, counts) invalidé si signature change."""
    if not _CACHE_ENABLED:
        return builder()
    with _LOCK:
        hit = _VALUE_CACHE.get(cache_key)
        if hit and hit[0] == signature:
            return hit[1]
    value = builder()
    with _LOCK:
        _VALUE_CACHE[cache_key] = (signature, value)
    return value


def log_startup(message: str, *, ms: float | None = None) -> None:
    if ms is None:
        logger.info("[STARTUP] %s", message)
    else:
        logger.info("[STARTUP] %s: %.1f ms", message, ms)
