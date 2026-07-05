from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEMO_ENRICHMENT_CACHE = PROJECT_ROOT / "data" / "demo_enrichment_cache.json"
DATA_ROOTS = ("data", "docs", "PROJECT_MANAGEMENT", "database", "imports", "resources")
SUPPORTED_DOCUMENT_EXTENSIONS = {
    ".docx",
    ".pdf",
    ".xlsx",
    ".csv",
    ".md",
    ".txt",
    ".json",
    ".geojson",
    ".kml",
    ".kmz",
}
TEXT_EXTENSIONS = {".md", ".txt", ".csv", ".json", ".geojson"}
MISSING_VALUE = "Donnée non encore renseignée"
DEMO_ENRICHMENT_MODE = True
AUTOMATIC_WEB_COLLECTION_ENABLED = False
OFFICIAL_PUBLICATION_ENABLED = False

CONFIDENCE_WEIGHTS = {
    "CAID": 40,
    "INS": 40,
    "MINISTERE": 35,
    "MINISTERE_RDC": 35,
    "GOUVERNORAT": 35,
    "WORLD_BANK": 30,
    "BANQUE_MONDIALE": 30,
    "FAO": 25,
    "OCHA": 25,
    "PNUD": 25,
    "UNDP": 25,
    "UNICEF": 25,
    "ARPTC": 35,
    "CENI": 25,
    "LEGANET": 25,
    "OPENSTREETMAP": 10,
    "OSM": 10,
    "WIKIPEDIA": 10,
    "POSTGRESQL": 45,
    "DOCUMENT_INTERNE": 30,
}

PUBLIC_CONNECTORS = [
    {
        "name": "CAID",
        "category": "institutionnel",
        "domains": ["caid.cd"],
        "confidence_weight": CONFIDENCE_WEIGHTS["CAID"],
        "enabled": False,
        "role": "Profils territoriaux, activités, services et infrastructures.",
    },
    {
        "name": "INS",
        "category": "institutionnel",
        "domains": ["ins.cd", "ins-rdc.org"],
        "confidence_weight": CONFIDENCE_WEIGHTS["INS"],
        "enabled": False,
        "role": "Population, statistiques nationales, indicateurs socio-économiques.",
    },
    {
        "name": "Ministères RDC",
        "category": "officiel",
        "domains": ["gouv.cd"],
        "confidence_weight": CONFIDENCE_WEIGHTS["MINISTERE"],
        "enabled": False,
        "role": "Textes officiels, programmes sectoriels, données administratives.",
    },
    {
        "name": "ARPTC",
        "category": "regulateur",
        "domains": ["arptc.gouv.cd"],
        "confidence_weight": CONFIDENCE_WEIGHTS["ARPTC"],
        "enabled": False,
        "role": "Connectivité, couverture réseau, télécommunications.",
    },
    {
        "name": "OCHA / FAO / UNICEF / UNDP",
        "category": "institutionnel international",
        "domains": ["unocha.org", "reliefweb.int", "fao.org", "unicef.org", "undp.org"],
        "confidence_weight": 25,
        "enabled": False,
        "role": "Contexte humanitaire, sécurité alimentaire, services publics, vulnérabilités.",
    },
    {
        "name": "OpenStreetMap",
        "category": "appui géographique",
        "domains": ["openstreetmap.org"],
        "confidence_weight": CONFIDENCE_WEIGHTS["OSM"],
        "enabled": False,
        "role": "Appui géographique uniquement, jamais source métier unique.",
    },
    {
        "name": "Wikipedia",
        "category": "complément",
        "domains": ["wikipedia.org"],
        "confidence_weight": CONFIDENCE_WEIGHTS["WIKIPEDIA"],
        "enabled": False,
        "role": "Complément documentaire à recouper avec une source officielle.",
    },
]

BANNED_PUBLIC_SOURCES = [
    "blogs",
    "Facebook",
    "TikTok",
    "YouTube",
    "forums",
    "contenus générés par IA",
    "sources sans auteur institutionnel",
]

