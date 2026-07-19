#!/usr/bin/env python3
"""Synchronise le programme national Sites 20 476 vers programs.fdsu_sites (NSME).

Usage:
  python database/sync_sites_20476_nsme.py
  python database/sync_sites_20476_nsme.py --dry-run
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

os.environ.setdefault("DATA_MODE", "db")
os.environ.setdefault("PYTHONPATH", str(PROJECT_ROOT))


def main() -> int:
    parser = argparse.ArgumentParser(description="Sync Sites 20476 → programs.fdsu_sites")
    parser.add_argument("--dry-run", action="store_true", help="Simuler sans écrire")
    args = parser.parse_args()

    from api.services import fdsu_sites_nsme_sync_service as sync

    result = sync.sync_sites_20476_to_nsme(dry_run=args.dry_run)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if not args.dry_run and not result.get("integrated_natively"):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
