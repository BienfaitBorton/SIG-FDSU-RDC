"""Experimental controlled web probe for territorial enrichment suggestions.

This script searches public institutional sources for a small fixed sample and
prepares suggestions in territorial_enrichment_suggestions only. It never
updates official territorial profiles, knowledge records, provinces,
territoires or localites.

Usage:
    python database/web_enrichment_probe.py
    python database/web_enrichment_probe.py --commit

Without --commit, the script writes the report only. With --commit, it inserts
the prepared suggestions into territorial_enrichment_suggestions.
"""

from __future__ import annotations

import argparse
import html
import re
import sys
import unicodedata
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable
from urllib.error import HTTPError, URLError
from urllib.parse import quote_plus, urlparse
from urllib.request import Request, urlopen

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from sqlalchemy.orm import Session  # noqa: E402

from app.database import engine  # noqa: E402
from app.models import TerritorialEnrichmentSuggestion  # noqa: E402


MAX_ENTITIES = 5
MAX_SOURCES_PER_ENTITY = 3
MAX_SUGGESTIONS_PER_ENTITY = 10
MAX_SEARCH_QUERIES_PER_ENTITY = 1
REPORT_PATH = ROOT_DIR / "PROJECT_MANAGEMENT" / "SPRINT_REPORTS" / "WEB_ENRICHMENT_PROBE_REPORT.md"
CONSULTED_AT = datetime.now(timezone.utc).replace(microsecond=0)
STATUS_PROPOSED = "proposé"

ENTITIES = [
    {"name": "Kinshasa", "type": "Ville-Province"},
    {"name": "Haut-Uélé", "type": "Province"},
    {"name": "Dungu", "type": "Territoire"},
    {"name": "Banalia", "type": "Territoire"},
    {"name": "Wando", "type": "Chefferie"},
][:MAX_ENTITIES]

FIELDS = {
    "situation_economique": ["economie", "économie", "revenu", "commerce", "industrie"],
    "activites_economiques_principales": ["principales activités", "activites principales", "agriculture", "élevage", "peche", "pêche", "commerce"],
    "activites_economiques_secondaires": ["secondaires", "petit commerce", "artisanat", "chasse"],
    "particularites": ["particularité", "particularites", "parc", "site", "culture", "langue", "frontiere", "frontière"],
    "defis": ["défis", "defis", "enclavement", "insécurité", "insecurite", "impraticable", "pauvreté", "pauvrete"],
    "potentiel_agricole": ["agricole", "agriculture", "cacao", "café", "huile", "vivrière", "vivriere"],
    "potentiel_minier": ["minier", "mine", "or", "diamant", "minerai", "fer"],
    "potentiel_commercial": ["commercial", "commerce", "marché", "marche", "transport", "port"],
    "potentiel_touristique": ["touristique", "tourisme", "parc national", "chutes", "réserve", "reserve"],
    "services_publics": ["hôpital", "hopital", "école", "ecole", "santé", "sante", "administration", "université", "universite"],
    "connectivite": ["connectivité", "connectivite", "réseau", "reseau", "route", "fibre", "internet", "télécom", "telecom"],
    "infrastructures": ["infrastructure", "route", "pont", "aéroport", "aeroport", "port", "rail", "bâtiment", "batiment"],
}

SOURCE_QUERIES = [
    ("CAID", "site:caid.cd {entity} RDC profil territoire activités économie"),
    ("INS", "site:ins-rdc.org {entity} RDC annuaire statistique"),
    ("ARPTC", "site:arptc.gouv.cd {entity} RDC couverture réseau télécommunications"),
    ("Ministères RDC", "site:gouv.cd {entity} RDC économie infrastructures services publics"),
    ("Gouvernorat", "{entity} gouvernorat RDC économie infrastructures site:gouv.cd OR site:hautuele.cd"),
    ("Rapport institutionnel", "{entity} RDC agriculture mines infrastructures rapport institutionnel filetype:pdf"),
    ("OpenStreetMap", "site:openstreetmap.org {entity} Democratic Republic Congo"),
]