FIELD_PATTERNS: dict[str, list[re.Pattern[str]]] = {
    "chef_lieu": [
        re.compile(r"^\s*(?:[-*]\s*)?chef(?:[-_\s]*)lieu\s*[:=]\s*([^\n\r.;]+)", re.IGNORECASE | re.MULTILINE),
    ],
    "superficie": [
        re.compile(r"^\s*(?:[-*]\s*)?superficie\s*[:=]\s*([^\n\r.;]+)", re.IGNORECASE | re.MULTILINE),
    ],
    "population": [
        re.compile(r"^\s*(?:[-*]\s*)?population\s*[:=]\s*([^\n\r.;]+)", re.IGNORECASE | re.MULTILINE),
    ],
    "activites_economiques_principales": [
        re.compile(r"^\s*(?:[-*]\s*)?activit(?:é|e)s?\s+principales?\s*[:=]\s*([^\n\r]+)", re.IGNORECASE | re.MULTILINE),
        re.compile(r"^\s*(?:[-*]\s*)?activit(?:é|e)s?\s+(?:é|e)conomiques?\s*[:=]\s*([^\n\r]+)", re.IGNORECASE | re.MULTILINE),
    ],
    "activites_economiques_secondaires": [
        re.compile(r"^\s*(?:[-*]\s*)?activit(?:é|e)s?\s+secondaires?\s*[:=]\s*([^\n\r]+)", re.IGNORECASE | re.MULTILINE),
    ],
    "particularites": [
        re.compile(r"^\s*(?:[-*]\s*)?particularit(?:é|e)s?\s*[:=]\s*([^\n\r]+)", re.IGNORECASE | re.MULTILINE),
    ],
    "defis": [
        re.compile(r"^\s*(?:[-*]\s*)?d(?:é|e)fis?\s*[:=]\s*([^\n\r]+)", re.IGNORECASE | re.MULTILINE),
        re.compile(r"^\s*(?:[-*]\s*)?contraintes?\s*[:=]\s*([^\n\r]+)", re.IGNORECASE | re.MULTILINE),
    ],
    "potentiel_agricole": [
        re.compile(r"^\s*(?:[-*]\s*)?potentiel\s+agricole\s*[:=]\s*([^\n\r]+)", re.IGNORECASE | re.MULTILINE),
    ],
    "potentiel_minier": [
        re.compile(r"^\s*(?:[-*]\s*)?potentiel\s+minier\s*[:=]\s*([^\n\r]+)", re.IGNORECASE | re.MULTILINE),
    ],
    "potentiel_commercial": [
        re.compile(r"^\s*(?:[-*]\s*)?potentiel\s+commercial\s*[:=]\s*([^\n\r]+)", re.IGNORECASE | re.MULTILINE),
    ],
    "potentiel_touristique": [
        re.compile(r"^\s*(?:[-*]\s*)?potentiel\s+touristique\s*[:=]\s*([^\n\r]+)", re.IGNORECASE | re.MULTILINE),
    ],
    "services_publics": [
        re.compile(r"^\s*(?:[-*]\s*)?services?\s+publics?\s*[:=]\s*([^\n\r]+)", re.IGNORECASE | re.MULTILINE),
    ],
    "connectivite": [
        re.compile(r"^\s*(?:[-*]\s*)?connectivit(?:é|e)\s*[:=]\s*([^\n\r]+)", re.IGNORECASE | re.MULTILINE),
        re.compile(r"^\s*(?:[-*]\s*)?couverture\s+r(?:é|e)seau\s*[:=]\s*([^\n\r]+)", re.IGNORECASE | re.MULTILINE),
    ],
    "infrastructures": [
        re.compile(r"^\s*(?:[-*]\s*)?infrastructures?\s*[:=]\s*([^\n\r]+)", re.IGNORECASE | re.MULTILINE),
    ],
}


@dataclass(slots=True)
class DocumentaryFinding:
    entity_name: str
    entity_type: str
    field_name: str
    proposed_value: str
    source_name: str
    source_url: str = ""
    consulted_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    confidence_level: str = "30%"
    excerpt: str = ""
    status: str = "proposé"
    sources: list[str] = field(default_factory=list)


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def source_category(source_name: str) -> str:
    normalized = source_name.upper()
    for category in CONFIDENCE_WEIGHTS:
        if category in normalized:
            return category
    if "WORLD BANK" in normalized:
        return "WORLD_BANK"
    if "BANQUE MONDIALE" in normalized:
        return "BANQUE_MONDIALE"
    if "OPENSTREETMAP" in normalized:
        return "OPENSTREETMAP"
    if "DOCUMENT" in normalized or "RAPPORT" in normalized:
        return "DOCUMENT_INTERNE"
    return "DOCUMENT_INTERNE"


def confidence_score(source_names: list[str]) -> int:
    categories = {source_category(name) for name in source_names if name}
    if not categories:
        return 0
    return min(100, sum(CONFIDENCE_WEIGHTS.get(category, 0) for category in categories))


