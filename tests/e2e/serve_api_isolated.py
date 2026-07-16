"""Serveur API Playwright avec historique des décisions isolé hors du dépôt."""

from __future__ import annotations

import argparse
import shutil
import sys
import uuid
from pathlib import Path

import uvicorn

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from api.services import explainable_decision_service


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8001)
    args = parser.parse_args()

    runtime_path = Path(explainable_decision_service.HISTORY_PATH)
    test_runtime_dir = PROJECT_ROOT / "work" / "test-runtime"
    test_runtime_dir.mkdir(parents=True, exist_ok=True)
    isolated_path = test_runtime_dir / f"case_history-e2e-{uuid.uuid4().hex}.json"
    try:
        if runtime_path.exists():
            shutil.copy2(runtime_path, isolated_path)
        explainable_decision_service.HISTORY_PATH = isolated_path
        # Importer l'application seulement apres la redirection. Certains
        # modules initialises par api.main peuvent charger/calculer un dossier
        # de decision pendant l'import ; ils ne doivent jamais voir le chemin
        # runtime reel dans un processus de test.
        from api.main import app

        uvicorn.run(app, host=args.host, port=args.port)
    finally:
        isolated_path.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
