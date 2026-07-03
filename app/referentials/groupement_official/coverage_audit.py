from __future__ import annotations

import json
import re
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


EXPECTED_NATIONAL_GROUPEMENTS = 6053


class GroupementCoverageAudit:
    def run(
        self,
        groupement_referential_path: str | Path = Path("data/reports/groupement_official/groupement_referential_official.json"),
        groupement_quality_path: str | Path = Path("data/reports/groupement_official/groupement_quality_report.json"),
        collectivity_referential_path: str | Path = Path("data/reports/collectivity_official/collectivity_referential_official.json"),
        territory_index_path: str | Path = Path("data/reports/collectivity_official/territory_collectivity_index.json"),
        province_referential_path: str | Path = Path("data/reports/province_official/province_referential_official.json"),
        output_dir: str | Path = Path("data/reports/groupement_official"),
    ) -> dict[str, Path]:
        groupement_report = self._read_json(groupement_referential_path)
        quality_report = self._read_json(groupement_quality_path)
        collectivity_report = self._read_json(collectivity_referential_path)
        territory_index = self._read_json(territory_index_path)
        province_report = self._read_json(province_referential_path)

        groupements = groupement_report.get("groupement_referential", [])
        collectivities = collectivity_report.get("collectivity_referential", [])
        official_provinces = [item["nom"] for item in province_report.get("province_referential", []) if item.get("nom")]
        official_territories = [
            item
            for item in territory_index.get("territories", [])
            if item.get("territoire") and item.get("province")
        ]

        audit = self._build_audit(
            groupements=groupements,
            collectivities=collectivities,
            official_provinces=official_provinces,
            official_territories=official_territories,
            quality_report=quality_report,
        )

        output = Path(output_dir)
        output.mkdir(parents=True, exist_ok=True)
        json_path = output / "groupement_coverage_audit.json"
        markdown_path = output / "groupement_coverage_audit.md"
        json_path.write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding="utf-8")
        markdown_path.write_text(self._to_markdown(audit), encoding="utf-8")
        self._update_national_registry(audit, output.parent / "national_counter_registry.json")
        return {"json": json_path, "markdown": markdown_path}

    def _build_audit(
        self,
        groupements: list[dict[str, Any]],
        collectivities: list[dict[str, Any]],
        official_provinces: list[str],
        official_territories: list[dict[str, Any]],
        quality_report: dict[str, Any],
    ) -> dict[str, Any]:
        province_counts = Counter(item.get("province") or "NON_DETERMINEE" for item in groupements)
        territory_counts = Counter(
            self._territory_key(item.get("province", ""), item.get("territoire", ""))
            for item in groupements
        )
        collectivity_counts = Counter(
            self._collectivity_key(
                item.get("province", ""),
                item.get("territoire", ""),
                item.get("collectivite_parent", ""),
            )
            for item in groupements
        )

        province_collectivities = defaultdict(set)
        province_covered_collectivities = defaultdict(set)
        for item in collectivities:
            province_collectivities[item.get("province") or "NON_DETERMINEE"].add(
                self._collectivity_key(item.get("province", ""), item.get("territoire", ""), item.get("nom", ""))
            )
        for item in groupements:
            if item.get("collectivite_parent"):
                province_covered_collectivities[item.get("province") or "NON_DETERMINEE"].add(
                    self._collectivity_key(item.get("province", ""), item.get("territoire", ""), item.get("collectivite_parent", ""))
                )

        territories_without_groupement = []
        for item in official_territories:
            key = self._territory_key(item.get("province", ""), item.get("territoire", ""))
            if territory_counts.get(key, 0) == 0:
                territories_without_groupement.append(
                    {
                        "province": item.get("province", ""),
                        "territoire": item.get("territoire", ""),
                        "zone_fdsu": item.get("zone_fdsu", ""),
                        "nombre_collectivites": item.get("nombre_collectivites", 0),
                    }
                )

        collectivities_without_groupement = []
        for item in collectivities:
            key = self._collectivity_key(item.get("province", ""), item.get("territoire", ""), item.get("nom", ""))
            if collectivity_counts.get(key, 0) == 0:
                collectivities_without_groupement.append(
                    {
                        "nom": item.get("nom", ""),
                        "type_collectivite": item.get("type_collectivite", ""),
                        "province": item.get("province", ""),
                        "territoire": item.get("territoire", ""),
                        "zone_fdsu": item.get("zone_fdsu", ""),
                        "code_officiel": item.get("code_officiel"),
                    }
                )

        orphan = next((item for item in groupements if not item.get("collectivite_parent")), None)
        orphan_audit = self._build_orphan_audit(orphan)
        inconsistency_summary = self._summarize_inconsistencies(quality_report.get("anomalies", []))

        official_found = len(groupements)
        expected_gap = EXPECTED_NATIONAL_GROUPEMENTS - official_found
        coverage_ratio = round((official_found / EXPECTED_NATIONAL_GROUPEMENTS) * 100, 2)

        province_distribution = self._province_distribution(
            official_provinces=official_provinces,
            province_counts=province_counts,
            province_collectivities=province_collectivities,
            province_covered_collectivities=province_covered_collectivities,
        )
        official_province_set = set(official_provinces)
        official_province_distribution = [
            item for item in province_distribution if item["province"] in official_province_set
        ]
        well_covered = [
            item["province"]
            for item in official_province_distribution
            if item["groupements"] >= 50 and item["collectivity_coverage_percent"] >= 75.0
        ]
        absent = [item["province"] for item in official_province_distribution if item["groupements"] == 0]
        weak = [
            item["province"]
            for item in official_province_distribution
            if item["groupements"] > 0 and (item["groupements"] < 25 or item["collectivity_coverage_percent"] < 50.0)
        ]

        conclusion = {
            "coverage_status": "partiel",
            "validation_recommendation": "marquer comme partiel, ne pas valider provisoirement comme référentiel national complet",
            "reason": (
                f"Le fichier couvre {coverage_ratio}% de la référence nationale officielle "
                f"({official_found}/{EXPECTED_NATIONAL_GROUPEMENTS}); l'écart est de {expected_gap} groupements."
            ),
            "well_covered_provinces": well_covered,
            "absent_provinces": absent,
            "weak_provinces": weak,
        }

        return {
            "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "source": "data/raw/Groupements.kmz",
            "national_reference": {
                "expected_groupements": EXPECTED_NATIONAL_GROUPEMENTS,
                "found_groupements": official_found,
                "gap": expected_gap,
                "coverage_percent": coverage_ratio,
            },
            "quality_snapshot": {
                "attached_count": quality_report.get("attached_count", 0),
                "orphan_count": quality_report.get("orphan_count", 0),
                "anomaly_count": len(quality_report.get("anomalies", [])),
                "global_score": quality_report.get("global_score", 0),
            },
            "distribution_by_province": province_distribution,
            "distribution_by_territory": self._territory_distribution(territory_counts),
            "distribution_by_collectivity": self._collectivity_distribution(collectivity_counts, collectivities),
            "territories_without_groupement": sorted(
                territories_without_groupement,
                key=lambda item: (item["province"], item["territoire"]),
            ),
            "collectivities_without_groupement": sorted(
                collectivities_without_groupement,
                key=lambda item: (item["province"], item["territoire"], item["nom"]),
            ),
            "orphan_groupement": orphan_audit,
            "attribute_inconsistency_summary": inconsistency_summary,
            "conclusion": conclusion,
        }

    def _province_distribution(
        self,
        official_provinces: list[str],
        province_counts: Counter,
        province_collectivities: dict[str, set[str]],
        province_covered_collectivities: dict[str, set[str]],
    ) -> list[dict[str, Any]]:
        rows = []
        for province in sorted(set(official_provinces) | set(province_counts.keys())):
            count = province_counts.get(province, 0)
            total_collectivities = len(province_collectivities.get(province, set()))
            covered_collectivities = len(province_covered_collectivities.get(province, set()))
            percent = round((covered_collectivities / total_collectivities) * 100, 2) if total_collectivities else 0.0
            rows.append(
                {
                    "province": province,
                    "groupements": count,
                    "collectivites_total": total_collectivities,
                    "collectivites_avec_groupements": covered_collectivities,
                    "collectivity_coverage_percent": percent,
                }
            )
        return sorted(rows, key=lambda item: (-item["groupements"], item["province"]))

    def _territory_distribution(self, territory_counts: Counter) -> list[dict[str, Any]]:
        rows = []
        for key, count in territory_counts.items():
            province, territory = key.split("|", 1)
            rows.append({"province": province, "territoire": territory, "groupements": count})
        return sorted(rows, key=lambda item: (item["province"], item["territoire"]))

    def _collectivity_distribution(
        self,
        collectivity_counts: Counter,
        collectivities: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        collectivity_meta = {
            self._collectivity_key(item.get("province", ""), item.get("territoire", ""), item.get("nom", "")): item
            for item in collectivities
        }
        rows = []
        for key, count in collectivity_counts.items():
            province, territory, collectivity = key.split("|", 2)
            meta = collectivity_meta.get(key, {})
            rows.append(
                {
                    "province": province,
                    "territoire": territory,
                    "collectivite": collectivity,
                    "type_collectivite": meta.get("type_collectivite", ""),
                    "code_officiel": meta.get("code_officiel"),
                    "groupements": count,
                }
            )
        return sorted(rows, key=lambda item: (item["province"], item["territoire"], item["collectivite"]))

    def _build_orphan_audit(self, orphan: dict[str, Any] | None) -> dict[str, Any] | None:
        if orphan is None:
            return None
        metadata = orphan.get("metadata", {})
        extended_data = metadata.get("extended_data", {})
        return {
            "nom": orphan.get("nom", ""),
            "code_officiel": orphan.get("code_officiel"),
            "source_collectivite": metadata.get("source_collectivite", ""),
            "source_territoire": metadata.get("source_territoire", ""),
            "attributes": extended_data,
            "geometry": orphan.get("geometry"),
            "cause_probable": (
                "Le préfixe de CODE_GRPT ne correspond à aucune collectivité officielle générée, "
                "et le couple COLLECTIV/TERRITOIRE source ne permet pas de rattachement fiable."
            ),
        }

    def _summarize_inconsistencies(self, anomalies: list[dict[str, Any]]) -> dict[str, Any]:
        inconsistency_anomalies = [item for item in anomalies if item.get("probleme") == "incoherence attributaire"]
        by_field = Counter()
        by_pair = Counter()
        examples = []
        pattern = re.compile(r"^(COLLECTIV|TERRITOIRE)='([^']*)' different .* '([^']*)'$")

        for item in inconsistency_anomalies:
            cause = item.get("cause", "")
            match = pattern.match(cause)
            if match:
                field, source_value, parent_value = match.groups()
                by_field[field] += 1
                by_pair[f"{field}: {source_value} -> {parent_value}"] += 1
            else:
                by_field["AUTRE"] += 1
            if len(examples) < 20:
                examples.append(item)

        return {
            "total": len(inconsistency_anomalies),
            "by_field": dict(sorted(by_field.items())),
            "top_mismatch_pairs": [
                {"mismatch": key, "count": count}
                for key, count in by_pair.most_common(25)
            ],
            "examples": examples,
        }

    def _to_markdown(self, audit: dict[str, Any]) -> str:
        ref = audit["national_reference"]
        q = audit["quality_snapshot"]
        conclusion = audit["conclusion"]
        lines = [
            "# Audit Couverture Groupements",
            "",
            f"- Source: {audit['source']}",
            f"- Date: {audit['generated_at']}",
            f"- Référence nationale attendue: {ref['expected_groupements']}",
            f"- Trouvé: {ref['found_groupements']}",
            f"- Écart: {ref['gap']}",
            f"- Couverture nationale: {ref['coverage_percent']}%",
            f"- Rattachés: {q['attached_count']}",
            f"- Orphelins: {q['orphan_count']}",
            f"- Anomalies: {q['anomaly_count']}",
            f"- Score qualité technique: {q['global_score']}",
            "",
            "## Conclusion",
            "",
            f"- Statut de couverture: {conclusion['coverage_status']}",
            f"- Recommandation: {conclusion['validation_recommendation']}",
            f"- Justification: {conclusion['reason']}",
            f"- Provinces bien couvertes: {', '.join(conclusion['well_covered_provinces']) or 'Aucune'}",
            f"- Provinces absentes: {', '.join(conclusion['absent_provinces']) or 'Aucune'}",
            f"- Provinces faibles: {', '.join(conclusion['weak_provinces']) or 'Aucune'}",
            "",
            "## Répartition par province",
            "",
            "| Province | Groupements | Collectivités | Collectivités couvertes | Couverture collectivités |",
            "|---|---:|---:|---:|---:|",
        ]
        for item in audit["distribution_by_province"]:
            lines.append(
                f"| {item['province']} | {item['groupements']} | {item['collectivites_total']} | "
                f"{item['collectivites_avec_groupements']} | {item['collectivity_coverage_percent']}% |"
            )

        lines.extend(["", "## Territoires sans groupement", ""])
        lines.append(f"Total: {len(audit['territories_without_groupement'])}")
        lines.extend(["", "| Province | Territoire | Zone | Collectivités |", "|---|---|---|---:|"])
        for item in audit["territories_without_groupement"]:
            lines.append(f"| {item['province']} | {item['territoire']} | {item['zone_fdsu']} | {item['nombre_collectivites']} |")

        lines.extend(["", "## Collectivités sans groupement", ""])
        lines.append(f"Total: {len(audit['collectivities_without_groupement'])}")
        lines.extend(["", "| Province | Territoire | Collectivité | Type | Code |", "|---|---|---|---|---|"])
        for item in audit["collectivities_without_groupement"][:250]:
            lines.append(
                f"| {item['province']} | {item['territoire']} | {item['nom']} | "
                f"{item['type_collectivite']} | {item['code_officiel'] or ''} |"
            )
        if len(audit["collectivities_without_groupement"]) > 250:
            lines.append(f"| ... | ... | {len(audit['collectivities_without_groupement']) - 250} autres dans le JSON complet | ... | ... |")

        lines.extend(["", "## Orphelin détecté", ""])
        orphan = audit["orphan_groupement"]
        if orphan:
            lines.extend(
                [
                    f"- Nom: {orphan['nom']}",
                    f"- Code: {orphan['code_officiel']}",
                    f"- Collectivité source: {orphan['source_collectivite']}",
                    f"- Territoire source: {orphan['source_territoire']}",
                    f"- Géométrie: {orphan['geometry']}",
                    f"- Cause probable: {orphan['cause_probable']}",
                ]
            )
        else:
            lines.append("Aucun orphelin détecté.")

        inc = audit["attribute_inconsistency_summary"]
        lines.extend(
            [
                "",
                "## Incohérences attributaires",
                "",
                f"- Total: {inc['total']}",
                f"- Par champ: {json.dumps(inc['by_field'], ensure_ascii=False)}",
                "",
                "| Incohérence fréquente | Nombre |",
                "|---|---:|",
            ]
        )
        for item in inc["top_mismatch_pairs"][:20]:
            lines.append(f"| {item['mismatch']} | {item['count']} |")

        lines.extend(["", "## Répartition par territoire", ""])
        lines.extend(["| Province | Territoire | Groupements |", "|---|---|---:|"])
        for item in audit["distribution_by_territory"]:
            lines.append(f"| {item['province']} | {item['territoire']} | {item['groupements']} |")

        lines.extend(["", "## Répartition par collectivité", ""])
        lines.extend(["| Province | Territoire | Collectivité | Type | Groupements |", "|---|---|---|---|---:|"])
        for item in audit["distribution_by_collectivity"]:
            lines.append(
                f"| {item['province']} | {item['territoire']} | {item['collectivite']} | "
                f"{item['type_collectivite']} | {item['groupements']} |"
            )
        return "\n".join(lines)

    def _update_national_registry(self, audit: dict[str, Any], path: Path) -> None:
        if path.exists():
            registry = self._read_json(path)
        else:
            registry = {"registre_national_des_compteurs": {}}
        counters = registry.setdefault("registre_national_des_compteurs", {})
        ref = audit["national_reference"]
        q = audit["quality_snapshot"]
        counters["groupements"] = {
            "attendu_officiel": ref["expected_groupements"],
            "trouve": ref["found_groupements"],
            "couverture": f"{ref['coverage_percent']}%",
            "statut": "partiel",
            "validation": "non publié",
            "anomalies": q["anomaly_count"],
            "orphelins": q["orphan_count"],
            "territoires_sans_groupement": len(audit["territories_without_groupement"]),
            "collectivites_sans_groupement": len(audit["collectivities_without_groupement"]),
            "recommandation": "source partielle, à compléter avec une autre source avant validation nationale",
        }
        counters["anomalies_groupements"] = {
            "nombre": q["anomaly_count"],
            "orphelins": q["orphan_count"],
            "incoherences_attributaires": audit["attribute_inconsistency_summary"]["total"],
        }
        registry["generated_at"] = audit["generated_at"]
        registry["source_groupements"] = "Groupements.kmz"
        path.write_text(json.dumps(registry, ensure_ascii=False, indent=2), encoding="utf-8")

    def _territory_key(self, province: str, territory: str) -> str:
        return f"{province or 'NON_DETERMINEE'}|{territory or 'NON_DETERMINE'}"

    def _collectivity_key(self, province: str, territory: str, collectivity: str) -> str:
        return f"{province or 'NON_DETERMINEE'}|{territory or 'NON_DETERMINE'}|{collectivity or 'NON_DETERMINEE'}"

    def _read_json(self, path: str | Path) -> dict[str, Any]:
        return json.loads(Path(path).read_text(encoding="utf-8"))

    def _normalize_key(self, value: str) -> str:
        normalized = unicodedata.normalize("NFKD", value or "")
        ascii_text = "".join(ch for ch in normalized if not unicodedata.combining(ch))
        ascii_text = ascii_text.replace("-", " ").replace("_", " ")
        return re.sub(r"\s+", " ", ascii_text).strip().upper()


def main() -> None:
    result = GroupementCoverageAudit().run()
    print("Audit couverture Groupements généré")
    print(f"JSON: {result['json']}")
    print(f"Markdown: {result['markdown']}")


if __name__ == "__main__":
    main()
