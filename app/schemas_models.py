from __future__ import annotations

from datetime import datetime
from typing import Any, Dict

from pydantic import BaseModel, Field


class SiteHistorySchema(BaseModel):
    id: int | None = None
    site_id: int
    changed_at: datetime | None = None
    changed_by: str | None = None
    action: str | None = None
    data: Dict[str, Any] | None = None

    class Config:
        orm_mode = True


class SiteExtendedSchema(BaseModel):
    id: int | None = None
    nom: str
    code_site: str
    code_fdsu: str
    statut: str
    type_site: str
    zone_fdsu: str | None = None
    operateur: str | None = None
    technologie: str | None = None
    alimentation: str | None = None
    adresse: str | None = None
    date_creation: datetime | None = None
    date_installation: datetime | None = None
    date_mise_service: datetime | None = None
    hauteur_pylone: float | None = None
    capacite: int | None = None
    altitude: float | None = None
    precision_gps: float | None = None
    observations: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    programme: str | None = Field(None, description="Programme associé au site")
    annee_planification: int | None = Field(None, description="Année de planification")
    phase: str | None = Field(None, description="Phase du projet")
    priorite: int | None = Field(0, description="Priorité du site")

    class Config:
        orm_mode = True
