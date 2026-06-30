from __future__ import annotations

import argparse
from pathlib import Path

from app.importer import import_fdsu, preview_import


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Importer les fichiers officiels FDSU vers le référentiel administratif RDC."
    )
    parser.add_argument(
        "file",
        type=Path,
        help="Chemin vers le fichier FDSU (xlsx, xls ou csv).",
    )
    parser.add_argument(
        "--entity",
        choices=["provinces", "territoires", "collectivites", "groupements", "villages"],
        help="Entité à importer. Si absent, toutes les entités seront traitées dans l'ordre hiérarchique.",
    )
    parser.add_argument(
        "--mapping",
        type=Path,
        help="Fichier JSON de mapping des colonnes FDSU vers les champs ORM.",
    )
    parser.add_argument(
        "--username",
        help="Nom de l'utilisateur qui exécute l'import.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Valider l'import sans persister les modifications.",
    )
    parser.add_argument(
        "--preview",
        action="store_true",
        help="Afficher un aperçu de l'import et du mapping avant exécution.",
    )
    return parser


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()
    file_path = args.file
    if not file_path.exists():
        print(f"Erreur : fichier introuvable {file_path}")
        return 1

    if args.preview:
        previews = preview_import(
            str(file_path),
            entity=args.entity,
            mapping_path=str(args.mapping) if args.mapping else None,
        )
        for entity_name, preview_data in previews.items():
            print(f"\n=== {entity_name} ===")
            print(f"Feuille détectée : {preview_data['sheet_name']}")
            print(f"Colonnes mappées : {preview_data['mapped_columns']}")
            if preview_data["missing_fields"]:
                print(f"Champs manquants : {preview_data['missing_fields']}")
            if preview_data["errors"]:
                print("Erreurs :")
                for error in preview_data["errors"]:
                    print(f"  - {error}")
            print("Échantillon de lignes :")
            for row in preview_data["sample"]:
                print(f"  - {row}")
        return 0

    report = import_fdsu(
        str(file_path),
        username=args.username,
        entity=args.entity,
        mapping_path=str(args.mapping) if args.mapping else None,
        dry_run=args.dry_run,
    )

    print(report.format_summary())
    return 0 if report.status in {"success", "dry-run"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
