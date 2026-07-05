#!/usr/bin/env python3
"""Importer tous les fichiers du Référentiel FDSU présents dans un dossier, dans l'ordre officiel.

Expected filenames (order enforced):
  01_Provinces.xlsx
  02_Territoires.xlsx
  03_Collectivites.xlsx
  04_Groupements.xlsx
  05_Villages.xlsx
  06_Sites.xlsx

Usage:
  python scripts/import_all_referentiel.py --dir path/to/Referentiel --mapping app/io/fdsu_mapping_example.json --username admin
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List

from app.fdsu_importer import FDSUExcelImporter


SEQUENCE = [
    ("01_Provinces.xlsx", "province"),
    ("02_Territoires.xlsx", "territoire"),
    ("03_Collectivites.xlsx", "collectivite"),
    ("04_Groupements.xlsx", "groupement"),
    ("05_Villages.xlsx", "village"),
    ("06_Sites.xlsx", "site"),
]


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Importer séquentiellement les fichiers du Référentiel FDSU dans un dossier")
    p.add_argument("--dir", required=True, help="Dossier contenant les fichiers du Référentiel")
    p.add_argument("--mapping", required=False, help="Fichier JSON de mapping des colonnes (optionnel)")
    p.add_argument("--username", required=False, default="cli", help="Nom d'utilisateur pour l'historique d'import")
    p.add_argument("--continue-on-error", action="store_true", help="Continuer l'import même si une entité échoue")
    p.add_argument("--create-parents", action="store_true", help="Créer automatiquement les parents manquants pendant l'import")
    return p.parse_args()


def _print_short(rep) -> None:
    print(f"{rep.filename} -> read={rep.rows_total} inserted={rep.rows_inserted} updated={rep.rows_updated} rejected={rep.rows_rejected} durée={rep.duration_seconds:.2f}s")


def main() -> int:
    args = parse_args()
    base = Path(args.dir)
    if not base.exists() or not base.is_dir():
        print(f"Dossier introuvable: {base}")
        return 2

    mapping_path = Path(args.mapping) if args.mapping else None
    if mapping_path and not mapping_path.exists():
        print(f"Fichier mapping introuvable: {mapping_path}")
        return 3

    importer = FDSUExcelImporter(username=args.username)

    total_read = total_inserted = total_updated = total_rejected = 0
    reports: List[object] = []

    for fname, entity in SEQUENCE:
        fpath = base / fname
        if not fpath.exists():
            print(f"Fichier absent, on passe: {fpath}")
            continue
        print(f"--- Import {fname} ({entity}) ---")
        try:
            report = importer.import_file(fpath, entity=entity, mapping_json=mapping_path, create_parents=args.create_parents)
        except Exception as exc:
            print(f"Erreur import {fname}: {exc}")
            if not args.continue_on_error:
                print("Arrêt de la séquence à cause d'une erreur.")
                return 4
            else:
                continue

        reports.append(report)
        total_read += report.rows_total
        total_inserted += report.rows_inserted
        total_updated += report.rows_updated
        total_rejected += report.rows_rejected

        # print per-file short summary and detailed errors if any
        print(f"Résumé {fname}:")
        print(json.dumps(report.as_dict(), ensure_ascii=False, indent=2))

    # final summary
    print("\n=== Résumé global ===")
    print(f"Fichiers traités : {len(reports)}")
    print(f"Total lignes lues : {total_read}")
    print(f"Total insérées    : {total_inserted}")
    print(f"Total mises à jour: {total_updated}")
    print(f"Total rejetées    : {total_rejected}")

    # heuristic exit code
    if total_read > 0 and total_rejected / total_read > 0.5:
        print("Plus de 50% des lignes rejetées sur l'ensemble — vérifier les fichiers et mappings.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
