from datetime import datetime
from typing import Any

from api.schemas.knowledge import (
    KnowledgePriority,
    KnowledgeProfile,
    KnowledgeSearchResult,
    KnowledgeSection,
    KnowledgeSource,
    KnowledgeSuggestionsResponse,
    KnowledgeSummary,
)

MISSING_VALUE = "Donnée non encore renseignée"

KNOWLEDGE_ENTITY_TYPES = [
    "Zone",
    "Province",
    "Ville-Province",
    "Territoire",
    "Ville",
    "Collectivité",
    "Secteur",
    "Chefferie",
    "Groupement",
    "Localité",
    "Village",
    "Site FDSU",
    "Mission",
]

KNOWLEDGE_SECTION_DEFINITIONS = [
    ("presentation", "Présentation"),
    ("administration", "Administration"),
    ("geographie", "Géographie"),
    ("subdivision", "Subdivision"),
    ("population", "Population"),
    ("activites_economiques_principales", "Activités économiques principales"),
    ("activites_economiques_secondaires", "Activités économiques secondaires"),
    ("particularites", "Particularités"),
    ("defis", "Défis"),
    ("potentiel_agricole", "Potentiel agricole"),
    ("potentiel_minier", "Potentiel minier"),
    ("potentiel_forestier", "Potentiel forestier"),
    ("potentiel_touristique", "Potentiel touristique"),
    ("potentiel_numerique", "Potentiel numérique"),
    ("services_publics", "Services publics"),
    ("connectivite", "Connectivité"),
    ("infrastructures", "Infrastructures"),
    ("documents", "Documents"),
    ("photos", "Photos"),
    ("rapports", "Rapports"),
    ("historique", "Historique"),
    ("sources", "Sources"),
    ("analyse_fdsu", "Analyse FDSU"),
]

CNCT_WORKFLOW = ["Recherche", "Propositions", "Comparaison", "Validation", "Publication"]
INTELLIGENCE_LINKS = ["Matrice FDSU", "KPI", "Scores", "Simulation", "Classements", "Recommandations"]

DEMO_SOURCE = KnowledgeSource(
    source="Référentiel FDSU interne",
    author="SIG-FDSU RDC",
    date="2026-07-04",
    url=None,
    confidence_level="interne",
    status="validé",
)

DEMO_PROFILES: dict[str, dict[str, Any]] = {
    "kinshasa": {
        "entity": "kinshasa",
        "entity_type": "Ville-Province",
        "title": "Kinshasa",
        "sections": {
            "presentation": "Ville-Province de la RDC.",
            "administration": "Statut Ville-Province.",
            "subdivision": "Districts : Funa, Lukunga, Mont-Amba, Tshangu.",
            "sources": "Sources internes et propositions contrôlées uniquement.",
        },
        "completeness": {
            "Référentiel": 100,
            "Subdivision": 100,
            "Activités": 0,
            "Défis": 0,
            "Services publics": 0,
            "Connectivité": 0,
            "Photos": 0,
            "Documents": 0,
        },
    },
    "territoire-exemple": {
        "entity": "territoire-exemple",
        "entity_type": "Territoire",
        "title": "Territoire exemple",
        "sections": {},
        "completeness": {
            "Référentiel": 100,
            "Subdivision": 60,
            "Activités": 0,
            "Défis": 0,
            "Services publics": 0,
            "Connectivité": 0,
            "Photos": 0,
            "Documents": 0,
        },
    },
}

PRIORITIES = [
    KnowledgePriority(
        province="Kinshasa",
        territoire="Ville-Province",
        completeness=25,
        missing_fields_count=18,
        priority="haute",
        last_updated_at="2026-07-04",
    ),
    KnowledgePriority(
        province="À qualifier",
        territoire="Territoire exemple",
        completeness=12,
        missing_fields_count=22,
        priority="critique",
        last_updated_at="2026-07-04",
    ),
]


def build_sections(raw_sections: dict[str, Any]) -> list[KnowledgeSection]:
    sections = []
    for key, label in KNOWLEDGE_SECTION_DEFINITIONS:
        value = raw_sections.get(key, MISSING_VALUE)
        has_value = bool(value and value != MISSING_VALUE)
        sections.append(
            KnowledgeSection(
                key=key,
                label=label,
                value=value or MISSING_VALUE,
                completeness=100 if has_value else 0,
                sources=[DEMO_SOURCE] if has_value else [],
            )
        )
    return sections


def build_profile(entity: str) -> KnowledgeProfile:
    key = entity.lower()
    raw = DEMO_PROFILES.get(key, {
        "entity": entity,
        "entity_type": "Entité territoriale",
        "title": entity,
        "sections": {},
        "completeness": {},
    })
    return KnowledgeProfile(
        entity=raw["entity"],
        entity_type=raw["entity_type"],
        title=raw["title"],
        updated_at=datetime.utcnow(),
        workflow=CNCT_WORKFLOW,
        sections=build_sections(raw.get("sections", {})),
        completeness=raw.get("completeness", {}),
        intelligence_links=INTELLIGENCE_LINKS,
    )


def get_knowledge_summary() -> KnowledgeSummary:
    return KnowledgeSummary(
        complete_profiles=0,
        incomplete_profiles=len(DEMO_PROFILES),
        profiles_without_photo=len(DEMO_PROFILES),
        profiles_without_activities=len(DEMO_PROFILES),
        profiles_without_challenges=len(DEMO_PROFILES),
        profiles_without_public_services=len(DEMO_PROFILES),
        profiles_without_connectivity=len(DEMO_PROFILES),
        profiles_without_documents=len(DEMO_PROFILES),
        workflow=CNCT_WORKFLOW,
    )


def list_completeness_priorities() -> list[KnowledgePriority]:
    return PRIORITIES


def search_knowledge(query: str) -> list[KnowledgeSearchResult]:
    text = query.strip().lower()
    if not text:
        return []
    results = []
    for raw in DEMO_PROFILES.values():
        matched_fields = []
        haystack_parts = [raw["title"], raw["entity_type"]]
        for key, value in raw.get("sections", {}).items():
            label = dict(KNOWLEDGE_SECTION_DEFINITIONS).get(key, key)
            haystack_parts.append(str(value))
            if text in str(value).lower() or text in label.lower():
                matched_fields.append(label)
        haystack = " ".join(haystack_parts).lower()
        if text in haystack:
            completeness_values = list(raw.get("completeness", {}).values())
            completeness = int(sum(completeness_values) / len(completeness_values)) if completeness_values else 0
            results.append(
                KnowledgeSearchResult(
                    entity=raw["title"],
                    entity_type=raw["entity_type"],
                    matched_fields=matched_fields or ["Présentation"],
                    excerpt=next(iter(raw.get("sections", {}).values()), MISSING_VALUE),
                    completeness=completeness,
                )
            )
    return results


def get_suggestions_ready_state() -> KnowledgeSuggestionsResponse:
    return KnowledgeSuggestionsResponse(
        workflow=CNCT_WORKFLOW,
        automatic_collection_enabled=False,
        suggestions_ready=True,
        items=[
            {
                "entity": "Kinshasa",
                "field": "Activités économiques principales",
                "status": "à rechercher",
                "next_step": "Créer une proposition sourcée puis comparer avant validation.",
            },
            {
                "entity": "Territoire exemple",
                "field": "Services publics",
                "status": "à rechercher",
                "next_step": "Attendre une source institutionnelle validable.",
            },
        ],
    )