DIRECT_SOURCE_URLS = {
    "Kinshasa": [
        ("CAID", "https://www.caid.cd/index.php/donnees-par-villes/ville-de-kinshasa/?domaine=fiche"),
        ("CAID", "https://caid.cd/index.php/donnees-par-villes/ville-de-kinshasa/?domaine=fiche"),
    ],
    "Haut-Uélé": [
        ("CAID", "https://www.caid.cd/index.php/donnees-par-province-administrative/province-de-haut-uele/?domaine=fiche"),
        ("CAID", "https://caid.cd/index.php/donnees-par-province-administrative/province-de-haut-uele/?domaine=fiche"),
    ],
    "Dungu": [
        ("CAID", "https://www.caid.cd/index.php/donnees-par-territoire/territoire-de-dungu/?domaine=fiche"),
        ("CAID", "https://caid.cd/index.php/donnees-par-territoire/territoire-de-dungu/?domaine=fiche"),
    ],
    "Banalia": [
        ("CAID", "https://www.caid.cd/index.php/donnees-par-territoire/territoire-de-banalia/?domaine=fiche"),
        ("CAID", "https://caid.cd/index.php/donnees-par-territoire/territoire-de-banalia/?domaine=fiche"),
    ],
    "Wando": [
        ("CAID", "https://www.caid.cd/index.php/donnees-par-territoire/territoire-de-dungu/?domaine=fiche"),
    ],
}

ALLOWED_DOMAINS = {
    "caid.cd",
    "www.caid.cd",
    "ins-rdc.org",
    "www.ins-rdc.org",
    "arptc.gouv.cd",
    "www.arptc.gouv.cd",
    "gouv.cd",
    "www.gouv.cd",
    "hautuele.cd",
    "www.hautuele.cd",
    "openstreetmap.org",
    "www.openstreetmap.org",
}


@dataclass
class SourceCandidate:
    entity: str
    source_name: str
    url: str
    title: str
    text: str


@dataclass
class Proposal:
    entity_name: str
    entity_type: str
    field_name: str
    proposed_value: str
    source_name: str
    source_url: str
    consulted_at: datetime
    confidence_level: str
    excerpt: str
    status: str = STATUS_PROPOSED


def fetch_url(url: str, timeout: int = 3) -> str:
    request = Request(
        url,
        headers={
            "User-Agent": "SIG-FDSU-RDC-WebEnrichmentProbe/0.1 (+controlled validation workflow)",
            "Accept-Language": "fr,en;q=0.8",
        },
    )
    with urlopen(request, timeout=timeout) as response:
        content_type = response.headers.get("Content-Type", "")
        raw = response.read(1_500_000)
    if "pdf" in content_type.lower():
        return ""
    return raw.decode("utf-8", errors="ignore")


def search_web(query: str) -> list[str]:
    search_url = f"https://duckduckgo.com/html/?q={quote_plus(query)}"
    body = fetch_url(search_url)
    urls = []
    for match in re.finditer(r'class="result__a"[^>]+href="([^"]+)"', body):
        url = html.unescape(match.group(1))
        if url.startswith("//duckduckgo.com/l/?uddg="):
            encoded = re.search(r"uddg=([^&]+)", url)
            if encoded:
                from urllib.parse import unquote

                url = unquote(encoded.group(1))
        if is_allowed_url(url) and url not in urls:
            urls.append(url)
    return urls


def is_allowed_url(url: str) -> bool:
    parsed = urlparse(url)
    host = parsed.netloc.lower().split(":")[0]
    return parsed.scheme in {"http", "https"} and host in ALLOWED_DOMAINS


def clean_text(raw_html: str) -> str:
    text = re.sub(r"(?is)<(script|style).*?</\1>", " ", raw_html)
    text = re.sub(r"(?s)<[^>]+>", " ", text)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def normalize_text(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value)
    ascii_text = "".join(char for char in decomposed if not unicodedata.combining(char))
    return re.sub(r"\s+", " ", ascii_text.lower()).strip()


