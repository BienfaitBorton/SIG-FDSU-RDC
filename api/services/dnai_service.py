"""DNAI v2.0 — normalisation institutionnelle explicable et gouvernée."""

from __future__ import annotations

import json
import re
import unicodedata
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[2]
DICTIONARY_PATH = ROOT / "data" / "business" / "dnai_dictionary_v1.json"
CENI_REGISTRY_PATH = ROOT / "data" / "reports" / "ceni_official" / "ceni_registry_v1.json"
TECHNICAL_ID_RE = re.compile(r"^(?:CENI|REF|CODE|FDSU|ID|UID)[\s._/-]*(?:EP|INST|IT|ISP|ISTM|ISDR|ISC|ISAM|ISIPA)?[\s._/-]*\d+$", re.I)
EP_NUMBER_RE = re.compile(r"^E\s*\.?\s*P\s*\.?(?:\s*(?:N\s*[°º]?|NO)\s*)?[- ]*0*([1-9]\d*)(?=\s|[.,;/\-]|$)", re.I)
UNKNOWN_SIGLE_RE = re.compile(r"(?<![A-Z0-9])([A-Z]{2,8})(?![A-Z0-9])")
HEALTH_CONTEXT = ("SANTE", "SANITAIRE", "CLINIQUE", "MATERNITE", "DISPENSAIRE", "HOPITAL", "HGR", "CSR", "CENTRE HOSPITALIER", "CENTRE MEDICAL", "POSTE DE SANTE")


def _ascii(value: str) -> str:
    text = unicodedata.normalize("NFKD", value)
    return "".join(ch for ch in text if not unicodedata.combining(ch)).upper()


def _clean(value: str) -> str:
    text = _ascii(value).replace("’", " ").replace("'", " ")
    text = re.sub(r"[\\/_]+", " ", text)
    text = re.sub(r"(?<=\b[A-Z])\.(?=[A-Z]\b|\s|\d|$)", "", text)
    return re.sub(r"[^A-Z0-9]+", " ", text).strip()


@dataclass(frozen=True, slots=True)
class DNAIResult:
    original_text: str
    cleaned_text: str
    normalized_text: str
    technical_identifier: bool
    rule_id: str | None
    regex: str | None
    expansion: str | None
    context: str
    category: str | None
    family: str | None
    confidence: float
    justification: str
    status: str
    matches: tuple[dict[str, Any], ...]

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


