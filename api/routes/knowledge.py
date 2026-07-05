from fastapi import APIRouter, Query

from api.schemas.knowledge import (
    KnowledgePriority,
    KnowledgeProfile,
    KnowledgeSearchResult,
    KnowledgeSuggestionsResponse,
    KnowledgeSummary,
)
from api.services.knowledge_service import (
    KNOWLEDGE_ENTITY_TYPES,
    KNOWLEDGE_SECTION_DEFINITIONS,
    build_profile,
    get_knowledge_summary,
    get_suggestions_ready_state,
    list_completeness_priorities,
    search_knowledge,
)
from api.services.documentary_enrichment_service import (
    audit_project_data,
    data_origins_status,
    documentary_engine_status,
    read_demo_enrichment_cache,
    scan_internal_documents,
)

router = APIRouter()


@router.get("", response_model=KnowledgeSummary, summary="Tableau de bord CNCT")
def read_knowledge_dashboard() -> KnowledgeSummary:
    return get_knowledge_summary()


@router.get("/types", summary="Types encyclopédiques CNCT")
def read_knowledge_types() -> dict[str, list[str]]:
    return {"types": KNOWLEDGE_ENTITY_TYPES}


@router.get("/sections", summary="Rubriques encyclopédiques CNCT")
def read_knowledge_sections() -> dict[str, list[dict[str, str]]]:
    return {"sections": [{"key": key, "label": label} for key, label in KNOWLEDGE_SECTION_DEFINITIONS]}


@router.get("/search", response_model=list[KnowledgeSearchResult], summary="Recherche CNCT")
def search(q: str = Query("", description="Recherche dans activités, défis, particularités, potentiel, sources et rapports.")) -> list[KnowledgeSearchResult]:
    return search_knowledge(q)


@router.get("/completeness", response_model=list[KnowledgePriority], summary="Priorités d'enrichissement")
def completeness() -> list[KnowledgePriority]:
    return list_completeness_priorities()


@router.get("/suggestions", response_model=KnowledgeSuggestionsResponse, summary="Suggestions prêtes sans collecte automatique")
def suggestions() -> KnowledgeSuggestionsResponse:
    return get_suggestions_ready_state()


@router.get("/documentary/audit", summary="Audit documentaire CNCT")
def documentary_audit() -> dict:
    return audit_project_data()


@router.get("/documentary/origins", summary="Origines et statut des donnees CNCT")
def documentary_origins() -> dict:
    return data_origins_status()


@router.get("/documentary/internal-suggestions", summary="Suggestions internes sans publication")
def documentary_internal_suggestions(max_files: int = Query(30, ge=1, le=100)) -> dict:
    return scan_internal_documents(max_files=max_files)


@router.get("/documentary/status", summary="Etat complet du moteur documentaire CNCT")
def documentary_status(max_files: int = Query(30, ge=1, le=100)) -> dict:
    return documentary_engine_status(max_files=max_files)


@router.get("/demo-enrichment", summary="Cache demo CNCT sans publication officielle")
def demo_enrichment() -> dict:
    return read_demo_enrichment_cache()


@router.get("/{entity}", response_model=KnowledgeProfile, summary="Fiche encyclopédique CNCT")
def read_entity_knowledge(entity: str) -> KnowledgeProfile:
    return build_profile(entity)
