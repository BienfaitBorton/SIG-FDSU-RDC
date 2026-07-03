from __future__ import annotations

import argparse
from pathlib import Path

from .service import TerritoryHierarchyService


def main() -> None:
    parser = argparse.ArgumentParser(description="Extraction hiérarchique des territoires depuis KMZ Zones (lecture seule).")
    parser.add_argument("source", type=Path, help="Chemin vers zones_fdsu.kmz")
    parser.add_argument("--output-dir", type=Path, default=Path("data/reports/territory_hierarchy"), help="Dossier de sortie")
    args = parser.parse_args()

    service = TerritoryHierarchyService()
    result = service.run(args.source, output_dir=args.output_dir)

    print("Extraction territoriale hiérarchique terminée")
    print(f"Source: {result.source_path}")
    print(f"Territoires: {result.report.territory_count}")
    print(f"Incohérences: {result.report.incoherence_count}")
    print(f"Rapport JSON: {result.report_json_path}")
    print(f"Rapport Markdown: {result.report_markdown_path}")


if __name__ == "__main__":
    main()
