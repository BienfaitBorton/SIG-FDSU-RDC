from __future__ import annotations

from datetime import date, datetime
from enum import Enum

from geoalchemy2 import Geometry
from sqlalchemy import BigInteger, Date, DateTime, Enum as SQLEnum, ForeignKey, Index, Numeric, String, Text, event, func, select
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from app.code_generator import generate_fdsu_code


class Base(DeclarativeBase):
    """Base declarative model for SQLAlchemy ORM."""
    pass


class CollectiviteType(str, Enum):
    Secteur = "Secteur"
    Chefferie = "Chefferie"
    Cite = "Cité"


class SiteStatus(str, Enum):
    Projet = "Projet"
    Survey = "Survey"
    Installation = "Installation"
    Actif = "Actif"
    Maintenance = "Maintenance"
    Hors_service = "Hors service"


class Province(Base):
    __tablename__ = "provinces"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    nom: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    code: Mapped[str] = mapped_column(String(5), nullable=False, unique=True)
    zone: Mapped[str] = mapped_column(String(5), nullable=False)
    chef_lieu: Mapped[str | None] = mapped_column(String(200), nullable=True)
    population: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    superficie: Mapped[float | None] = mapped_column(Numeric(14, 2), nullable=True)
    geom: Mapped[Geometry | None] = mapped_column(Geometry(geometry_type="MULTIPOLYGON", srid=4326), nullable=True)

    territoires: Mapped[list[Territoire]] = relationship(
        back_populates="province",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    __table_args__ = (
        Index("ix_provinces_code", "code"),
        Index("ix_provinces_geom", "geom", postgresql_using="gist"),
    )

    def __repr__(self) -> str:
        return (
            f"<Province(id={self.id}, code={self.code}, nom={self.nom}, "
            f"zone={self.zone})>"
        )


class Territoire(Base):
    __tablename__ = "territoires"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    nom: Mapped[str] = mapped_column(String(200), nullable=False)
    code: Mapped[str] = mapped_column(String(5), nullable=False)
    chef_lieu: Mapped[str | None] = mapped_column(String(200), nullable=True)
    province_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("provinces.id", ondelete="CASCADE"),
        nullable=False,
    )
    geom: Mapped[str | None] = mapped_column(Geometry(geometry_type="MULTIPOLYGON", srid=4326), nullable=True)

    province: Mapped[Province] = relationship(back_populates="territoires")
    collectivites: Mapped[list[Collectivite]] = relationship(
        back_populates="territoire",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    __table_args__ = (
        Index("ix_territoires_code", "code"),
        Index("ix_territoires_province_id", "province_id"),
        Index("ix_territoires_geom", "geom", postgresql_using="gist"),
    )

    def __repr__(self) -> str:
        return (
            f"<Territoire(id={self.id}, code={self.code}, nom={self.nom}, "
            f"chef_lieu={self.chef_lieu})>"
        )


class Collectivite(Base):
    __tablename__ = "collectivites"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    nom: Mapped[str] = mapped_column(String(200), nullable=False)
    code: Mapped[str] = mapped_column(String(5), nullable=False)
    type_collectivite: Mapped[CollectiviteType] = mapped_column(
        SQLEnum(CollectiviteType, name="collectivite_type"), nullable=False
    )
    territoire_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("territoires.id", ondelete="CASCADE"),
        nullable=False,
    )
    geom: Mapped[str | None] = mapped_column(Geometry(geometry_type="MULTIPOLYGON", srid=4326), nullable=True)

    territoire: Mapped[Territoire] = relationship(back_populates="collectivites")
    groupements: Mapped[list[Groupement]] = relationship(
        back_populates="collectivite",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    __table_args__ = (
        Index("ix_collectivites_code", "code"),
        Index("ix_collectivites_territoire_id", "territoire_id"),
        Index("ix_collectivites_geom", "geom", postgresql_using="gist"),
    )

    def __repr__(self) -> str:
        return (
            f"<Collectivite(id={self.id}, type={self.type_collectivite}, "
            f"nom={self.nom})>"
        )


class Groupement(Base):
    __tablename__ = "groupements"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    nom: Mapped[str] = mapped_column(String(200), nullable=False)
    code: Mapped[str] = mapped_column(String(5), nullable=False)
    collectivite_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("collectivites.id", ondelete="CASCADE"),
        nullable=False,
    )
    geom: Mapped[str | None] = mapped_column(Geometry(geometry_type="MULTIPOLYGON", srid=4326), nullable=True)

    collectivite: Mapped[Collectivite] = relationship(back_populates="groupements")
    villages: Mapped[list[Village]] = relationship(
        back_populates="groupement",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    __table_args__ = (
        Index("ix_groupements_code", "code"),
        Index("ix_groupements_collectivite_id", "collectivite_id"),
        Index("ix_groupements_geom", "geom", postgresql_using="gist"),
    )

    def __repr__(self) -> str:
        return f"<Groupement(id={self.id}, code={self.code}, nom={self.nom})>"


class Village(Base):
    __tablename__ = "villages"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    nom: Mapped[str] = mapped_column(String(200), nullable=False)
    code: Mapped[str] = mapped_column(String(5), nullable=False)
    groupement_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("groupements.id", ondelete="CASCADE"),
        nullable=False,
    )
    geom: Mapped[str | None] = mapped_column(Geometry(geometry_type="POINT", srid=4326), nullable=True)

    groupement: Mapped[Groupement] = relationship(back_populates="villages")
    sites: Mapped[list[Site]] = relationship(
        back_populates="village",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    __table_args__ = (
        Index("ix_villages_code", "code"),
        Index("ix_villages_groupement_id", "groupement_id"),
        Index("ix_villages_geom", "geom", postgresql_using="gist"),
    )

    def __repr__(self) -> str:
        return f"<Village(id={self.id}, code={self.code}, nom={self.nom})>"


class Site(Base):
    __tablename__ = "sites"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    nom: Mapped[str] = mapped_column(String(200), nullable=False)
    code_site: Mapped[str] = mapped_column(String(30), nullable=False, unique=True)
    zone_fdsu: Mapped[str | None] = mapped_column(String(50), nullable=True)
    operateur: Mapped[str | None] = mapped_column(String(100), nullable=True)
    technologie: Mapped[str | None] = mapped_column(String(100), nullable=True)
    energie: Mapped[str | None] = mapped_column(String(100), nullable=True)
    statut: Mapped[SiteStatus | None] = mapped_column(
        SQLEnum(SiteStatus, name="site_status"), nullable=True
    )
    date_creation: Mapped[date | None] = mapped_column(Date, nullable=True)
    date_installation: Mapped[date | None] = mapped_column(Date, nullable=True)
    date_mise_service: Mapped[date | None] = mapped_column(Date, nullable=True)
    altitude: Mapped[float | None] = mapped_column(nullable=True)
    precision_gps: Mapped[float | None] = mapped_column(nullable=True)
    observations: Mapped[str | None] = mapped_column(Text, nullable=True)
    latitude: Mapped[float | None] = mapped_column(nullable=True)
    longitude: Mapped[float | None] = mapped_column(nullable=True)
    village_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("villages.id", ondelete="CASCADE"),
        nullable=False,
    )
    geom: Mapped[str | None] = mapped_column(Geometry(geometry_type="POINT", srid=4326), nullable=True)

    village: Mapped[Village] = relationship(back_populates="sites")
    missions: Mapped[list[Mission]] = relationship(
        back_populates="site",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    __table_args__ = (
        Index("ix_sites_code_site", "code_site"),
        Index("ix_sites_statut", "statut"),
        Index("ix_sites_village_id", "village_id"),
        Index("ix_sites_geom", "geom", postgresql_using="gist"),
    )

    @property
    def groupement(self) -> Groupement | None:
        return self.village.groupement if self.village is not None else None

    @property
    def collectivite(self) -> Collectivite | None:
        return self.groupement.collectivite if self.groupement is not None else None

    @property
    def territoire(self) -> Territoire | None:
        return self.collectivite.territoire if self.collectivite is not None else None

    @property
    def province(self) -> Province | None:
        return self.territoire.province if self.territoire is not None else None

    @property
    def fdsu_code(self) -> str:
        if not self.code_site:
            raise ValueError("Le code_site n'est pas généré")
        return self.code_site

    def __repr__(self) -> str:
        return (
            f"<Site(id={self.id}, code_site={self.code_site}, nom={self.nom}, "
            f"statut={self.statut})>"
        )


@event.listens_for(Site, "before_insert")
def auto_generate_code_site(mapper, connection, target: Site) -> None:
    if target.date_creation is None:
        target.date_creation = date.today()

    if target.code_site:
        return

    if target.village_id is None:
        raise ValueError("Impossible de générer code_site sans village associé")

    hierarchy_stmt = (
        select(
            Province.zone,
            Province.code,
            Territoire.code.label("territoire_code"),
            Collectivite.code.label("collectivite_code"),
        )
        .select_from(Village)
        .join(Groupement, Village.groupement_id == Groupement.id)
        .join(Collectivite, Groupement.collectivite_id == Collectivite.id)
        .join(Territoire, Collectivite.territoire_id == Territoire.id)
        .join(Province, Territoire.province_id == Province.id)
        .where(Village.id == target.village_id)
    )

    result = connection.execute(hierarchy_stmt).one_or_none()
    if result is None:
        raise ValueError("Impossible de générer code_site sans hiérarchie administrative complète")

    zone, province_code, territoire_code, collectivite_code = result
    prefix = (
        f"FDSU_{zone}_"
        f"{province_code}_"
        f"{territoire_code}_"
        f"{collectivite_code}_"
    )

    code_stmt = select(Site.code_site).where(Site.code_site.like(prefix + "%"))
    rows = connection.execute(code_stmt).scalars().all()
    max_suffix = 0
    for code in rows:
        try:
            suffix = int(code.rsplit("_", 1)[-1])
            max_suffix = max(max_suffix, suffix)
        except (ValueError, AttributeError):
            continue

    target.code_site = generate_fdsu_code(
        zone=zone,
        province_code=province_code,
        territoire_code=territoire_code,
        collectivite_code=collectivite_code,
        numero=str(max_suffix + 1).zfill(3),
    )


class Mission(Base):
    __tablename__ = "missions"

    id: Mapped[int] = mapped_column(primary_key=True)
    titre: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    date_debut: Mapped[date] = mapped_column(Date, nullable=True)
    date_fin: Mapped[date] = mapped_column(Date, nullable=True)
    site_id: Mapped[int] = mapped_column(
        ForeignKey("sites.id", ondelete="SET NULL"), nullable=True
    )

    site: Mapped[Site] = relationship(back_populates="missions")
    documents: Mapped[list[Document]] = relationship(
        back_populates="mission",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    photos: Mapped[list[Photo]] = relationship(
        back_populates="mission",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __repr__(self) -> str:
        return f"<Mission(id={self.id}, titre={self.titre})>"


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    nom: Mapped[str] = mapped_column(String(200), nullable=False)
    type: Mapped[str] = mapped_column(String(100), nullable=False)
    chemin: Mapped[str] = mapped_column(String(500), nullable=False)
    mission_id: Mapped[int] = mapped_column(
        ForeignKey("missions.id", ondelete="CASCADE"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)

    mission: Mapped[Mission] = relationship(back_populates="documents")

    def __repr__(self) -> str:
        return f"<Document(id={self.id}, nom={self.nom})>"


class Photo(Base):
    __tablename__ = "photos"

    id: Mapped[int] = mapped_column(primary_key=True)
    nom: Mapped[str] = mapped_column(String(200), nullable=False)
    caption: Mapped[str] = mapped_column(String(400), nullable=True)
    chemin: Mapped[str] = mapped_column(String(500), nullable=False)
    mission_id: Mapped[int] = mapped_column(
        ForeignKey("missions.id", ondelete="CASCADE"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)

    mission: Mapped[Mission] = relationship(back_populates="photos")

    def __repr__(self) -> str:
        return f"<Photo(id={self.id}, nom={self.nom})>"

class ImportHistory(Base):
    __tablename__ = "import_history"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    filename: Mapped[str] = mapped_column(String(500), nullable=False)
    username: Mapped[str] = mapped_column(String(200), nullable=False)
    imported_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    entity: Mapped[str] = mapped_column(String(100), nullable=False)
    rows_total: Mapped[int] = mapped_column(BigInteger, nullable=False)
    rows_inserted: Mapped[int] = mapped_column(BigInteger, nullable=False)
    rows_updated: Mapped[int] = mapped_column(BigInteger, nullable=False)
    rows_rejected: Mapped[int] = mapped_column(BigInteger, nullable=False)
    duration_seconds: Mapped[float] = mapped_column(nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    file_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)

    def __repr__(self) -> str:
        return (
            f"<ImportHistory(id={self.id}, filename={self.filename}, "
            f"status={self.status}, rows_total={self.rows_total})>"
        )
