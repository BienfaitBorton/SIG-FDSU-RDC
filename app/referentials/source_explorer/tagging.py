from __future__ import annotations

from typing import Iterable

CATEGORY_RULES: list[tuple[str, tuple[str, ...]]] = [
    ("Télécommunications", ("telecom", "antenne", "bts", "site", "fibre", "cell", "tower", "radio")),
    ("Sites", ("site", "emplacement", "station")),
    ("Planification", ("plan", "phase", "deploiement", "priorite")),
    ("Couverture", ("couverture", "coverage", "signal")),
    ("Backbone", ("backbone", "fibre", "trunk", "liaison")),
    ("Population", ("population", "demographie", "menage", "habitants")),
    ("Statistiques", ("kpi", "stat", "indicateur", "score", "ratio")),
    ("Documents", ("document", "rapport", "fiche", "pdf", "reference")),
    ("Photos", ("photo", "image", "media", "capture")),
    ("Référentiel administratif", ("province", "territoire", "commune", "secteur", "chefferie", "groupement", "village", "collectivite", "administratif")),
]

MODULE_MAPPING: dict[str, str] = {
    "Référentiel administratif": "Gestion des Référentiels",
    "Télécommunications": "Cartographie",
    "Sites": "Sites FDSU",
    "Planification": "Statistiques",
    "Couverture": "Cartographie",
    "Backbone": "Cartographie",
    "Population": "Statistiques",
    "Statistiques": "Statistiques",
    "Documents": "Gestion des Référentiels",
    "Photos": "Gestion des Référentiels",
    "Autres": "Dashboard",
}


def classify_category(folder_name: str, fields: Iterable[str]) -> str:
    corpus = " ".join([folder_name, *fields]).lower()
    for category, keywords in CATEGORY_RULES:
        if any(keyword in corpus for keyword in keywords):
            return category
    return "Autres"


def suggest_module(category: str) -> str:
    return MODULE_MAPPING.get(category, "Dashboard")


def compute_tags(folder_name: str, fields: Iterable[str], category: str) -> list[str]:
    corpus = " ".join([folder_name, *fields]).lower()
    tags: list[str] = [category]

    conditional_tags = {
        "Sites": ("site", "bts", "station"),
        "Backbone": ("backbone", "fibre"),
        "Province": ("province",),
        "Territoire": ("territoire",),
        "Village": ("village",),
        "Collectivité": ("collectivite", "secteur", "chefferie", "groupement"),
        "Déploiement": ("deploiement", "phase", "plan"),
        "KPI": ("kpi", "indicateur", "score", "ratio"),
        "Télécommunications": ("telecom", "antenne", "fibre", "radio", "couverture"),
    }

    for tag, keywords in conditional_tags.items():
        if any(keyword in corpus for keyword in keywords):
            tags.append(tag)

    # Keep insertion order while removing duplicates.
    seen: set[str] = set()
    unique_tags: list[str] = []
    for tag in tags:
        if tag not in seen:
            seen.add(tag)
            unique_tags.append(tag)
    return unique_tags
