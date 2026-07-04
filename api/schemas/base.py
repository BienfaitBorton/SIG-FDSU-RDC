from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, Field


class SiteStatus(str, Enum):
    Prevu = "Prévu"
    En_etude = "En étude"
    En_construction = "En construction"
    Actif = "Actif"
    Hors_service = "Hors service"


class ProvinceBase(BaseModel):
    nom: str = Field(..., description="Nom de la province.", json_schema_extra={"example": "Kinshasa"})
    code: str = Field(..., description="Code province FDSU.", json_schema_extra={"example": "11"})
    zone: str = Field(..., description="Zone administrative FDSU.", json_schema_extra={"example": "ND"})
    chef_lieu: str | None = Field(None, description="Chef-lieu de la province.", json_schema_extra={"example": "Kinshasa"})
    population: int | None = Field(None, description="Population estimée de la province.", json_schema_extra={"example": 15000000})
    superficie: float | None = Field(None, description="Superficie de la province en km².", json_schema_extra={"example": 9965.0})


class ProvinceCreate(ProvinceBase):
    pass


class ProvinceRead(ProvinceBase):
    id: int

    model_config = {"from_attributes": True}


class TerritoireBase(BaseModel):
    nom: str = Field(..., description="Nom du territoire.", json_schema_extra={"example": "Funa"})
    code: str = Field(..., description="Code territoire.", json_schema_extra={"example": "145"})
    chef_lieu: str | None = Field(None, description="Chef-lieu du territoire.", json_schema_extra={"example": "Matete"})
    province_id: int = Field(..., description="Identifiant de la province parent.")
    nb_sites_reference: int = Field(0, description="Nombre de sites GSM de référence (import FDSU Structure).", json_schema_extra={"example": 12})


class TerritoireCreate(TerritoireBase):
    pass


class TerritoireRead(TerritoireBase):
    id: int

    model_config = {"from_attributes": True}


class CollectiviteBase(BaseModel):
    nom: str = Field(..., description="Nom de la collectivité.", json_schema_extra={"example": "Kasa-Vubu"})
    code: str = Field(..., description="Code de la collectivité.", json_schema_extra={"example": "001"})
    type_collectivite: str = Field(..., description="Type de collectivité (Secteur, Chefferie, Cité).", json_schema_extra={"example": "Secteur"})
    territoire_id: int = Field(..., description="Identifiant du territoire parent.")


class CollectiviteCreate(CollectiviteBase):
    pass


class CollectiviteRead(CollectiviteBase):
    id: int

    model_config = {"from_attributes": True}


class GroupementBase(BaseModel):
    nom: str = Field(..., description="Nom du groupement.", json_schema_extra={"example": "Groupement Alpha"})
    code: str = Field(..., description="Code du groupement.", json_schema_extra={"example": "001"})
    collectivite_id: int = Field(..., description="Identifiant de la collectivité parent.")


class GroupementCreate(GroupementBase):
    pass


class GroupementRead(GroupementBase):
    id: int

    model_config = {"from_attributes": True}


class VillageBase(BaseModel):
    nom: str = Field(..., description="Nom du village.", json_schema_extra={"example": "Village Exemple"})
    code: str = Field(..., description="Code du village.", json_schema_extra={"example": "001"})
    groupement_id: int = Field(..., description="Identifiant du groupement parent.")


class VillageCreate(VillageBase):
    pass


class VillageRead(VillageBase):
    id: int

    model_config = {"from_attributes": True}


class SiteType(str, Enum):
    Backbone = "Backbone"
    BTS = "BTS"
    CCN = "CCN"
    Gateway = "Gateway"
    Relais = "Relais"
    POP = "POP"
    Autre = "Autre"


class SiteTechnology(str, Enum):
    G2 = "2G"
    G3 = "3G"
    G4 = "4G"
    G5 = "5G"
    VSAT = "VSAT"
    Fibre = "Fibre"
    Starlink = "Starlink"


class SiteAlimentation(str, Enum):
    Solaire = "Solaire"
    Groupe = "Groupe"
    SNEL = "SNEL"
    Mixte = "Mixte"