def is_entity_specific(entity: str, text: str) -> bool:
    normalized_entity = normalize_text(entity)
    normalized_text = normalize_text(text)
    if normalized_entity in normalized_text:
        return True
    if entity == "Haut-Uélé" and "haut-uele" in normalized_text:
        return True
    return False


def is_generic_or_search_page(source_name: str, url: str, title: str, text: str) -> bool:
    normalized_title = normalize_text(title)
    normalized_url = normalize_text(url)
    normalized_text = normalize_text(text)
    if source_name == "CAID" and "accueil_caid" in normalized_title:
        return True
    if source_name == "OpenStreetMap" and "/search" in normalized_url:
        return True
    generic_caid_markers = [
        "secteurs decouvrez les differents secteurs que traite la caid",
        "institution de la republique la presidence",
        "immeuble semois",
    ]
    return source_name == "CAID" and all(marker in normalized_text for marker in generic_caid_markers)


def extract_title(raw_html: str) -> str:
    match = re.search(r"(?is)<title[^>]*>(.*?)</title>", raw_html)
    return clean_text(match.group(1)) if match else "Source publique"


def split_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+", text)
    return [part.strip() for part in parts if len(part.strip()) >= 45]


def discover_sources(entity: str) -> tuple[list[SourceCandidate], list[str]]:
    sources: list[SourceCandidate] = []
    errors: list[str] = []
    seen_urls: set[str] = set()
    for source_name, url in DIRECT_SOURCE_URLS.get(entity, []):
        if len(sources) >= MAX_SOURCES_PER_ENTITY:
            break
        if url in seen_urls or not is_allowed_url(url):
            continue
        seen_urls.add(url)
        try:
            body = fetch_url(url)
        except (HTTPError, URLError, TimeoutError, OSError) as exc:
            errors.append(f"{entity} / {url}: lecture directe impossible ({exc})")
            continue
        text = clean_text(body)
        title = extract_title(body)
        if len(text) < 120:
            errors.append(f"{entity} / {url}: source directe trop courte ou non exploitable")
            continue
        if is_generic_or_search_page(source_name, url, title, text):
            errors.append(f"{entity} / {url}: page generique ou recherche non exploitable")
            continue
        if not is_entity_specific(entity, text):
            errors.append(f"{entity} / {url}: page accessible mais non specifique a l'entite")
            continue
        sources.append(
            SourceCandidate(
                entity=entity,
                source_name=source_name,
                url=url,
                title=title,
                text=text,
            )
        )
    search_count = 0
    for source_name, template in SOURCE_QUERIES:
        if len(sources) >= MAX_SOURCES_PER_ENTITY:
            break
        if search_count >= MAX_SEARCH_QUERIES_PER_ENTITY:
            break
        search_count += 1
        query = template.format(entity=entity)
        try:
            urls = search_web(query)
        except (HTTPError, URLError, TimeoutError, OSError) as exc:
            errors.append(f"{entity} / {source_name}: recherche impossible ({exc})")
            continue
        for url in urls:
            if len(sources) >= MAX_SOURCES_PER_ENTITY:
                break
            if url in seen_urls:
                continue
            seen_urls.add(url)
            try:
                body = fetch_url(url)
            except (HTTPError, URLError, TimeoutError, OSError) as exc:
                errors.append(f"{entity} / {url}: lecture impossible ({exc})")
                continue
            text = clean_text(body)
            title = extract_title(body)
            if len(text) < 120:
                continue
            if is_generic_or_search_page(source_name, url, title, text):
                continue
            if not is_entity_specific(entity, text):
                continue
            sources.append(
                SourceCandidate(
                    entity=entity,
                    source_name=source_name,
                    url=url,
                    title=title,
                    text=text,
                )
            )
    return sources[:MAX_SOURCES_PER_ENTITY], errors


