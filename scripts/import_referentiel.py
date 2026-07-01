#!/usr/bin/env python
"""Script CLI pour importer les référentiels administratifs officiels FDSU.

Usage:
    python scripts/import_referentiel.py --entity provinces --file fichier.xlsx [--mapping mapping.json] [--username admin]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from app.fdsu_importer import FDSUExcelImporter


PLURALS = {
    "provinces": "province",
    "province": "province",
    "territoires": "territoire",
    "territoire": "territoire",
    "collectivites": "collectivite",
    "collectivite": "collectivite",
    "groupements": "groupement",
    "groupement": "groupement",
    "villages": "village",
    "village": "village",
    "sites": "site",
    "site": "site",
}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Importer les référentiels administratifs FDSU depuis un fichier Excel")
    p.add_argument("--entity", required=True, help="Entité à importer (provinces, territoires, collectivites, groupements, villages, sites)")
    p.add_argument("--file", required=True, help="Chemin vers le fichier Excel à importer")
    p.add_argument("--mapping", required=False, help="Chemin vers fichier JSON de mapping des colonnes")
    p.add_argument("--username", required=False, default="cli", help="Nom d'utilisateur qui lance l'import (pour import_history)")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    entity_raw = args.entity.strip().lower()
    entity = PLURALS.get(entity_raw)
    if not entity:
        print(f"Entité inconnue: {args.entity}")
        return 2

    file_path = Path(args.file)
    if not file_path.exists():
        print(f"Fichier introuvable: {file_path}")
        return 3

    mapping_path = Path(args.mapping) if args.mapping else None
    if mapping_path and not mapping_path.exists():
        print(f"Fichier de mapping introuvable: {mapping_path}")
        return 4

    importer = FDSUExcelImporter(username=args.username)
    print(f"Import: entity={entity}, file={file_path}, mapping={mapping_path}")
    report = importer.import_file(file_path, entity=entity, mapping_json=mapping_path)

    # Affichage résumé
    print("\n=== Résumé de l'import ===")
    print(f"Lignes lues     : {report.rows_total}")
    print(f"Insérées        : {report.rows_inserted}")
    print(f"Mises à jour    : {report.rows_updated}")
    print(f"Rejetées        : {report.rows_rejected}")
    print(f"Durée (s)       : {report.duration_seconds:.2f}")
    print("Rapport détaillé (JSON):")
    print(json.dumps(report.as_dict(), ensure_ascii=False, indent=2))

    # exit code 0 on success or partial, 1 on error > 50% rejected (heuristic)
    if report.rows_total > 0 and report.rows_rejected / report.rows_total > 0.5:
        print("Plus de 50% des lignes ont été rejetées — vérifier le fichier et le mapping.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
#!/usr/bin/env python3
"""CLI pour importer les référentiels administratifs FDSU.

Usage:
  python scripts/import_referentiel.py --entity provinces --file fichier.xlsx [--mapping mapping.json] [--username user]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Dict

# Ensure project root is on sys.path when running this script directly
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.fdsu_importer import FDSUExcelImporter


ENTITY_MAP: Dict[str, str] = {
    "provinces": "province",
    "province": "province",
    "territoires": "territoire",
    "territoire": "territoire",
    "collectivites": "collectivite",
    "collectivite": "collectivite",
    "groupements": "groupement",
    "groupement": "groupement",
    "villages": "village",
    "village": "village",
    "sites": "site",
    "site": "site",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Importer les référentiels administratifs FDSU (Excel)")
    parser.add_argument("--entity", required=True, help="Entité à importer: provinces, territoires, collectivites, groupements, villages, sites")
    parser.add_argument("--file", required=True, help="Fichier Excel d'entrée (.xlsx)")
    parser.add_argument("--mapping", required=False, help="Fichier JSON de mapping des colonnes (optionnel)")
    parser.add_argument("--username", required=False, default="cli", help="Nom d'utilisateur pour l'historique d'import")
    parser.add_argument("--create-parents", action="store_true", help="Créer automatiquement les parents manquants pendant l'import")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    ent = args.entity.lower()
    if ent not in ENTITY_MAP:
        print(f"Entité inconnue: {args.entity}")
        return 2

    entity = ENTITY_MAP[ent]
    file_path = Path(args.file)
    if not file_path.exists():
        print(f"Fichier introuvable: {file_path}")
        return 2

    mapping_path = Path(args.mapping) if args.mapping else None
    if mapping_path and not mapping_path.exists():
        print(f"Fichier mapping introuvable: {mapping_path}")
        return 2

    importer = FDSUExcelImporter(username=args.username)
    try:
        report = importer.import_file(file_path, entity=entity, mapping_json=mapping_path, create_parents=args.create_parents)
    except Exception as exc:  # pragma: no cover - CLI top-level
        print("Erreur lors de l'import:", str(exc))
        return 3

    # Afficher résumé
    print("\n== Rapport d'import ==")
    print(f"Fichier   : {report.filename}")
    print(f"Entité    : {report.entity}")
    print(f"Lignes    : {report.rows_total}")
    print(f"Insérées  : {report.rows_inserted}")
    print(f"Mises à jour: {report.rows_updated}")
    print(f"Rejetées  : {report.rows_rejected}")
    print(f"Durée (s) : {report.duration_seconds:.2f}")

    if report.errors:
        print("\nErreurs détaillées:")
        for err in report.errors:
            print(json.dumps(err, ensure_ascii=False))

    print("== Fin du rapport ==\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
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
