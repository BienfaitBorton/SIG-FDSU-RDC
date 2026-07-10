"""Générateur de codes FDSU aligné sur la nomenclature officielle."""

from __future__ import annotations


def generate_fdsu_code(
    zone: str,
    province_code: str,
    territoire_code: str,
    collectivite_code: str,
    numero: str | int,
) -> str:
    """Génère un code FDSU normalisé.

    Format officiel:
      FDSU_<ZONE>_<PROVINCE>_<TERRITOIRE>_<COLLECTIVITE>_<NUMERO>
    Exemple étendu: FDSU_ND_26_145_001_001
    Format court (sans collectivité vide): FDSU_ND_18_003_10100
    """
    zone_normalized = str(zone).upper().strip()
    province_segment = str(province_code).strip().zfill(2)
    territoire_segment = str(territoire_code).strip().zfill(3)
    collectivite_segment = str(collectivite_code).strip().zfill(3)
    numero_segment = str(numero).strip().zfill(3)

    if not zone_normalized:
        raise ValueError("Zone value must not be empty")

    # Évite le double underscore historique et les collectivité "000" vides.
    if collectivite_segment in {"", "000"}:
        return (
            f"FDSU_{zone_normalized}_"
            f"{province_segment}_"
            f"{territoire_segment}_"
            f"{numero_segment}"
        )

    return (
        f"FDSU_{zone_normalized}_"
        f"{province_segment}_"
        f"{territoire_segment}_"
        f"{collectivite_segment}_"
        f"{numero_segment}"
    )