def build_proposals(entity: dict[str, str], sources: Iterable[SourceCandidate]) -> list[Proposal]:
    proposals: list[Proposal] = []
    seen_fields: set[str] = set()
    entity_name = entity["name"]
    entity_type = entity["type"]
    for source in sources:
        sentences = split_sentences(source.text)
        for field_name, keywords in FIELDS.items():
            if len(proposals) >= MAX_SUGGESTIONS_PER_ENTITY:
                return proposals
            if field_name in seen_fields:
                continue
            excerpt = first_matching_sentence(sentences, keywords)
            if not excerpt:
                continue
            if source.source_name == "OpenStreetMap" and field_name not in {"particularites", "infrastructures", "connectivite"}:
                continue
            seen_fields.add(field_name)
            proposals.append(
                Proposal(
                    entity_name=entity_name,
                    entity_type=entity_type,
                    field_name=field_name,
                    proposed_value=excerpt[:900],
                    source_name=source.source_name,
                    source_url=source.url,
                    consulted_at=CONSULTED_AT,
                    confidence_level=confidence_for_source(source.source_name),
                    excerpt=excerpt[:900],
                )
            )
    return proposals


def first_matching_sentence(sentences: list[str], keywords: list[str]) -> str | None:
    for sentence in sentences:
        normalized = sentence.lower()
        if any(keyword.lower() in normalized for keyword in keywords):
            return sentence
    return None


def confidence_for_source(source_name: str) -> str:
    if source_name in {"CAID", "INS", "ARPTC", "Ministères RDC", "Gouvernorat"}:
        return "élevé"
    if source_name == "Rapport institutionnel":
        return "moyen"
    return "appui géographique"


def insert_proposals(proposals: list[Proposal]) -> int:
    if not proposals:
        return 0
    inserted = 0
    with Session(engine) as session:
        for proposal in proposals:
            existing = (
                session.query(TerritorialEnrichmentSuggestion)
                .filter(
                    TerritorialEnrichmentSuggestion.entity_name == proposal.entity_name,
                    TerritorialEnrichmentSuggestion.entity_type == proposal.entity_type,
                    TerritorialEnrichmentSuggestion.field_name == proposal.field_name,
                    TerritorialEnrichmentSuggestion.source_url == proposal.source_url,
                    TerritorialEnrichmentSuggestion.status == STATUS_PROPOSED,
                )
                .first()
            )
            if existing:
                continue
            session.add(
                TerritorialEnrichmentSuggestion(
                    entity_type=proposal.entity_type,
                    entity_id=None,
                    entity_name=proposal.entity_name,
                    field_name=proposal.field_name,
                    proposed_value=proposal.proposed_value,
                    source_name=proposal.source_name,
                    source_url=proposal.source_url,
                    consulted_at=proposal.consulted_at.replace(tzinfo=None),
                    confidence_level=proposal.confidence_level,
                    status=STATUS_PROPOSED,
                    review_note=f"Extrait/resume source: {proposal.excerpt}",
                )
            )
            inserted += 1
        session.commit()
    return inserted