class SiteBase(BaseModel):
    nom: str = Field(..., description="Nom du site FDSU.", json_schema_extra={"example": "Site FDSU 001"})
    code_fdsu: str | None = Field(None, description="Code unique FDSU du site.", json_schema_extra={"example": "FDSU_ND_11_145_001_001"})
    village_id: int = Field(..., description="Identifiant du village associé au site.")
    statut: SiteStatus = Field(..., description="Statut opérationnel du site.", json_schema_extra={"example": "Actif"})
    type_site: SiteType = Field(..., description="Type d'infrastructure du site.", json_schema_extra={"example": "BTS"})
    zone_fdsu: str | None = Field(None, description="Zone administrative FDSU.", json_schema_extra={"example": "ND"})
    operateur: str | None = Field(None, description="Opérateur qui exploite le site.", json_schema_extra={"example": "Vodacom"})
    technologie: SiteTechnology | None = Field(None, description="Technologie de transmission utilisée.", json_schema_extra={"example": "4G"})
    alimentation: SiteAlimentation | None = Field(None, description="Source d'alimentation du site.", json_schema_extra={"example": "Solaire"})
    adresse: str | None = Field(None, description="Adresse précise du site.", json_schema_extra={"example": "Avenue du Centre, Village Test"})
    date_creation: date | None = Field(None, description="Date de création du site dans le référentiel.", json_schema_extra={"example": "2026-01-01"})
    date_installation: date | None = Field(None, description="Date d'installation des équipements.", json_schema_extra={"example": "2026-02-01"})
    date_mise_service: date | None = Field(None, description="Date de mise en service effective.", json_schema_extra={"example": "2026-03-01"})
    hauteur_pylone: float | None = Field(None, description="Hauteur du pylône en mètres.", json_schema_extra={"example": 30.5})
    capacite: int | None = Field(None, description="Capacité d'accueil ou de charge du site.", json_schema_extra={"example": 500})
    altitude: float | None = Field(None, description="Altitude du site en mètres.", json_schema_extra={"example": 1030.5})
    precision_gps: float | None = Field(None, description="Précision GPS du positionnement en mètres.", json_schema_extra={"example": 5.2})
    observations: str | None = Field(None, description="Observations techniques ou terrain.", json_schema_extra={"example": "Site à proximité du village"})
    latitude: float | None = Field(None, description="Latitude géographique du site.", json_schema_extra={"example": -4.4419})
    longitude: float | None = Field(None, description="Longitude géographique du site.", json_schema_extra={"example": 15.2663})


class SiteCreate(SiteBase):
    pass


class SiteRead(SiteBase):
    id: int
    code_site: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MissionBase(BaseModel):
    titre: str = Field(..., description="Titre de la mission.", json_schema_extra={"example": "Mission de prospection"})
    description: str | None = Field(None, description="Description de la mission.", json_schema_extra={"example": "Inspection détaillée du site"})
    date_debut: date | None = Field(None, description="Date de début de la mission.", json_schema_extra={"example": "2026-04-01"})
    date_fin: date | None = Field(None, description="Date de fin prévue de la mission.", json_schema_extra={"example": "2026-04-15"})
    site_id: int = Field(..., description="Identifiant du site associé à la mission.")


class MissionCreate(MissionBase):
    pass


class MissionRead(MissionBase):
    id: int

    model_config = {"from_attributes": True}


class DocumentBase(BaseModel):
    nom: str = Field(..., description="Nom du document.", json_schema_extra={"example": "Rapport terrain"})
    type: str = Field(..., description="Type de document.", json_schema_extra={"example": "PDF"})
    chemin: str = Field(..., description="Chemin d'accès ou URL du document.", json_schema_extra={"example": "/data/docs/rapport.pdf"})
    mission_id: int = Field(..., description="Identifiant de la mission associée.")


class DocumentCreate(DocumentBase):
    pass


class DocumentRead(DocumentBase):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}


class PhotoBase(BaseModel):
    nom: str = Field(..., description="Nom de la photo.", json_schema_extra={"example": "Photo antenne"})
    caption: str | None = Field(None, description="Légende de la photo.", json_schema_extra={"example": "Vue du pylône"})
    chemin: str = Field(..., description="Chemin d'accès ou URL de la photo.", json_schema_extra={"example": "/data/photos/antenne.jpg"})
    mission_id: int = Field(..., description="Identifiant de la mission associée.")


class PhotoCreate(PhotoBase):
    pass


class PhotoRead(PhotoBase):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}


class TerritorialEnrichmentSuggestionBase(BaseModel):
    entity_type: str = Field(..., description="Niveau territorial concerné.", json_schema_extra={"example": "province"})
    entity_id: int | None = Field(None, description="Identifiant interne de l'entité si disponible.")
    entity_name: str | None = Field(None, description="Nom lisible de l'entité.", json_schema_extra={"example": "Kinshasa"})
    field_name: str = Field(..., description="Champ de fiche à enrichir.", json_schema_extra={"example": "potentiel_numerique"})
    proposed_value: str = Field(..., description="Valeur proposée, jamais injectée directement dans la fiche officielle.")
    source_name: str = Field(..., description="Source publique autorisée.", json_schema_extra={"example": "CAID"})
    source_url: str = Field(..., description="URL publique de la source consultée.")
    consulted_at: datetime = Field(..., description="Date de consultation de la source.")
    confidence_level: str = Field(..., description="Niveau de confiance attribué.", json_schema_extra={"example": "élevé"})


class TerritorialEnrichmentSuggestionCreate(TerritorialEnrichmentSuggestionBase):
    pass


class TerritorialEnrichmentSuggestionUpdate(BaseModel):
    proposed_value: str | None = Field(None, description="Valeur ajustée avant validation.")
    status: str | None = Field(None, description="Statut de revue: proposé, validé ou rejeté.")
    review_note: str | None = Field(None, description="Commentaire de validation ou rejet.")
    validated_by: str | None = Field(None, description="Utilisateur validateur.")


class TerritorialEnrichmentSuggestionRead(TerritorialEnrichmentSuggestionBase):
    id: int
    status: str
    review_note: str | None = None
    validated_at: datetime | None = None
    validated_by: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
