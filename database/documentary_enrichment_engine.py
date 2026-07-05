from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sqlalchemy.orm import sessionmaker

from api.services.documentary_enrichment_service import documentary_engine_status
from app.database import engine
from app.models import TerritorialEnrichmentSuggestion

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Moteur documentaire CNCT - enrichissement par propositions.")
    parser.add_argument("--max-files", type=int, default=30, help="Nombre maximum de fichiers texte internes à analyser.")
    parser.add_argument("--commit", action="store_true", help="Insere les propositions dans territorial_enrichment_suggestions.")
    parser.add_argument("--json", action="store_true", help="Affiche le resultat complet en JSON.")
    return parser.parse_args()


def insert_suggestions(suggestions: list[dict]) -> int:
    inserted = 0
    with SessionLocal() as session:
        for item in suggestions:
            consulted_at = item.get("consulted_at")
            if isinstance(consulted_at, str):
                consulted_at = datetime.fromisoformat(consulted_at)
            suggestion = TerritorialEnrichmentSuggestion(
                entity_type=item.get("entity_type") or "Entité territoriale",
                entity_name=item.get("entity_name") or "Entité à qualifier",
                field_name=item.get("field_name") or "champ_a_qualifier",
                proposed_value=item.get("proposed_value") or "",
                source_name=item.get("source_name") or "Document interne",
                source_url=item.get("source_url") or "",
                consulted_at=consulted_at,
                confidence_level=item.get("confidence_level") or "à vérifier",
                status="proposé",
                review_note=item.get("excerpt") or "",
            )
            session.add(suggestion)
            inserted += 1
        session.commit()
    return inserted


def main() -> int:
    args = parse_args()
    payload = documentary_engine_status(max_files=args.max_files)
    suggestions = payload["internal_engine"]["suggestions"]
    inserted = insert_suggestions(suggestions) if args.commit else 0
    payload["execution"] = {
        "commit": args.commit,
        "inserted_suggestions": inserted,
        "official_tables_modified": False,
        "target_table": "territorial_enrichment_suggestions" if args.commit else None,
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print("Moteur documentaire CNCT")
        print(f"Fichiers supportes : {payload['audit']['supported_files']}")
        print(f"Fichiers analyses : {len(payload['internal_engine']['analyzed_files'])}")
        print(f"Propositions preparees : {payload['internal_engine']['merged_suggestions_count']}")
        print(f"Insertion : {inserted} proposition(s)" if args.commit else "Insertion : non, simulation uniquement")
        print("Tables officielles modifiees : non")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