def write_report(
    *,
    committed: bool,
    inserted_count: int,
    sources_by_entity: dict[str, list[SourceCandidate]],
    proposals_by_entity: dict[str, list[Proposal]],
    errors: list[str],
) -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# SIG-FDSU RDC - Web Enrichment Probe",
        "",
        f"Date de consultation : {CONSULTED_AT.isoformat()}",
        f"Mode insertion : {'commit' if committed else 'dry-run'}",
        f"Propositions inserees : {inserted_count}",
        "",
        "## Perimetre",
        "",
        "- Maximum 5 entites.",
        "- Maximum 10 propositions par entite.",
        "- Maximum 3 sources par entite.",
        "- Aucune ecriture dans `territorial_profiles`, `knowledge`, `localites`, `territoires` ou `provinces`.",
        "- Insertion autorisee uniquement dans `territorial_enrichment_suggestions` lorsque `--commit` est utilise.",
        "",
        "## Sources trouvees",
        "",
    ]
    for entity in ENTITIES:
        name = entity["name"]
        lines.append(f"### {name}")
        found = sources_by_entity.get(name, [])
        if not found:
            lines.append("- Aucune source publique autorisee exploitable trouvee pendant ce probe.")
        for source in found:
            lines.append(f"- {source.source_name} : [{source.title}]({source.url})")
        lines.append("")

    lines.extend(["## Donnees proposees", ""])
    for entity in ENTITIES:
        name = entity["name"]
        proposals = proposals_by_entity.get(name, [])
        lines.append(f"### {name}")
        if not proposals:
            lines.append("- Aucune proposition creee sans source exploitable.")
        for proposal in proposals:
            lines.append(
                f"- `{proposal.field_name}` | {proposal.source_name} | confiance `{proposal.confidence_level}` | "
                f"statut `{proposal.status}` : {proposal.proposed_value}"
            )
        lines.append("")

    lines.extend(["## Donnees non trouvees", ""])
    for entity in ENTITIES:
        name = entity["name"]
        found_fields = {proposal.field_name for proposal in proposals_by_entity.get(name, [])}
        missing_fields = [field for field in FIELDS if field not in found_fields]
        lines.append(f"- {name} : {', '.join(missing_fields) if missing_fields else 'aucune lacune detectee dans les champs cibles du probe'}")

    lines.extend(["", "## Risques", ""])
    lines.extend([
        "- Les moteurs de recherche peuvent retourner des pages non officielles ou des miroirs ; le script filtre par domaine autorise.",
        "- Les pages institutionnelles peuvent changer de structure ou etre indisponibles.",
        "- Les extraits textuels ne constituent pas une validation metier.",
        "- OpenStreetMap est limite a l'appui geographique et ne doit pas fonder seul une donnee economique.",
    ])

    lines.extend(["", "## Limites", ""])
    if errors:
        lines.append("- Erreurs ou indisponibilites observees :")
        for error in errors[:20]:
            lines.append(f"  - {error}")
    else:
        lines.append("- Aucun incident technique signale pendant ce probe.")
    lines.extend([
        "- Le script ne contourne pas les restrictions reseau de l'environnement Codex.",
        "- Si l'environnement n'a pas acces a Internet, aucune donnee n'est inventee et aucune proposition n'est creee.",
    ])

    lines.extend(["", "## Recommandations", ""])
    lines.extend([
        "- Executer d'abord sans `--commit` pour relire le rapport.",
        "- Valider manuellement chaque proposition dans l'assistant d'enrichissement.",
        "- Ajouter une liste de pages institutionnelles fixes si CAID, INS ou ARPTC exposent des URL stables.",
        "- Ajouter une extraction PDF controlee lors d'un sprint dedie si les rapports institutionnels sont majoritairement au format PDF.",
    ])
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run(commit: bool) -> int:
    all_errors: list[str] = []
    sources_by_entity: dict[str, list[SourceCandidate]] = {}
    proposals_by_entity: dict[str, list[Proposal]] = {}
    all_proposals: list[Proposal] = []

    for entity in ENTITIES:
        sources, errors = discover_sources(entity["name"])
        all_errors.extend(errors)
        sources_by_entity[entity["name"]] = sources
        proposals = build_proposals(entity, sources)
        proposals_by_entity[entity["name"]] = proposals
        all_proposals.extend(proposals)

    inserted_count = insert_proposals(all_proposals) if commit else 0
    write_report(
        committed=commit,
        inserted_count=inserted_count,
        sources_by_entity=sources_by_entity,
        proposals_by_entity=proposals_by_entity,
        errors=all_errors,
    )
    return inserted_count


def main() -> None:
    parser = argparse.ArgumentParser(description="Controlled web enrichment probe.")
    parser.add_argument("--commit", action="store_true", help="Insert proposals into territorial_enrichment_suggestions.")
    args = parser.parse_args()
    inserted = run(commit=args.commit)
    mode = "commit" if args.commit else "dry-run"
    print(f"Probe termine en mode {mode}. Propositions inserees: {inserted}. Rapport: {REPORT_PATH}")


if __name__ == "__main__":
    main()
