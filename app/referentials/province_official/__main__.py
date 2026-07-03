from __future__ import annotations

import argparse
import json
from pathlib import Path

from .service import ProvinceOfficialReferentialService, ProvinceReferentialValidationError


def main() -> None:
    parser = argparse.ArgumentParser(description="Construction du Referentiel Officiel des Provinces (lecture seule).")
    parser.add_argument("source", type=Path, help="Chemin vers Province26.kmz")
    parser.add_argument("--output-dir", type=Path, default=Path("data/reports/province_official"), help="Dossier de sortie")
    parser.add_argument(
        "--zones-config",
        type=Path,
        default=Path("app/referentials/config/zones_fdsu.yaml"),
        help="Configuration officielle de rattachement zones FDSU",
    )
    parser.add_argument(
        "--expected-count",
        type=int,
        default=26,
        help="Nombre attendu de provinces (interrompt le traitement si différent)",
    )
    args = parser.parse_args()

    service = ProvinceOfficialReferentialService()
    try:
        result = service.run(
            source_path=args.source,
            output_dir=args.output_dir,
            zones_config_path=args.zones_config,
            expected_province_count=args.expected_count,
        )
    except ProvinceReferentialValidationError as exc:
        print("Echec validation référentiel provinces")
        print(str(exc))
        print("Anomalies détectées:")
        print(json.dumps(exc.anomalies, ensure_ascii=False, indent=2))
        raise SystemExit(2)

    print("Referentiel Provinces construit")
    print(f"Source: {result.source_path}")
    print(f"Provinces retenues: {len(result.report.province_referential)}")
    print(f"Qualite globale: {result.report.quality.global_score}")
    print(f"Referentiel JSON: {result.referential_json_path}")
    print(f"Fiches JSON: {result.fact_sheets_json_path}")
    print(f"Qualite JSON: {result.quality_json_path}")
    print(f"Rapport Markdown: {result.report_markdown_path}")
    print(f"Rapport fichiers: {result.files_report_path}")


if __name__ == "__main__":
    main()
