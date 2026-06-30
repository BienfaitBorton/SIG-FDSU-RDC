from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, Field


class SiteStatus(str, Enum):
    Projet = "Projet"
    Survey = "Survey"
    Installation = "Installation"
    Actif = "Actif"
    Maintenance = "Maintenance"
    Hors_service = "Hors service"


class ProvinceBase(BaseModel):
    nom: str = Field(..., json_schema_extra={"example": "Kinshasa"})
    code: str = Field(..., json_schema_extra={"example": "11"})
    zone: str = Field(..., json_schema_extra={"example": "ND"})
    chef_lieu: str | None = Field(None, json_schema_extra={"example": "Kinshasa"})
    population: int | None = Field(None, json_schema_extra={"example": 15000000})
    superficie: float | None = Field(None, json_schema_extra={"example": 9965.0})


class ProvinceCreate(ProvinceBase):
    pass


class ProvinceRead(ProvinceBase):
    id: int

    model_config = {"from_attributes": True}


class TerritoireBase(BaseModel):
    nom: str = Field(..., json_schema_extra={"example": "Funa"})
    code: str = Field(..., json_schema_extra={"example": "145"})
    chef_lieu: str | None = Field(None, json_schema_extra={"example": "Matete"})
    province_id: int


class TerritoireCreate(TerritoireBase):
    pass


class TerritoireRead(TerritoireBase):
    id: int

    model_config = {"from_attributes": True}


class CollectiviteBase(BaseModel):
    nom: str = Field(..., json_schema_extra={"example": "Kasa-Vubu"})
    code: str = Field(..., json_schema_extra={"example": "001"})
    type_collectivite: str = Field(..., json_schema_extra={"example": "Secteur"})
    territoire_id: int


class CollectiviteCreate(CollectiviteBase):
    pass


class CollectiviteRead(CollectiviteBase):
    id: int

    model_config = {"from_attributes": True}


class GroupementBase(BaseModel):
    nom: str = Field(..., json_schema_extra={"example": "Groupement Alpha"})
    code: str = Field(..., json_schema_extra={"example": "001"})
    collectivite_id: int


class GroupementCreate(GroupementBase):
    pass


class GroupementRead(GroupementBase):
    id: int

    model_config = {"from_attributes": True}


class VillageBase(BaseModel):
    nom: str = Field(..., json_schema_extra={"example": "Village Exemple"})
    code: str = Field(..., json_schema_extra={"example": "001"})
    groupement_id: int


class VillageCreate(VillageBase):
    pass


class VillageRead(VillageBase):
    id: int

    model_config = {"from_attributes": True}


class SiteBase(BaseModel):
    nom: str = Field(..., json_schema_extra={"example": "Site FDSU 001"})
    village_id: int
    zone_fdsu: str | None = Field(None, json_schema_extra={"example": "ND"})
    operateur: str | None = Field(None, json_schema_extra={"example": "Vodacom"})
    technologie: str | None = Field(None, json_schema_extra={"example": "4G"})
    energie: str | None = Field(None, json_schema_extra={"example": "Fibre"})
    statut: SiteStatus | None = Field(None, json_schema_extra={"example": "Actif"})
    date_creation: date | None = Field(None, json_schema_extra={"example": "2026-01-01"})
    date_installation: date | None = Field(None, json_schema_extra={"example": "2026-02-01"})
    date_mise_service: date | None = Field(None, json_schema_extra={"example": "2026-03-01"})
    altitude: float | None = Field(None, json_schema_extra={"example": 1030.5})
    precision_gps: float | None = Field(None, json_schema_extra={"example": 5.2})
    observations: str | None = Field(None, json_schema_extra={"example": "Site à proximité du village"})
    latitude: float | None = Field(None, json_schema_extra={"example": -4.4419})
    longitude: float | None = Field(None, json_schema_extra={"example": 15.2663})


class SiteCreate(SiteBase):
    pass


class SiteRead(SiteBase):
    id: int
    code_site: str

    model_config = {"from_attributes": True}


class MissionBase(BaseModel):
    titre: str = Field(..., json_schema_extra={"example": "Mission de survey"})
    description: str | None = Field(None, json_schema_extra={"example": "Inspection du site"})
    date_debut: date | None = Field(None, json_schema_extra={"example": "2026-04-01"})
    date_fin: date | None = Field(None, json_schema_extra={"example": "2026-04-15"})
    site_id: int


class MissionCreate(MissionBase):
    pass


class MissionRead(MissionBase):
    id: int

    model_config = {"from_attributes": True}


class DocumentBase(BaseModel):
    nom: str = Field(..., json_schema_extra={"example": "Rapport terrain"})
    type: str = Field(..., json_schema_extra={"example": "PDF"})
    chemin: str = Field(..., json_schema_extra={"example": "/data/docs/rapport.pdf"})
    mission_id: int


class DocumentCreate(DocumentBase):
    pass


class DocumentRead(DocumentBase):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}


class PhotoBase(BaseModel):
    nom: str = Field(..., json_schema_extra={"example": "Photo antenne"})
    caption: str | None = Field(None, json_schema_extra={"example": "Vue du pylône"})
    chemin: str = Field(..., json_schema_extra={"example": "/data/photos/antenne.jpg"})
    mission_id: int


class PhotoCreate(PhotoBase):
    pass


class PhotoRead(PhotoBase):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}
