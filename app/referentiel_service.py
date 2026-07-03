"""
Services pour le référentiel administratif FDSU.
- Recherches par nom et par code
- Recherches hiérarchiques (enfants d'une entité)
- Statistiques d'import et lecture de l'historique

Conçu pour être utilisé depuis des scripts ou des routes existantes sans modifier l'API.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Iterable, List

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.models import (
    CollectiviteType,
    Province,
    Territoire,
    Collectivite,
    Groupement,
    Village,
    ImportHistory,
)
from app.referentials.quality import QualityService


# Recherche par nom (recherche approximative, sensible à la casse DB)
def search_provinces_by_name(session: Session, name: str, limit: int = 50) -> List[Province]:
    pattern = f"%{name}%"
    stmt = select(Province).where(Province.nom.ilike(pattern)).limit(limit)
    return session.execute(stmt).scalars().all()


def search_territoires_by_name(session: Session, name: str, province_code: str | None = None, limit: int = 50) -> List[Territoire]:
    pattern = f"%{name}%"
    stmt = select(Territoire).where(Territoire.nom.ilike(pattern))
    if province_code:
        stmt = stmt.join(Province).where(Province.code == province_code.upper())
    stmt = stmt.limit(limit)
    return session.execute(stmt).scalars().all()


def search_collectivites_by_name(session: Session, name: str, territoire_code: str | None = None, limit: int = 50) -> List[Collectivite]:
    pattern = f"%{name}%"
    stmt = select(Collectivite).where(Collectivite.nom.ilike(pattern))
    if territoire_code:
        stmt = stmt.join(Territoire).where(Territoire.code == territoire_code.upper())
    stmt = stmt.limit(limit)
    return session.execute(stmt).scalars().all()


def search_groupements_by_name(session: Session, name: str, collectivite_code: str | None = None, limit: int = 50) -> List[Groupement]:
    pattern = f"%{name}%"
    stmt = select(Groupement).where(Groupement.nom.ilike(pattern))
    if collectivite_code:
        stmt = stmt.join(Collectivite).where(Collectivite.code == collectivite_code.upper())
    stmt = stmt.limit(limit)
    return session.execute(stmt).scalars().all()


def search_villages_by_name(session: Session, name: str, groupement_code: str | None = None, limit: int = 50) -> List[Village]:
    pattern = f"%{name}%"
    stmt = select(Village).where(Village.nom.ilike(pattern))
    if groupement_code:
        stmt = stmt.join(Groupement).where(Groupement.code == groupement_code.upper())
    stmt = stmt.limit(limit)
    return session.execute(stmt).scalars().all()


# Recherche par code (recherche exacte)
def get_province_by_code(session: Session, code: str) -> Province | None:
    return session.scalar(select(Province).where(Province.code == code.upper()))


def get_territoire_by_code(session: Session, code: str, province_code: str | None = None) -> Territoire | None:
    stmt = select(Territoire).where(Territoire.code == code)
    if province_code:
        stmt = stmt.join(Province).where(Province.code == province_code.upper())
    return session.scalar(stmt)


def get_collectivite_by_code(session: Session, code: str, territoire_code: str | None = None) -> Collectivite | None:
    stmt = select(Collectivite).where(Collectivite.code == code)
    if territoire_code:
        stmt = stmt.join(Territoire).where(Territoire.code == territoire_code.upper())
    return session.scalar(stmt)


def get_groupement_by_code(session: Session, code: str, collectivite_code: str | None = None) -> Groupement | None:
    stmt = select(Groupement).where(Groupement.code == code)
    if collectivite_code:
        stmt = stmt.join(Collectivite).where(Collectivite.code == collectivite_code.upper())
    return session.scalar(stmt)


def get_village_by_code(session: Session, code: str, groupement_code: str | None = None) -> Village | None:
    stmt = select(Village).where(Village.code == code)
    if groupement_code:
        stmt = stmt.join(Groupement).where(Groupement.code == groupement_code.upper())
    return session.scalar(stmt)


# Recherches hiérarchiques (enfants)
def territoires_by_province_code(session: Session, province_code: str) -> List[Territoire]:
    stmt = select(Territoire).join(Province).where(Province.code == province_code.upper()).order_by(Territoire.nom)
    return session.execute(stmt).scalars().all()


def collectivites_by_territoire_code(session: Session, territoire_code: str) -> List[Collectivite]:
    stmt = select(Collectivite).join(Territoire).where(Territoire.code == territoire_code.upper()).order_by(Collectivite.nom)
    return session.execute(stmt).scalars().all()


def groupements_by_collectivite_code(session: Session, collectivite_code: str) -> List[Groupement]:
    stmt = select(Groupement).join(Collectivite).where(Collectivite.code == collectivite_code.upper()).order_by(Groupement.nom)
    return session.execute(stmt).scalars().all()


def villages_by_groupement_code(session: Session, groupement_code: str) -> List[Village]:
    stmt = select(Village).join(Groupement).where(Groupement.code == groupement_code.upper()).order_by(Village.nom)
    return session.execute(stmt).scalars().all()


# Récupérer la hiérarchie complète pour un village (par id)
def hierarchy_for_village(session: Session, village_id: int) -> dict:
    village = session.get(Village, village_id)
    if village is None:
        return {}
    groupement = village.groupement
    collectivite = groupement.collectivite if groupement is not None else None
    territoire = collectivite.territoire if collectivite is not None else None
    province = territoire.province if territoire is not None else None
    return {
        "province": province,
        "territoire": territoire,
        "collectivite": collectivite,
        "groupement": groupement,
        "village": village,
    }


# Statistiques et historique d'import
def recent_imports(session: Session, limit: int = 50) -> List[ImportHistory]:
    stmt = select(ImportHistory).order_by(ImportHistory.imported_at.desc()).limit(limit)
    return session.execute(stmt).scalars().all()


def import_aggregates(session: Session, days: int | None = None) -> dict:
    stmt = select(
        func.count(ImportHistory.id),
        func.sum(ImportHistory.rows_inserted),
        func.sum(ImportHistory.rows_updated),
        func.sum(ImportHistory.rows_rejected),
    )
    if days is not None:
        since = datetime.utcnow() - timedelta(days=days)
        stmt = stmt.where(ImportHistory.imported_at >= since)
    row = session.execute(stmt).one()
    return {
        "imports_count": int(row[0] or 0),
        "rows_inserted": int(row[1] or 0),
        "rows_updated": int(row[2] or 0),
        "rows_rejected": int(row[3] or 0),
    }


@dataclass(slots=True)
class AdministrativeTreeNode:
    level: str
    label: str
    code: str | None = None
    count: int = 0
    children: list["AdministrativeTreeNode"] = field(default_factory=list)
    anomalies: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "level": self.level,
            "label": self.label,
            "code": self.code,
            "count": self.count,
            "children": [child.to_dict() for child in self.children],
            "anomalies": list(self.anomalies),
        }


@dataclass(slots=True)
class AdministrativeAnomaly:
    level: str
    entity: str
    message: str
    severity: str = "warning"
    code: str | None = None
    parent: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "level": self.level,
            "entity": self.entity,
            "message": self.message,
            "severity": self.severity,
            "code": self.code,
            "parent": self.parent,
        }


@dataclass(slots=True)
class AdministrativeReferentialReport:
    root: AdministrativeTreeNode
    statistics: dict[str, Any]
    anomalies: list[AdministrativeAnomaly]
    quality: dict[str, Any]
    compatibility: dict[str, Any]
    markdown: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "root": self.root.to_dict(),
            "statistics": dict(self.statistics),
            "anomalies": [anomaly.to_dict() for anomaly in self.anomalies],
            "quality": dict(self.quality),
            "compatibility": dict(self.compatibility),
            "markdown": self.markdown,
        }


def build_administrative_referential_report(
    session: Session,
    staging_entities: Iterable[Any] | None = None,
) -> AdministrativeReferentialReport:
    provinces = session.execute(select(Province).order_by(Province.zone, Province.nom)).scalars().all()
    territoires = session.execute(select(Territoire).order_by(Territoire.nom)).scalars().all()
    collectivites = session.execute(select(Collectivite).order_by(Collectivite.nom)).scalars().all()
    groupements = session.execute(select(Groupement).order_by(Groupement.nom)).scalars().all()
    villages = session.execute(select(Village).order_by(Village.nom)).scalars().all()

    anomalies: list[AdministrativeAnomaly] = []
    level_counts: dict[str, int] = {
        "rdc": 1,
        "zone_fdsu": 0,
        "province": len(provinces),
        "territoire": len(territoires),
        "secteur": 0,
        "chefferie": 0,
        "cite": 0,
        "groupement": len(groupements),
        "village": len(villages),
    }
    type_counts = Counter()
    zone_counts = Counter()

    root = AdministrativeTreeNode(level="rdc", label="RDC", count=1)
    zone_nodes: dict[str, AdministrativeTreeNode] = {}
    province_nodes: dict[int, AdministrativeTreeNode] = {}
    territoire_nodes: dict[int, AdministrativeTreeNode] = {}

    for province in provinces:
        zone_code = (province.zone or "INCONNU").upper()
        zone_node = zone_nodes.get(zone_code)
        if zone_node is None:
            zone_node = AdministrativeTreeNode(level="zone_fdsu", label=f"Zone FDSU {zone_code}", code=zone_code)
            zone_nodes[zone_code] = zone_node
            root.children.append(zone_node)
        zone_node.count += 1
        zone_counts[zone_code] += 1

        if not province.zone:
            anomalies.append(
                AdministrativeAnomaly(
                    level="province",
                    entity=province.nom,
                    code=province.code,
                    message="Province sans zone FDSU renseignée.",
                    severity="error",
                )
            )

        province_node = AdministrativeTreeNode(level="province", label=province.nom, code=province.code)
        zone_node.children.append(province_node)
        province_nodes[province.id] = province_node

    for territoire in territoires:
        province_node = province_nodes.get(territoire.province_id)
        if province_node is None:
            anomalies.append(
                AdministrativeAnomaly(
                    level="territoire",
                    entity=territoire.nom,
                    code=territoire.code,
                    message="Territoire sans province parente exploitable.",
                    severity="error",
                )
            )
            continue

        territoire_node = AdministrativeTreeNode(level="territoire", label=territoire.nom, code=territoire.code)
        province_node.children.append(territoire_node)
        territoire_nodes[territoire.id] = territoire_node

    for collectivite in collectivites:
        territoire_node = territoire_nodes.get(collectivite.territoire_id)
        if territoire_node is None:
            anomalies.append(
                AdministrativeAnomaly(
                    level="collectivite",
                    entity=collectivite.nom,
                    code=collectivite.code,
                    message="Collectivité sans territoire parent exploitable.",
                    severity="error",
                )
            )
            continue

        collectivite_type = collectivite.type_collectivite.value if isinstance(collectivite.type_collectivite, CollectiviteType) else str(collectivite.type_collectivite)
        if collectivite_type not in {item.value for item in CollectiviteType}:
            anomalies.append(
                AdministrativeAnomaly(
                    level="collectivite",
                    entity=collectivite.nom,
                    code=collectivite.code,
                    message=f"Type de collectivité inattendu: {collectivite_type}.",
                    severity="warning",
                )
            )

        if collectivite_type == CollectiviteType.Secteur.value:
            level_counts["secteur"] += 1
        elif collectivite_type == CollectiviteType.Chefferie.value:
            level_counts["chefferie"] += 1
        else:
            level_counts["cite"] += 1

        collectivite_node = AdministrativeTreeNode(level=collectivite_type.lower(), label=collectivite.nom, code=collectivite.code)
        territoire_node.children.append(collectivite_node)

        for groupement in sorted(collectivite.groupements, key=lambda item: (item.nom.lower(), item.code)):
            groupement_node = AdministrativeTreeNode(level="groupement", label=groupement.nom, code=groupement.code)
            collectivite_node.children.append(groupement_node)

            for village in sorted(groupement.villages, key=lambda item: (item.nom.lower(), item.code)):
                village_node = AdministrativeTreeNode(level="village", label=village.nom, code=village.code)
                groupement_node.children.append(village_node)

    level_counts["zone_fdsu"] = len(zone_nodes)

    if staging_entities is not None:
        staging_entities = list(staging_entities)
        compatibility = _build_compatibility_snapshot(staging_entities)
        anomalies.extend(compatibility.pop("anomalies", []))
    else:
        compatibility = {
            "future_levels": {"ville": 0, "commune_urbaine": 0, "commune_rurale": 0, "quartier": 0},
            "anomalies": [],
        }

    duplicate_anomalies = _detect_duplicates(provinces, territoires, collectivites, groupements, villages)
    anomalies.extend(duplicate_anomalies)

    level_counts.update(
        {
            "groupement": len(groupements),
            "village": len(villages),
        }
    )

    total_entities = sum(value for key, value in level_counts.items() if key != "rdc")
    orphan_count = sum(1 for anomaly in anomalies if anomaly.severity == "error")
    inconsistency_count = len(anomalies)
    completeness = 100.0 if total_entities else 0.0
    consistency = max(0.0, round(100.0 - ((inconsistency_count / max(total_entities, 1)) * 100.0), 2))
    coverage = 100.0 if root.children else 0.0
    quality_score = round((completeness * 0.35) + (consistency * 0.45) + (coverage * 0.20), 2)

    quality_service = QualityService()
    quality_report = quality_service.evaluate(
        ["referentiel_administratif_national"],
        metrics={
            "referentiel_administratif_national": {
                "completeness": completeness,
                "consistency": consistency,
                "valid_geometries": 100.0,
                "duplicates": max(0.0, 100.0 - ((len(duplicate_anomalies) / max(total_entities, 1)) * 100.0)),
                "global_quality": quality_score,
                "entity_count": total_entities,
                "orphan_count": orphan_count,
                "issue_count": inconsistency_count,
            }
        },
    )

    statistics = {
        "entity_count": total_entities,
        "by_level": dict(level_counts),
        "by_zone": dict(zone_counts),
        "province_count": len(provinces),
        "territoire_count": len(territoires),
        "collectivite_count": len(collectivites),
        "groupement_count": len(groupements),
        "village_count": len(villages),
        "orphan_count": orphan_count,
        "inconsistency_count": inconsistency_count,
        "quality_score": quality_score,
    }

    markdown = _render_markdown_report(root, statistics, anomalies, compatibility, quality_report)

    return AdministrativeReferentialReport(
        root=root,
        statistics=statistics,
        anomalies=anomalies,
        quality=quality_report.as_dict(),
        compatibility=compatibility,
        markdown=markdown,
    )


def _detect_duplicates(
    provinces: list[Province],
    territoires: list[Territoire],
    collectivites: list[Collectivite],
    groupements: list[Groupement],
    villages: list[Village],
) -> list[AdministrativeAnomaly]:
    anomalies: list[AdministrativeAnomaly] = []

    def check(items: list[Any], level: str, code_attr: str = "code", name_attr: str = "nom") -> None:
        code_counts = Counter(getattr(item, code_attr, None) for item in items if getattr(item, code_attr, None))
        name_counts = Counter(str(getattr(item, name_attr, "")).strip().upper() for item in items if getattr(item, name_attr, None))
        for item in items:
            code = getattr(item, code_attr, None)
            name = getattr(item, name_attr, None)
            if code and code_counts[code] > 1:
                anomalies.append(
                    AdministrativeAnomaly(
                        level=level,
                        entity=str(name or code),
                        code=str(code),
                        message="Code dupliqué dans le référentiel.",
                        severity="error",
                    )
                )
            if name and name_counts[str(name).strip().upper()] > 1:
                anomalies.append(
                    AdministrativeAnomaly(
                        level=level,
                        entity=str(name),
                        code=str(code) if code else None,
                        message="Nom dupliqué dans le référentiel.",
                        severity="warning",
                    )
                )

    check(provinces, "province")
    check(territoires, "territoire")
    check(collectivites, "collectivite")
    check(groupements, "groupement")
    check(villages, "village")
    return anomalies


def _build_compatibility_snapshot(staging_entities: list[Any]) -> dict[str, Any]:
    future_levels = Counter()
    anomalies: list[AdministrativeAnomaly] = []

    for entity in staging_entities:
        entity_type = str(getattr(entity, "entity_type", "") or "").strip().lower()
        if not entity_type:
            continue
        if entity_type in {"ville", "commune_urbaine", "commune_rurale", "quartier", "secteur", "chefferie", "groupement", "groupement_incorpore", "village"}:
            future_levels[entity_type] += 1
        if entity_type in {"ville", "commune_urbaine", "commune_rurale", "quartier"} and not getattr(entity, "parent_source_id", None):
            anomalies.append(
                AdministrativeAnomaly(
                    level=entity_type,
                    entity=str(getattr(entity, "raw_name", getattr(entity, "normalized_name", entity_type))),
                    code=getattr(entity, "normalized_code", None),
                    message="Entité future sans rattachement hiérarchique exploitable.",
                    severity="error",
                )
            )

    return {
        "future_levels": dict(future_levels),
        "anomalies": anomalies,
    }


def _render_markdown_report(
    root: AdministrativeTreeNode,
    statistics: dict[str, Any],
    anomalies: list[AdministrativeAnomaly],
    compatibility: dict[str, Any],
    quality_report: Any,
) -> str:
    lines = [
        "# Référentiel administratif national",
        "",
        f"- Entités: {statistics['entity_count']}",
        f"- Orphelins: {statistics['orphan_count']}",
        f"- Incohérences: {statistics['inconsistency_count']}",
        f"- Score qualité: {statistics['quality_score']}",
        "",
        "## Arborescence",
        "",
    ]
    lines.extend(_render_tree_lines(root))
    lines.extend([
        "",
        "## Statistiques",
        "",
    ])
    for key, value in statistics["by_level"].items():
        lines.append(f"- {key}: {value}")
    lines.extend([
        "",
        "## Qualité",
        "",
    ])
    quality_indicators = getattr(quality_report, "indicators", [])
    if quality_indicators:
        indicator = quality_indicators[0]
        lines.append(f"- Complétude: {indicator.completeness}")
        lines.append(f"- Cohérence: {indicator.consistency}")
        lines.append(f"- Qualité globale: {indicator.global_quality}")
    lines.extend([
        "",
        "## Anomalies",
        "",
    ])
    if anomalies:
        for anomaly in anomalies:
            code_part = f" [{anomaly.code}]" if anomaly.code else ""
            lines.append(f"- {anomaly.severity}/{anomaly.level}{code_part}: {anomaly.message}")
    else:
        lines.append("- aucune anomalie détectée")
    lines.extend([
        "",
        "## Compatibilité future",
        "",
    ])
    future_levels = compatibility.get("future_levels", {})
    if future_levels:
        for key, value in future_levels.items():
            lines.append(f"- {key}: {value}")
    else:
        lines.append("- aucune entité future analysée")
    return "\n".join(lines)


def _render_tree_lines(node: AdministrativeTreeNode, depth: int = 0) -> list[str]:
    indent = "  " * depth
    code_part = f" ({node.code})" if node.code else ""
    lines = [f"{indent}- {node.label}{code_part} [{node.count}]"]
    for anomaly in node.anomalies:
        lines.append(f"{indent}  - anomalie: {anomaly}")
    for child in node.children:
        lines.extend(_render_tree_lines(child, depth + 1))
    return lines
