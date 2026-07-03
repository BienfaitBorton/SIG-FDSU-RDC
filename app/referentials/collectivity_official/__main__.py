from __future__ import annotations

import argparse
from pathlib import Path

from .service import CollectivityOfficialReferentialService


def main() -> None:
    parser = argparse.ArgumentParser(description="Construction du Referentiel Officiel des Collectivites.")
    parser.add_argument("source", type=Path, help="Chemin vers collectivites.kmz")
    parser.add_argument("--output-dir", type=Path, default=Path("data/reports/collectivity_official"), help="Dossier de sortie")
    parser.add_argument(
        "--territory-report",
        type=Path,
        default=Path("data/reports/territory_hierarchy/territoires_hierarchie_kmz.report.json"),
        help="Rapport territorial KMZ utilise pour rattacher les collectivites par code INS",
    )
    args = parser.parse_args()

    service = CollectivityOfficialReferentialService()
    result = service.run(args.source, output_dir=args.output_dir, territory_report_path=args.territory_report)

    print("Referentiel Collectivites construit")
    print(f"Source: {result.source_path}")
    print(f"Secteurs: {result.report.quality.secteur_count}")
    print(f"Chefferies: {result.report.quality.chefferie_count}")
    print(f"Total collectivites: {result.report.quality.collectivity_count}")
    print(f"Anomalies: {len(result.report.quality.anomalies)}")
    print(f"Score qualite: {result.report.quality.global_score}")
    print(f"Referentiel JSON: {result.referential_json_path}")
    print(f"Fiches JSON: {result.fact_sheets_json_path}")
    print(f"Qualite JSON: {result.quality_json_path}")
    print(f"Rapport Markdown: {result.report_markdown_path}")
    print(f"Rapport fichiers: {result.files_report_path}")
    print(f"Index territoires: {result.territory_index_json_path}")
    print(f"Index provinces: {result.province_index_json_path}")
    print(f"Registre national des compteurs: {result.national_counter_registry_path}")


if __name__ == "__main__":
    main()
