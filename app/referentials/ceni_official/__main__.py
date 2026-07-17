from __future__ import annotations

import argparse
import json
import sys

from .service import CeniRegistryService


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description="Référentiel National CENI v1.0")
    parser.add_argument("command", choices=("audit", "dry-run", "validation", "import", "report", "classify", "rollback"))
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()
    service = CeniRegistryService()
    if args.command == "audit":
        result = service.audit()
    elif args.command in {"dry-run", "validation"}:
        registry = service.build(limit=args.limit)
        result = {"_meta": registry["_meta"], "statistics": registry["statistics"], "valid": registry["_meta"]["record_count"] > 0}
    elif args.command in {"import", "report"}:
        registry = service.write(service.build(limit=args.limit))
        result = {"_meta": registry["_meta"], "statistics": registry["statistics"]}
    elif args.command == "classify":
        registry = service.enrich_classification()
        result = {"_meta": registry["_meta"], "classification": registry["statistics"]["classification"], "categories": registry["statistics"]["categories"]}
    else:
        result = {"status": "manual_only", "message": "Rollback limité aux artefacts générés du batch; la source officielle n’est jamais modifiée."}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
