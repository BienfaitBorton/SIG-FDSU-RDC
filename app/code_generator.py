from __future__ import annotations


def generate_fdsu_code(
    zone: str,
    province_code: str,
    territoire_code: str,
    collectivite_code: str,
    numero: str | int,
) -> str:
    """Generate a normalized FDSU code for a site.

    Format: FDSU_<ZONE>_<PROVINCE>_<TERRITOIRE>_<COLLECTIVITE>_<NUMERO>
    Example: FDSU_ND_26_145_001_001
    """
    zone_normalized = str(zone).upper().strip()
    province_segment = str(province_code).strip().zfill(2)
    territoire_segment = str(territoire_code).strip().zfill(3)
    collectivite_segment = str(collectivite_code).strip().zfill(3)
    numero_segment = str(numero).strip().zfill(3)

    if not zone_normalized:
        raise ValueError("Zone value must not be empty")

    return (
        f"FDSU_{zone_normalized}_"
        f"{province_segment}_"
        f"{territoire_segment}_"
        f"{collectivite_segment}_"
        f"_{numero_segment}"
    )
