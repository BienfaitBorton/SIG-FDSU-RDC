from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.orm import Session

from api.dependencies import get_db
from api.schemas.decision import DecisionRecord, DecisionSearchResponse

router = APIRouter()

DECISION_FIELDS = [
    "population",
    "couverture_2g",
    "couverture_3g",
    "couverture_4g",
    "couverture_5g",
    "centre_sante",
    "ecole_primaire",
    "ecole_secondaire",
    "marche",
    "electricite",
    "activite_principale",
    "activite_secondaire",
    "potentiel_agricole",
    "potentiel_minier",
    "potentiel_commercial",
    "potentiel_numerique",
    "niveau_enclavement",
    "score_connectivite",
    "score_potentiel",
    "score_priorite_fdsu",
    "recommandation",
]


def _as_float(value: Any) -> Any:
    if isinstance(value, Decimal):
        return float(value)
    return value


def _record_from_mapping(row: Any, niveau: str) -> DecisionRecord:
    data = dict(row)
    payload = {
        key: _as_float(data.get(key))
        for key in DecisionRecord.model_fields
        if key not in {"champs_a_completer"}
    }
    payload["niveau"] = niveau
    payload["champs_a_completer"] = [field for field in DECISION_FIELDS if data.get(field) is None]
    return DecisionRecord(**payload)


def _safe_rows(db: Session, sql: str, params: dict[str, Any]) -> list[dict[str, Any]]:
    try:
        return [dict(row) for row in db.execute(text(sql), params).mappings().all()]
    except ProgrammingError as error:
        db.rollback()
        message = str(getattr(error, "orig", error)).lower()
        if "does not exist" in message or "n'existe pas" in message or "undefinedtable" in message:
            return []
        raise


def _add_common_filters(
    where: list[str],
    params: dict[str, Any],
    *,
    zone: str | None,
    province: str | None,
    territoire: str | None,
    couverture_reseau: str | None,
    centre_sante: bool | None,
    ecole_secondaire: bool | None,
    activite_economique: str | None,
    potentiel: str | None,
    niveau_connectivite: float | None,
    score_priorite_min: float | None,
) -> None:
    if zone:
        where.append("z.code = :zone")
        params["zone"] = zone
    if province:
        where.append("p.nom ILIKE :province")
        params["province"] = f"%{province}%"
    if territoire:
        where.append("t.nom ILIKE :territoire")
        params["territoire"] = f"%{territoire}%"
    if couverture_reseau:
        coverage_column = {
            "2G": "cp.couverture_2g",
            "3G": "cp.couverture_3g",
            "4G": "cp.couverture_4g",
            "5G": "cp.couverture_5g",
        }.get(couverture_reseau.upper())
        if coverage_column:
            where.append(f"{coverage_column} IS TRUE")
    if centre_sante is not None:
        where.append("ps.centre_sante = :centre_sante")
        params["centre_sante"] = centre_sante
    if ecole_secondaire is not None:
        where.append("ps.ecole_secondaire = :ecole_secondaire")
        params["ecole_secondaire"] = ecole_secondaire
    if activite_economique:
        where.append("(ea.activite_principale ILIKE :activite OR ea.activite_secondaire ILIKE :activite)")
        params["activite"] = f"%{activite_economique}%"
    if potentiel:
        where.append(
            "("
            "ea.potentiel_agricole ILIKE :potentiel OR "
            "ea.potentiel_minier ILIKE :potentiel OR "
            "ea.potentiel_commercial ILIKE :potentiel OR "
            "ea.potentiel_numerique ILIKE :potentiel"
            ")"
        )
        params["potentiel"] = f"%{potentiel}%"
    if niveau_connectivite is not None:
        where.append("cp.score_connectivite <= :niveau_connectivite")
        params["niveau_connectivite"] = niveau_connectivite
    if score_priorite_min is not None:
        where.append("fps.score_priorite_fdsu >= :score_priorite_min")
        params["score_priorite_min"] = score_priorite_min


def _where_clause(where: list[str]) -> str:
    return "WHERE " + " AND ".join(where) if where else ""


