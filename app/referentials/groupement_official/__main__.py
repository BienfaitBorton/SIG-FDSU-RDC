from __future__ import annotations

import argparse
from pathlib import Path

from .service import GroupementOfficialReferentialService


def main() -> None:
    parser = argparse.ArgumentParser(description="Construction du Referentiel Officiel des Groupements.")
    parser.add_argument("source", type=Path, help="Chemin vers Groupements.kmz")
    parser.add_argument("--output-dir", type=Path, default=Path("data/reports/groupement_official"), help="Dossier de sortie")
    parser.add_argument(
        "--collectivity-referential",
        type=Path,
        default=Path("data/reports/collectivity_official/collectivity_referential_official.json"),
        help="Referentiel officiel des collectivites utilise pour le rattachement",
    )
    args = parser.parse_args()

    service = GroupementOfficialReferentialService()
    result = service.run(args.source, output_dir=args.output_dir, collectivity_referential_path=args.collectivity_referential)

    print("Referentiel Groupements construit")
    print(f"Source: {result.source_path}")
    print(f"Groupements: {result.report.quality.groupement_count}")
    print(f"Rattaches: {result.report.quality.attached_count}")
    print(f"Orphelins: {result.report.quality.orphan_count}")
    print(f"Anomalies: {len(result.report.quality.anomalies)}")
    print(f"Score qualite: {result.report.quality.global_score}")
    print(f"Referentiel JSON: {result.referential_json_path}")
    print(f"Fiches JSON: {result.fact_sheets_json_path}")
    print(f"Qualite JSON: {result.quality_json_path}")
    print(f"Rapport Markdown: {result.report_markdown_path}")
    print(f"Rapport fichiers: {result.files_report_path}")
    print(f"Index collectivites: {result.collectivity_index_json_path}")
    print(f"Index territoires: {result.territory_index_json_path}")
    print(f"Index provinces: {result.province_index_json_path}")
    print(f"Registre national des compteurs: {result.national_counter_registry_path}")


if __name__ == "__main__":
    main()
