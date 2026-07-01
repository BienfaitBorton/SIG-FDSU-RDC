#!/usr/bin/env python3
"""Simple CLI to import the official FDSU structure Excel file.

Usage:
  python scripts/import_structure.py --file path/to/"FDSU Structure code Territoire zones.xlsx" [--username admin]
"""
import argparse
import json
import os
import sys
from pathlib import Path

# Allow the script to run both as a module and as a top-level script.
# When executed with `python scripts/import_structure.py`, the current working
# directory may not be the repository root, so add the project root to sys.path.
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.fdsu_structure_importer import FDSUStructureImporter


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", required=True, help="Chemin vers le fichier .xlsx officiel")
    parser.add_argument("--username", default="system", help="Nom d'utilisateur pour l'historique d'import")
    args = parser.parse_args()

    path = Path(args.file)
    absolute_path = path.resolve()
    print(f"Répertoire de travail courant : {os.getcwd()}")
    print(f"Chemin absolu calculé : {absolute_path}")
    if not absolute_path.exists():
        print(f"Fichier introuvable : {path}")
        print(f"Chemin absolu recherché : {absolute_path}")
        raise SystemExit(2)

    importer = FDSUStructureImporter(username=args.username)
    report = importer.import_file(path)
    print(report.summary_text())


if __name__ == "__main__":
    main()
