"""API Territorial Intelligence Explorer v1 (+ multi-échelle)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query

from api.services import territorial_intelligence_service as tis

router = APIRouter()


@router.get("/symbology", summary="Registre unique de symbologie cartographique")
def get_symbology_registry() -> dict[str, Any]:
    from api.services import cartography_symbology_registry as symbology

    return symbology.registry_payload()


@router.get("/entities/{entity_id}", summary="Intelligence territoriale multi-échelle")
def get_entity_intelligence(entity_id: str) -> dict[str, Any]:
    from api.services import territorial_multiscale_service as tms

    result = tms.build_entity_intelligence(entity_id)
    if not result:
        raise HTTPException(status_code=404, detail="Entité territoriale introuvable.")
    return result


@router.get("/entities/{entity_id}/map", summary="Carte multi-échelle de l’entité")
def get_entity_map(entity_id: str) -> dict[str, Any]:
    from api.services import territorial_multiscale_service as tms

    entity = tms.resolve_entity(entity_id)
    if not entity:
        raise HTTPException(status_code=404, detail="Entité territoriale introuvable.")
    result = tms.build_map_for_entity(entity)
    if not result:
        raise HTTPException(status_code=404, detail="Carte introuvable.")
    return result


@router.get("/entities/{entity_id}/children", summary="Enfants administratifs directs")
def get_entity_children(entity_id: str, limit: int = Query(200, gt=0, le=1000)) -> dict[str, Any]:
    from api.services import territorial_multiscale_service as tms

    entity = tms.resolve_entity(entity_id)
    if not entity:
        raise HTTPException(status_code=404, detail="Entité territoriale introuvable.")
    children = tms.list_children(entity, limit=limit)
    return {
        "entity": {"type": entity.get("type"), "id": entity.get("id"), "name": entity.get("name")},
        "children_level": children[0]["type"] if children else None,
        "count": len(children),
        "children": children,
    }


@router.get("/territories", summary="Lister les territoires (intelligence territoriale)")
def list_territories(
    province: str | None = Query(None),
    zone: str | None = Query(None),
    priority_level: str | None = Query(None),
    data_quality: str | None = Query(None),
    q: str | None = Query(None, description="Recherche rapide"),
    limit: int = Query(500, gt=0, le=5000),
) -> dict[str, Any]:
    return tis.list_territories(
        province=province,
        zone=zone,
        priority_level=priority_level,
        data_quality=data_quality,
        q=q,
        limit=limit,
    )


@router.get("/territories/{territory_id}", summary="Profil Territorial FDSU")
def get_territory_profile(territory_id: str) -> dict[str, Any]:
    # Multi-échelle : si l’id n’est pas un territoire, renvoyer le contrat partagé
    upper = str(territory_id or "").upper()
    if not upper.startswith("TERRITOIRE") and any(
        upper.startswith(p + "-")
        for p in ("PROVINCE", "COLLECTIVITE", "GROUPEMENT", "LOCALITE", "SECTEUR", "CHEFFERIE", "CITE")
    ):
        from api.services import territorial_multiscale_service as tms

        result = tms.build_entity_intelligence(territory_id)
        if not result:
            raise HTTPException(status_code=404, detail="Entité territoriale introuvable.")
        return result
    result = tis.build_territorial_profile(territory_id)
    if not result:
        raise HTTPException(status_code=404, detail="Territoire introuvable.")
    # Enrichissement non destructif : fil d’Ariane + enfants
    try:
        from api.services import territorial_multiscale_service as tms

        multi = tms.build_entity_intelligence(territory_id)
        if multi:
            result["breadcrumb"] = multi.get("breadcrumb")
            result["children"] = multi.get("children")
            result["coverage"] = multi.get("coverage")
            result["entity"] = multi.get("entity")
    except Exception:
        pass
    return result


@router.get("/territories/{territory_id}/map", summary="Carte GeoJSON du territoire")
def get_territory_map(territory_id: str) -> dict[str, Any]:
    upper = str(territory_id or "").upper()
    if not upper.startswith("TERRITOIRE") and any(
        upper.startswith(p + "-")
        for p in ("PROVINCE", "COLLECTIVITE", "GROUPEMENT", "LOCALITE", "SECTEUR", "CHEFFERIE", "CITE")
    ):
        from api.services import territorial_multiscale_service as tms

        entity = tms.resolve_entity(territory_id)
        if not entity:
            raise HTTPException(status_code=404, detail="Entité territoriale introuvable.")
        result = tms.build_map_for_entity(entity)
        if not result:
            raise HTTPException(status_code=404, detail="Carte introuvable.")
        return result
    result = tis.build_map_payload(territory_id)
    if not result:
        raise HTTPException(status_code=404, detail="Carte territoriale introuvable.")
    return result


@router.get("/territories/{territory_id}/indicators", summary="Indicateurs territoriaux")
def get_territory_indicators(territory_id: str) -> dict[str, Any]:
    result = tis.build_indicators(territory_id)
    if not result:
        raise HTTPException(status_code=404, detail="Indicateurs territoriaux introuvables.")
    return result


@router.get("/territories/{territory_id}/recommendations", summary="Recommandations explicables")
def get_territory_recommendations(territory_id: str) -> dict[str, Any]:
    result = tis.build_recommendations(territory_id)
    if not result:
        raise HTTPException(status_code=404, detail="Recommandations introuvables.")
    return result


@router.get("/territories/{territory_id}/explain", summary="Justification territoriale")
def explain_territory(territory_id: str) -> dict[str, Any]:
    result = tis.explain_territory(territory_id)
    if not result:
        raise HTTPException(status_code=404, detail="Justification territoriale introuvable.")
    return result


@router.get(
    "/territories/{territory_id}/explainability",
    summary="Synthèses explicables par domaine (décideur)",
)
def get_explainability_bundle(territory_id: str) -> dict[str, Any]:
    from api.services import territorial_explainability_service as tex

    result = tex.build_explainability_bundle(territory_id)
    if not result:
        raise HTTPException(status_code=404, detail="Explicabilité territoriale introuvable.")
    return result


@router.get(
    "/territories/{territory_id}/details/{domain}",
    summary="Liste détaillée paginée d’un domaine territorial",
)
def get_domain_details(
    territory_id: str,
    domain: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    program: str | None = Query(None),
    level: str | None = Query(None),
) -> dict[str, Any]:
    from api.services import territorial_explainability_service as tex

    result = tex.build_domain_explain(
        territory_id,
        domain,
        page=page,
        page_size=page_size,
        program=program,
        level=level,
    )
    if not result:
        raise HTTPException(status_code=404, detail="Domaine ou territoire introuvable.")
    return result
