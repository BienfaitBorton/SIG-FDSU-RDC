from __future__ import annotations

import argparse
from pathlib import Path

from app.referentiel_administratif import (
    import_collectivites,
    import_groupements,
    import_provinces,
    import_territoires,
    import_villages,
)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Importer le référentiel administratif RDC depuis des fichiers Excel."
    )
    parser.add_argument(
        "entity",
        choices=["provinces", "territoires", "collectivites", "groupements", "villages"],
        help="Entité administrative à importer.",
    )
    parser.add_argument(
        "file",
        type=Path,
        help="Fichier Excel source.",
    )
    return parser


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()
    if not args.file.exists():
        print(f"Erreur : le fichier {args.file} est introuvable.")
        return 1

    try:
        match args.entity:
            case "provinces":
                report = import_provinces(str(args.file))
            case "territoires":
                report = import_territoires(str(args.file))
            case "collectivites":
                report = import_collectivites(str(args.file))
            case "groupements":
                report = import_groupements(str(args.file))
            case "villages":
                report = import_villages(str(args.file))
            case _:
                raise ValueError("Entité inconnue")
    except Exception as exc:
        print(f"Import échoué : {exc}")
        return 2

    print("\n".join(report.format_lines()))
    print(f"Journal enregistré dans : {report.file_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
