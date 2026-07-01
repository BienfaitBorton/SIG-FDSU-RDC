from __future__ import annotations

from pathlib import Path
from typing import Literal

from .excel_handler import ExcelHandler
from .csv_handler import CSVHandler
from .geojson_handler import GeoJSONHandler
from .kml_handler import KMLHandler
from .shapefile_handler import ShapefileHandler
from .exceptions import FormatNotSupported


def get_handler(format: Literal["xlsx", "csv", "geojson", "kml", "kmz", "shp"], **kwargs):
    fmt = format.lower()
    if fmt in {"xlsx", "xls"}:
        return ExcelHandler(**kwargs)
    if fmt == "csv":
        return CSVHandler(**kwargs)
    if fmt == "geojson":
        return GeoJSONHandler(**kwargs)
    if fmt in {"kml", "kmz"}:
        return KMLHandler(**kwargs)
    if fmt in {"shp", "shapefile"}:
        return ShapefileHandler(**kwargs)
    raise FormatNotSupported(f"Format non supporté : {format}")
