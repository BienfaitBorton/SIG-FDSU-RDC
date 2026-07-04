from __future__ import annotations

import argparse
import json
from pathlib import Path

from .service import LocalityOfficialReferentialService


def main() -> None:
    parser = argparse.ArgumentParser(description="Construction du Referentiel Officiel des Localites.")
    parser.add_argument("--source", default="data/raw/Localités.kmz")
    parser.add_argument("--output-dir", default="data/reports/locality_official")
    args = parser.parse_args()

    result = LocalityOfficialReferentialService().run(Path(args.source), Path(args.output_dir))
    print(
        json.dumps(
            {
                "source": str(result["source_path"]),
                "locality_count": result["quality"]["locality_count"],
                "type_distribution": result["quality"]["type_distribution"],
                "global_score": result["quality"]["global_score"],
                "created_files": result["created_files"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
