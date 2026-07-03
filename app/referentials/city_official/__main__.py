from __future__ import annotations

import argparse
from pathlib import Path

from .service import CityOfficialReferentialService


def main() -> None:
    parser = argparse.ArgumentParser(description="Construction du Referentiel Officiel des Villes (TYPE=Commune).")
    parser.add_argument("source", type=Path, help="Chemin vers le KMZ des Zones")
    parser.add_argument("--output-dir", type=Path, default=Path("data/reports/city_official"), help="Dossier de sortie")
    args = parser.parse_args()

    service = CityOfficialReferentialService()
    result = service.run(args.source, output_dir=args.output_dir)

    print("Referentiel Villes construit")
    print(f"Source: {result.source_path}")
    print(f"Villes retenues: {len(result.report.city_referential)}")
    print(f"Qualite globale: {result.report.quality.global_score}")
    print(f"Referentiel JSON: {result.referential_json_path}")
    print(f"Fiches JSON: {result.fact_sheets_json_path}")
    print(f"Qualite JSON: {result.quality_json_path}")
    print(f"Rapport Markdown: {result.report_markdown_path}")
    print(f"Rapport fichiers: {result.files_report_path}")


if __name__ == "__main__":
    main()