def _locality_sql(where: list[str]) -> str:
    return f"""
        SELECT
            l.id,
            l.nom,
            l.code,
            z.code AS zone,
            p.nom AS province,
            t.nom AS territoire,
            c.nom AS collectivite,
            g.nom AS groupement,
            tp.population,
            cp.couverture_2g,
            cp.couverture_3g,
            cp.couverture_4g,
            cp.couverture_5g,
            ps.centre_sante,
            ps.ecole_primaire,
            ps.ecole_secondaire,
            ps.marche,
            ps.electricite,
            ea.activite_principale,
            ea.activite_secondaire,
            ea.potentiel_agricole,
            ea.potentiel_minier,
            ea.potentiel_commercial,
            ea.potentiel_numerique,
            tp.niveau_enclavement,
            cp.score_connectivite,
            ea.score_potentiel,
            fps.score_priorite_fdsu,
            fps.recommandation
        FROM localites l
        JOIN groupements g ON g.id = l.parent_id
        JOIN collectivites c ON c.id = g.parent_id
        JOIN territoires t ON t.id = c.parent_id
        JOIN provinces p ON p.id = t.parent_id
        JOIN zones z ON z.id = p.parent_id
        LEFT JOIN territorial_profiles tp ON tp.localite_id = l.id
        LEFT JOIN connectivity_profiles cp ON cp.localite_id = l.id
        LEFT JOIN public_services ps ON ps.localite_id = l.id
        LEFT JOIN economic_activities ea ON ea.localite_id = l.id
        LEFT JOIN fdsu_priority_scores fps ON fps.localite_id = l.id
        {_where_clause(where)}
        ORDER BY fps.score_priorite_fdsu DESC NULLS LAST, l.nom
        LIMIT :limit
    """


def _territory_sql(where: list[str]) -> str:
    return f"""
        SELECT
            t.id,
            t.nom,
            t.code,
            z.code AS zone,
            p.nom AS province,
            t.nom AS territoire,
            NULL::text AS collectivite,
            NULL::text AS groupement,
            tp.population,
            cp.couverture_2g,
            cp.couverture_3g,
            cp.couverture_4g,
            cp.couverture_5g,
            ps.centre_sante,
            ps.ecole_primaire,
            ps.ecole_secondaire,
            ps.marche,
            ps.electricite,
            ea.activite_principale,
            ea.activite_secondaire,
            ea.potentiel_agricole,
            ea.potentiel_minier,
            ea.potentiel_commercial,
            ea.potentiel_numerique,
            tp.niveau_enclavement,
            cp.score_connectivite,
            ea.score_potentiel,
            fps.score_priorite_fdsu,
            fps.recommandation
        FROM territoires t
        JOIN provinces p ON p.id = t.parent_id
        JOIN zones z ON z.id = p.parent_id
        LEFT JOIN territorial_profiles tp ON tp.territoire_id = t.id
        LEFT JOIN connectivity_profiles cp ON cp.territoire_id = t.id
        LEFT JOIN public_services ps ON ps.territoire_id = t.id
        LEFT JOIN economic_activities ea ON ea.territoire_id = t.id
        LEFT JOIN fdsu_priority_scores fps ON fps.territoire_id = t.id
        {_where_clause(where)}
        ORDER BY fps.score_priorite_fdsu DESC NULLS LAST, t.nom
        LIMIT :limit
    """


@router.get("/localites-prioritaires", response_model=list[DecisionRecord])
def localites_prioritaires(
    zone: str | None = None,
    province: str | None = None,
    territoire: str | None = None,
    population_min: int = Query(3000, ge=0),
    couverture_reseau: str | None = None,
    centre_sante: bool | None = True,
    ecole_secondaire: bool | None = True,
    activite_economique: str | None = None,
    potentiel: str | None = "fort",
    niveau_connectivite: float | None = None,
    score_priorite_min: float | None = None,
    limit: int = Query(100, gt=0, le=1000),
    db: Session = Depends(get_db),
) -> list[DecisionRecord]:
    where = [
        "tp.population > :population_min",
        "cp.couverture_4g IS FALSE",
    ]
    params: dict[str, Any] = {"population_min": population_min, "limit": limit}
    if potentiel:
        where.append("ea.potentiel_agricole ILIKE :potentiel_agricole")
        params["potentiel_agricole"] = f"%{potentiel}%"
    _add_common_filters(
        where,
        params,
        zone=zone,
        province=province,
        territoire=territoire,
        couverture_reseau=couverture_reseau,
        centre_sante=centre_sante,
        ecole_secondaire=ecole_secondaire,
        activite_economique=activite_economique,
        potentiel=None,
        niveau_connectivite=niveau_connectivite,
        score_priorite_min=score_priorite_min,
    )
    return [_record_from_mapping(row, "localite") for row in _safe_rows(db, _locality_sql(where), params)]