def audit_project_data(root: Path | None = None) -> dict[str, Any]:
    base = root or PROJECT_ROOT
    roots = [base / name for name in DATA_ROOTS if (base / name).exists()]
    files: list[Path] = []
    for folder in roots:
        files.extend(path for path in folder.rglob("*") if path.is_file())

    extension_counter = Counter(path.suffix.lower() or "[sans extension]" for path in files)
    supported_files = [path for path in files if path.suffix.lower() in SUPPORTED_DOCUMENT_EXTENSIONS]
    major_sources = sorted(supported_files, key=lambda path: path.stat().st_size, reverse=True)[:20]
    internal_reports = [
        path
        for path in supported_files
        if "reports" in {part.lower() for part in path.parts} or path.suffix.lower() in {".json", ".geojson", ".md"}
    ]
    heavy_binary = [
        path
        for path in supported_files
        if path.suffix.lower() in {".pdf", ".docx", ".xlsx", ".kmz", ".kml"}
    ]
    return {
        "generated_at": datetime.utcnow().isoformat(),
        "roots": [str(path.relative_to(base)) for path in roots],
        "total_files": len(files),
        "supported_files": len(supported_files),
        "by_extension": dict(sorted(extension_counter.items())),
        "internal_reports_ready": len(internal_reports),
        "binary_connectors_ready": len(heavy_binary),
        "major_sources": [
            {
                "path": str(path.relative_to(base)),
                "extension": path.suffix.lower(),
                "size_bytes": path.stat().st_size,
                "can_feed_profiles": path.suffix.lower() in SUPPORTED_DOCUMENT_EXTENSIONS,
                "status": "indexed" if path.suffix.lower() in TEXT_EXTENSIONS else "connector prepared",
            }
            for path in major_sources
        ],
    }


def extract_entity_hint(text: str, fallback_name: str = "Entité à qualifier") -> str:
    name_match = re.search(r"(?:province|territoire|localit(?:é|e)|groupement|collectivit(?:é|e))\s+(?:de|du|d')\s+([A-ZÀ-Ÿ][^\n\r,.;:]+)", text, re.IGNORECASE)
    if name_match:
        return normalize_text(name_match.group(1))
    return fallback_name


def extract_from_internal_text(
    entity_name: str,
    entity_type: str,
    text: str,
    source_path: str,
) -> list[DocumentaryFinding]:
    findings: list[DocumentaryFinding] = []
    compact_text = text[:50000]
    source_name = f"Document interne - {Path(source_path).name}"
    for field_name, patterns in FIELD_PATTERNS.items():
        for pattern in patterns:
            match = pattern.search(compact_text)
            if not match:
                continue
            value = normalize_text(match.group(1))
            if not value or value == MISSING_VALUE:
                continue
            excerpt_start = max(0, match.start() - 80)
            excerpt_end = min(len(compact_text), match.end() + 120)
            findings.append(
                DocumentaryFinding(
                    entity_name=entity_name,
                    entity_type=entity_type,
                    field_name=field_name,
                    proposed_value=value,
                    source_name=source_name,
                    source_url=source_path,
                    confidence_level=f"{confidence_score([source_name])}%",
                    excerpt=normalize_text(compact_text[excerpt_start:excerpt_end]),
                    sources=[source_name],
                )
            )
            break
    return findings


def _json_text_fragments(payload: Any, limit: int = 60) -> list[tuple[str, str, str]]:
    fragments: list[tuple[str, str, str]] = []

    def visit(node: Any, context: dict[str, str]) -> None:
        if len(fragments) >= limit:
            return
        if isinstance(node, dict):
            next_context = dict(context)
            for key in ("nom", "name", "province", "territoire", "entity_name", "title"):
                value = node.get(key)
                if isinstance(value, str) and value.strip():
                    next_context["entity_name"] = value.strip()
                    break
            for key in ("type", "entity_type", "niveau"):
                value = node.get(key)
                if isinstance(value, str) and value.strip():
                    next_context["entity_type"] = value.strip()
                    break
            text_parts = []
            for key, value in node.items():
                if isinstance(value, str) and len(value) > 3:
                    text_parts.append(f"{key}: {value}")
            if text_parts:
                fragments.append(
                    (
                        next_context.get("entity_name", "Entité à qualifier"),
                        next_context.get("entity_type", "Entité territoriale"),
                        "\n".join(text_parts),
                    )
                )
            for value in node.values():
                visit(value, next_context)
        elif isinstance(node, list):
            for item in node[:limit]:
                visit(item, context)

    visit(payload, {})
    return fragments


