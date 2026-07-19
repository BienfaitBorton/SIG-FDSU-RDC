"""Nearest-neighbor helpers — bounding-box prefilter + Haversine (pas O(n²) multi-sites)."""

from __future__ import annotations

import math
from typing import Any, Callable, Iterable


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * r * math.asin(min(1.0, math.sqrt(a)))


def nearest_points(
    lat: float,
    lon: float,
    points: Iterable[dict[str, Any]],
    *,
    radius_m: float,
    limit: int = 15,
    lat_key: str = "latitude",
    lon_key: str = "longitude",
) -> list[dict[str, Any]]:
    """Retourne les points les plus proches dans radius_m (bbox degrés puis Haversine)."""
    if radius_m <= 0 or limit <= 0:
        return []
    # ~111.32 km / degré latitude ; longitude compressée par cos(lat)
    dlat = radius_m / 111_320.0
    cos_lat = max(0.2, abs(math.cos(math.radians(lat))))
    dlon = radius_m / (111_320.0 * cos_lat)
    lat_min, lat_max = lat - dlat, lat + dlat
    lon_min, lon_max = lon - dlon, lon + dlon

    scored: list[tuple[float, dict[str, Any]]] = []
    for row in points:
        try:
            rlat = float(row.get(lat_key))
            rlon = float(row.get(lon_key))
        except (TypeError, ValueError):
            continue
        if rlat < lat_min or rlat > lat_max or rlon < lon_min or rlon > lon_max:
            continue
        dist = haversine_m(lat, lon, rlat, rlon)
        if dist <= radius_m:
            scored.append((dist, row))

    scored.sort(key=lambda item: item[0])
    out: list[dict[str, Any]] = []
    for dist, row in scored[:limit]:
        item = dict(row)
        item["distance_m"] = round(dist, 1)
        out.append(item)
    return out


def format_km(distance_m: float | None) -> str | None:
    if distance_m is None:
        return None
    try:
        meters = float(distance_m)
    except (TypeError, ValueError):
        return None
    if meters < 1000:
        return f"{meters:.0f} m"
    return f"{meters / 1000.0:.1f} km".replace(".", ",")
