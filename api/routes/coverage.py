"""API National Coverage Intelligence — Référentiel National des Besoins."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query

from api.services import coverage_intelligence_service as nci

router = APIRouter()


@router.get("", summary="Vue d'ensemble NCI")
@router.get("/", summary="Vue d'ensemble NCI", include_in_schema=False)
def coverage_overview() -> dict[str, Any]:
    return nci.overview()


@router.get("/statistics", summary="Statistiques nationales de couverture")
def coverage_statistics() -> dict[str, Any]:
    return nci.statistics()


@router.get("/provinces", summary="Agrégats par province")
def coverage_provinces(limit: int = Query(100, gt=0, le=200)) -> dict[str, Any]:
    return nci.list_provinces(limit=limit)


@router.get("/territories", summary="Agrégats par territoire + NDCI")
def coverage_territories(
    province: str | None = Query(None),
    q: str | None = Query(None),
    limit: int = Query(500, gt=0, le=2000),
) -> dict[str, Any]:
    return nci.list_territories(province=province, q=q, limit=limit)


@router.get("/localities", summary="Localités (besoins) — pagination")
def coverage_localities(
    status: str | None = Query("uncovered", description="uncovered|covered|all"),
    province: str | None = Query(None),
    territoire: str | None = Query(None),
    priority: str | None = Query(None),
    categorie: str | None = Query(None),
    q: str | None = Query(None),
    limit: int = Query(200, gt=0, le=2000),
    offset: int = Query(0, ge=0),
) -> dict[str, Any]:
    return nci.list_localities(
        status=status,
        province=province,
        territoire=territoire,
        priority=priority,
        categorie=categorie,
        q=q,
        limit=limit,
        offset=offset,
    )


@router.get("/population", summary="Population couverte / restante")
def coverage_population() -> dict[str, Any]:
    return nci.population_payload()


@router.get("/priority", summary="Répartition des priorités")
def coverage_priority() -> dict[str, Any]:
    return nci.priority_payload()


@router.get("/categories", summary="Répartition des catégories")
def coverage_categories() -> dict[str, Any]:
    return nci.categories_payload()


@router.get("/infrastructure", summary="Types d'infrastructures essentielles")
def coverage_infrastructure() -> dict[str, Any]:
    return nci.infrastructure_payload()


@router.get("/map", summary="GeoJSON besoins (chargement progressif)")
def coverage_map(
    status: str = Query("uncovered"),
    province: str | None = Query(None),
    territoire: str | None = Query(None),
    priority: str | None = Query(None),
    limit: int = Query(3000, gt=0, le=15000),
) -> dict[str, Any]:
    return nci.map_payload(
        status=status,
        province=province,
        territoire=territoire,
        priority=priority,
        limit=limit,
    )


@router.get("/explain", summary="Explicabilité NDCI (national ou territoire)")
def coverage_explain(
    territoire: str | None = Query(None, description="Nom du territoire (optionnel)"),
) -> dict[str, Any]:
    if territoire:
        result = nci.explain_territory_index(territoire)
        if not result.get("available"):
            raise HTTPException(status_code=404, detail=result.get("why") or "Territoire introuvable")
        return result
    stats = nci.statistics()
    charts = nci.edvs_charts()
    return {
        "available": True,
        "scope": "national",
        "why": (
            "Le Référentiel National des Besoins compare population couverte / restante, "
            "localités, priorités, catégories, distances et infrastructures."
        ),
        "kpis": stats.get("kpis"),
        "priority": stats.get("priorities"),
        "categories": stats.get("categories"),
        "ndci_top": stats.get("ndci_top"),
        "charts_available": list(charts.keys()),
        "confidence_level": "high",
        "sources": (nci.get_manifest().get("sources") or []),
    }


@router.get("/edvs", summary="Graphiques exécutifs NCI (EDVS)")
def coverage_edvs() -> dict[str, Any]:
    return nci.edvs_charts()