class DNAIService:
    def __init__(self, dictionary_path: Path = DICTIONARY_PATH) -> None:
        self.dictionary_path = Path(dictionary_path)
        self.dictionary = json.loads(self.dictionary_path.read_text(encoding="utf-8"))
        self.entries = self.dictionary["entries"]

    def _result(self, original: str, cleaned: str, normalized: str, **kwargs: Any) -> DNAIResult:
        return DNAIResult(original_text=original, cleaned_text=cleaned, normalized_text=normalized, **kwargs)

    def normalize(self, text: str, referential: str = "national") -> DNAIResult:
        original = str(text or "").strip()
        cleaned = _clean(original)
        compact_id = re.sub(r"[\s._/-]+", "-", _ascii(original)).strip("-")
        if TECHNICAL_ID_RE.fullmatch(compact_id):
            return self._result(original, cleaned, cleaned, technical_identifier=True, rule_id="TECHNICAL_IDENTIFIER", regex=TECHNICAL_ID_RE.pattern, expansion=None, context=referential, category=None, family=None, confidence=1.0, justification="Le libellé correspond à un identifiant technique; aucune expansion institutionnelle n’est autorisée.", status="Non classifié", matches=())

        ep = EP_NUMBER_RE.match(_ascii(original))
        if ep:
            number = str(int(ep.group(1)))
            remainder = _clean(original[ep.end():])
            normalized = f"ÉCOLE PRIMAIRE {number}" + (f" {remainder}" if remainder else "")
            entry = self._by_id("DNAI-EDU-EP")
            match = self._match(entry, "EP + numéro", f"ÉCOLE PRIMAIRE {number}", EP_NUMBER_RE.pattern)
            return self._result(original, cleaned, normalized, technical_identifier=False, rule_id=entry["id"], regex=EP_NUMBER_RE.pattern, expansion=match["expansion"], context=referential, category=entry["category"], family=entry["family"], confidence=entry["confidence"], justification=f"Forme scolaire compacte ou numérotée reconnue en tête de libellé; numéro canonique {number} conservé.", status="Certain", matches=(match,))

        normalized = cleaned
        matches: list[dict[str, Any]] = []
        # CS appartient au DNAI : CENI privilégie l'école, sauf indice sanitaire explicite.
        if re.match(r"^CS(?:\s|$)", cleaned) and referential.upper() == "CENI":
            is_health = any(re.search(rf"(?:^|\s){re.escape(term)}(?:\s|$)", cleaned) for term in HEALTH_CONTEXT)
            expansion = "CENTRE DE SANTÉ" if is_health else "COMPLEXE SCOLAIRE"
            if is_health and re.match(r"^CS\s+(?:DE\s+)?SANTE(?:\s|$)", cleaned):
                normalized = re.sub(r"^CS\s+(?:DE\s+)?SANTE(?=\s|$)", expansion, cleaned, count=1)
            else:
                normalized = re.sub(r"^CS(?=\s|$)", expansion, cleaned, count=1)
            entry = self._by_id("DNAI-EDU-CS")
            matches.append(self._match(entry, "CS", expansion, r"^CS(?:\s|$)"))
            confidence = .98 if is_health else entry["confidence"]
            return self._result(original, cleaned, normalized, technical_identifier=False, rule_id="DNAI-CS-CONTEXT", regex=r"^CS(?:\s|$)", expansion=expansion, context=f"{referential}: {'sanitaire' if is_health else 'scolaire'}", category="health" if is_health else "education", family="Santé" if is_health else "Éducation", confidence=confidence, justification="L’abréviation CS est résolue par la priorité du référentiel CENI et les indices sanitaires explicites.", status="Certain" if is_health else "Probable", matches=tuple(matches))

        ordered = sorted(self.entries, key=lambda item: (item.get("referential_priority", {}).get(referential.upper(), 0), len(item["abbreviation"])), reverse=True)
        for entry in ordered:
            aliases = [entry["abbreviation"], *entry.get("variants", []), *entry.get("synonyms", [])]
            for alias in sorted(aliases, key=len, reverse=True):
                token = _clean(alias)
                pattern = rf"^{re.escape(token)}(?=\s|$)"
                if re.search(pattern, normalized):
                    normalized = re.sub(pattern, entry["official_expansion"], normalized, count=1)
                    matches.append(self._match(entry, alias, entry["official_expansion"], pattern))
                    return self._result(original, cleaned, normalized, technical_identifier=False, rule_id=entry["id"], regex=pattern, expansion=entry["official_expansion"], context=referential, category=entry["category"], family=entry["family"], confidence=float(entry["confidence"]), justification=f"La variante institutionnelle « {alias} » est publiée dans le DNAI {self.dictionary['version']}.", status="Certain" if float(entry["confidence"]) >= .95 else "Probable", matches=tuple(matches))

        pending = next((p for p in self.dictionary.get("pending_validations", []) if re.search(rf"(?:^|\s){re.escape(p['abbreviation'])}(?:\s|$)", cleaned)), None)
        if pending:
            return self._result(original, cleaned, cleaned, technical_identifier=False, rule_id=None, regex=None, expansion=None, context=referential, category=None, family=None, confidence=0.0, justification=pending["reason"], status="À vérifier", matches=())
        return self._result(original, cleaned, cleaned, technical_identifier=False, rule_id=None, regex=None, expansion=None, context=referential, category=None, family=None, confidence=0.0, justification="Aucune entrée DNAI publiée ne correspond au libellé.", status="Non reconnu", matches=())

    def _by_id(self, entry_id: str) -> dict[str, Any]:
        return next(item for item in self.entries if item["id"] == entry_id)

    @staticmethod
    def _match(entry: dict[str, Any], motif: str, expansion: str, regex: str) -> dict[str, Any]:
        return {"entry_id": entry["id"], "motif": motif, "regex": regex, "expansion": expansion, "category": entry["category"], "confidence": entry["confidence"]}

    def search(self, query: str = "", family: str | None = None) -> list[dict[str, Any]]:
        needle = _ascii(query).strip()
        return [item for item in self.entries if (not family or _ascii(item["family"]) == _ascii(family)) and (not needle or needle in _ascii(json.dumps(item, ensure_ascii=False)))]

    def expand(self, abbreviation: str, referential: str = "national") -> DNAIResult:
        return self.normalize(abbreviation, referential)

    def statistics(self) -> dict[str, Any]:
        variants = sum(len(e.get("variants", [])) + len(e.get("synonyms", [])) + 1 for e in self.entries)
        return {"version": self.dictionary["version"], "abbreviations": len(self.entries), "recognized_variants": variants, "families": dict(Counter(e["family"] for e in self.entries)), "ambiguities": len(self.dictionary.get("pending_validations", [])), "referential_coverage": dict(Counter(r for e in self.entries for r in e["referentials"]))}

    def pending_validations(self) -> list[dict[str, Any]]:
        return self.dictionary.get("pending_validations", [])

    def discover(self, labels: Iterable[str], referential: str = "CENI") -> dict[str, Any]:
        known = {_clean(v) for e in self.entries for v in [e["abbreviation"], *e.get("variants", []), *e.get("synonyms", [])]}
        pending = {p["abbreviation"] for p in self.pending_validations()}
        counts: Counter[str] = Counter()
        contexts: defaultdict[str, list[str]] = defaultdict(list)
        for label in labels:
            cleaned = _clean(label)
            for sigle in UNKNOWN_SIGLE_RE.findall(cleaned):
                if sigle in known or sigle in {"DE", "DU", "LA", "LE", "ET"}: continue
                counts[sigle] += 1
                if len(contexts[sigle]) < 5 and label not in contexts[sigle]: contexts[sigle].append(label)
        return {"referential": referential, "discoveries": [{"abbreviation": key, "occurrences": value, "contexts": contexts[key], "expansion": None, "status": "À vérifier", "already_pending": key in pending} for key, value in counts.most_common()]}

    def discover_ceni(self) -> dict[str, Any]:
        if not CENI_REGISTRY_PATH.exists(): return {"referential": "CENI", "discoveries": [], "warning": "Registre CENI indisponible."}
        rows = json.loads(CENI_REGISTRY_PATH.read_text(encoding="utf-8")).get("assets", [])
        return self.discover((row.get("name", "") for row in rows), "CENI")


@lru_cache(maxsize=1)
def default_dnai() -> DNAIService:
    return DNAIService()
