from pathlib import Path

print("=" * 60)
print("      SIG FDSU RDC - Initialisation")
print("=" * 60)

# Racine du projet
ROOT = Path(__file__).resolve().parent.parent

# Dossiers à créer
folders = [
    "data/raw",
    "data/processed",
    "database",
    "exports",
    "imports",
    "docs",
    "backup",
    "dashboard",
    "web",
    "mobile",
    "qgis",
    "resources",
    "styles",
    "tests"
]

for folder in folders:
    path = ROOT / folder
    path.mkdir(parents=True, exist_ok=True)
    print(f"[OK] {path}")

print()
print("Projet SIG-FDSU prêt.")
print(f"Emplacement : {ROOT}")