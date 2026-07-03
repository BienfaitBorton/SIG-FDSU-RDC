from __future__ import annotations

import argparse
from pathlib import Path

from .explorer import SourceExplorerService


def main() -> None:
    parser = argparse.ArgumentParser(description="Explorateur de Sources Géographiques (lecture seule).")
    parser.add_argument("source", type=Path, help="Fichier source à analyser (.kmz, .kml, .geojson, .shp)")
    parser.add_argument("--output-dir", type=Path, default=Path("data/reports/source_explorer"), help="Dossier de sortie des rapports")
    args = parser.parse_args()

    service = SourceExplorerService()
    result = service.run(args.source, output_dir=args.output_dir)

    print("Exploration terminée")
    print(f"Source: {result.source_path}")
    print(f"Objets: {result.report.object_count}")
    print(f"Dossiers: {len(result.report.folders)}")
    print(f"Rapport JSON: {result.report_json_path}")
    print(f"Rapport Markdown: {result.report_markdown_path}")


if __name__ == "__main__":
    main()