@router.get("/territoires-prioritaires", response_model=list[DecisionRecord])
def territoires_prioritaires(
    zone: str | None = "ND",
    province: str | None = None,
    territoire: str | None = None,
    activite_economique: str | None = None,
    potentiel: str | None = "fort",
    niveau_connectivite: float | None = 40,
    score_priorite_min: float | None = None,
    limit: int = Query(100, gt=0, le=1000),
    db: Session = Depends(get_db),
) -> list[DecisionRecord]:
    where: list[str] = []
    params: dict[str, Any] = {"limit": limit}
    _add_common_filters(
        where,
        params,
        zone=zone,
        province=province,
        territoire=territoire,
        couverture_reseau=None,
        centre_sante=None,
        ecole_secondaire=None,
        activite_economique=activite_economique,
        potentiel=potentiel,
        niveau_connectivite=niveau_connectivite,
        score_priorite_min=score_priorite_min,
    )
    return [_record_from_mapping(row, "territoire") for row in _safe_rows(db, _territory_sql(where), params)]


@router.get("/search", response_model=DecisionSearchResponse)
def search(
    q: str | None = Query(None, description="Recherche par nom, code, activite ou recommandation."),
    zone: str | None = None,
    province: str | None = None,
    territoire: str | None = None,
    population_min: int | None = Query(None, ge=0),
    couverture_reseau: str | None = None,
    centre_sante: bool | None = None,
    ecole_secondaire: bool | None = None,
    activite_economique: str | None = None,
    potentiel: str | None = None,
    niveau_connectivite: float | None = None,
    score_priorite_min: float | None = None,
    niveau: str | None = Query(None, pattern="^(localite|territoire)$"),
    limit: int = Query(100, gt=0, le=1000),
    db: Session = Depends(get_db),
) -> DecisionSearchResponse:
    records: list[DecisionRecord] = []
    include_localites = niveau in (None, "localite")
    include_territoires = niveau in (None, "territoire")

    if include_localites:
        where: list[str] = ["fps.id IS NOT NULL"]
        params: dict[str, Any] = {"limit": limit}
        _add_common_filters(
            where,
            params,
            zone=zone,
            province=province,
            territoire=territoire,
            couverture_reseau=couverture_reseau,
            centre_sante=centre_sante,
            ecole_secondaire=ecole_secondaire,
            activite_economique=activite_economique,
            potentiel=potentiel,
            niveau_connectivite=niveau_connectivite,
            score_priorite_min=score_priorite_min,
        )
        if population_min is not None:
            where.append("tp.population >= :population_min")
            params["population_min"] = population_min
        if q:
            where.append(
                "("
                "l.nom ILIKE :q OR l.code ILIKE :q OR "
                "ea.activite_principale ILIKE :q OR ea.activite_secondaire ILIKE :q OR "
                "fps.recommandation ILIKE :q"
                ")"
            )
            params["q"] = f"%{q}%"
        records.extend(_record_from_mapping(row, "localite") for row in _safe_rows(db, _locality_sql(where), params))

    if include_territoires and len(records) < limit:
        where = ["fps.id IS NOT NULL"]
        params = {"limit": limit - len(records)}
        _add_common_filters(
            where,
            params,
            zone=zone,
            province=province,
            territoire=territoire,
            couverture_reseau=couverture_reseau,
            centre_sante=centre_sante,
            ecole_secondaire=ecole_secondaire,
            activite_economique=activite_economique,
            potentiel=potentiel,
            niveau_connectivite=niveau_connectivite,
            score_priorite_min=score_priorite_min,
        )
        if population_min is not None:
            where.append("tp.population >= :population_min")
            params["population_min"] = population_min
        if q:
            where.append(
                "("
                "t.nom ILIKE :q OR t.code ILIKE :q OR "
                "ea.activite_principale ILIKE :q OR ea.activite_secondaire ILIKE :q OR "
                "fps.recommandation ILIKE :q"
                ")"
            )
            params["q"] = f"%{q}%"
        records.extend(_record_from_mapping(row, "territoire") for row in _safe_rows(db, _territory_sql(where), params))

    records.sort(key=lambda item: (item.score_priorite_fdsu is None, -(item.score_priorite_fdsu or 0), item.nom))
    records = records[:limit]
    return DecisionSearchResponse(total=len(records), items=records)