def scan_internal_documents(root: Path | None = None, max_files: int = 30) -> dict[str, Any]:
    base = root or PROJECT_ROOT
    candidates: list[Path] = []
    for folder_name in DATA_ROOTS:
        folder = base / folder_name
        if folder.exists():
            candidates.extend(path for path in folder.rglob("*") if path.is_file() and path.suffix.lower() in TEXT_EXTENSIONS)
    prioritized = sorted(candidates, key=lambda path: ("reports" not in {part.lower() for part in path.parts}, path.stat().st_size))

    findings: list[DocumentaryFinding] = []
    analyzed_files: list[str] = []
    for path in prioritized[:max_files]:
        analyzed_files.append(str(path.relative_to(base)))
        try:
            raw = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        if path.suffix.lower() in {".json", ".geojson"}:
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                payload = None
            if payload is not None:
                for entity_name, entity_type, text in _json_text_fragments(payload):
                    findings.extend(extract_from_internal_text(entity_name, entity_type, text, str(path.relative_to(base))))
                continue
        entity_name = extract_entity_hint(raw)
        findings.extend(extract_from_internal_text(entity_name, "Entité territoriale", raw, str(path.relative_to(base))))

    merged = merge_findings(findings)
    return {
        "analyzed_files": analyzed_files,
        "findings_count": len(findings),
        "merged_suggestions_count": len(merged),
        "suggestions": [asdict(item) for item in merged],
    }


def merge_findings(findings: list[DocumentaryFinding]) -> list[DocumentaryFinding]:
    grouped: dict[tuple[str, str, str], list[DocumentaryFinding]] = defaultdict(list)
    for finding in findings:
        key = (
            finding.entity_name.lower(),
            finding.field_name,
            normalize_text(finding.proposed_value).lower(),
        )
        grouped[key].append(finding)

    merged: list[DocumentaryFinding] = []
    for items in grouped.values():
        first = items[0]
        source_names = []
        source_urls = []
        excerpts = []
        for item in items:
            source_names.append(item.source_name)
            if item.source_url:
                source_urls.append(item.source_url)
            if item.excerpt:
                excerpts.append(item.excerpt)
        unique_sources = list(dict.fromkeys(source_names))
        score = confidence_score(unique_sources)
        merged.append(
            DocumentaryFinding(
                entity_name=first.entity_name,
                entity_type=first.entity_type,
                field_name=first.field_name,
                proposed_value=first.proposed_value,
                source_name="; ".join(unique_sources[:3]),
                source_url="; ".join(dict.fromkeys(source_urls)),
                consulted_at=first.consulted_at,
                confidence_level=f"{score}%",
                excerpt=excerpts[0] if excerpts else "",
                status="proposé",
                sources=unique_sources,
            )
        )
    return sorted(merged, key=lambda item: (item.entity_name, item.field_name, item.proposed_value))


def data_origins_status(root: Path | None = None) -> dict[str, Any]:
    audit = audit_project_data(root)
    return {
        "automatic_web_collection_enabled": AUTOMATIC_WEB_COLLECTION_ENABLED,
        "official_publication_enabled": OFFICIAL_PUBLICATION_ENABLED,
        "validation_required": True,
        "missing_value_label": MISSING_VALUE,
        "origins": [
            {
                "origin": "PostgreSQL / PostGIS",
                "status": "prioritaire",
                "confidence": 45,
                "source_count": "tables relationnelles",
                "validation_status": "interne",
                "last_update": audit["generated_at"],
            },
            {
                "origin": "Documents internes",
                "status": "indexé",
                "confidence": 30,
                "source_count": audit["supported_files"],
                "validation_status": "proposition uniquement",
                "last_update": audit["generated_at"],
            },
            *[
                {
                    "origin": connector["name"],
                    "status": "connecteur prêt",
                    "confidence": connector["confidence_weight"],
                    "source_count": len(connector["domains"]),
                    "validation_status": "désactivé sans validation humaine",
                    "last_update": audit["generated_at"],
                }
                for connector in PUBLIC_CONNECTORS
            ],
        ],
        "banned_public_sources": BANNED_PUBLIC_SOURCES,
    }


def documentary_engine_status(root: Path | None = None, max_files: int = 30) -> dict[str, Any]:
    return {
        "audit": audit_project_data(root),
        "internal_engine": scan_internal_documents(root, max_files=max_files),
        "public_connectors": PUBLIC_CONNECTORS,
        "banned_public_sources": BANNED_PUBLIC_SOURCES,
        "rules": {
            "no_automatic_publication": True,
            "suggestions_table_only": "territorial_enrichment_suggestions",
            "official_tables_read_only": [
                "territorial_profiles",
                "knowledge",
                "localites",
                "territoires",
                "provinces",
                "collectivites",
                "groupements",
            ],
        },
    }


def read_demo_enrichment_cache() -> dict[str, Any]:
    if not DEMO_ENRICHMENT_CACHE.exists():
        return {
            "demo_enrichment_mode": False,
            "generated_at": None,
            "status": "cache absent",
            "entities": [],
        }
    with DEMO_ENRICHMENT_CACHE.open("r", encoding="utf-8") as handle:
        return json.load(handle)
