from __future__ import annotations

from pathlib import Path
from .pipeline import GeospatialPipeline


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Analyse un ou plusieurs KMZ et produit des GeoJSON enrichis.")
    parser.add_argument("kmz", nargs="+", type=Path)
    parser.add_argument("--output-dir", type=Path, default=Path("data/geodata/generated"))
    parser.add_argument("--report-dir", type=Path, default=Path("data/geodata/generated/reports"))
    args = parser.parse_args()

    pipeline = GeospatialPipeline()

    for kmz_path in args.kmz:
      stem = kmz_path.stem.lower().replace(" ", "_")
      output_geojson = args.output_dir / f"{stem}.geojson"
      output_report = args.report_dir / f"{stem}.report.json"
      report = pipeline.process(kmz_path, output_geojson, output_report)
      print(f"{kmz_path.name}: {report.feature_count} entités, GeoJSON -> {output_geojson}, rapport -> {output_report}")


if __name__ == "__main__":
    main()
