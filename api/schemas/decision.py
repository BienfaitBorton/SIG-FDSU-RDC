from pydantic import BaseModel, Field


class DecisionRecord(BaseModel):
    id: int
    niveau: str
    nom: str
    code: str | None = None
    zone: str | None = None
    province: str | None = None
    territoire: str | None = None
    collectivite: str | None = None
    groupement: str | None = None
    population: int | None = None
    couverture_2g: bool | None = None
    couverture_3g: bool | None = None
    couverture_4g: bool | None = None
    couverture_5g: bool | None = None
    centre_sante: bool | None = None
    ecole_primaire: bool | None = None
    ecole_secondaire: bool | None = None
    marche: bool | None = None
    electricite: bool | None = None
    activite_principale: str | None = None
    activite_secondaire: str | None = None
    potentiel_agricole: str | None = None
    potentiel_minier: str | None = None
    potentiel_commercial: str | None = None
    potentiel_numerique: str | None = None
    niveau_enclavement: str | None = None
    score_connectivite: float | None = None
    score_potentiel: float | None = None
    score_priorite_fdsu: float | None = None
    recommandation: str | None = None
    champs_a_completer: list[str] = Field(default_factory=list)


class DecisionSearchResponse(BaseModel):
    total: int
    items: list[DecisionRecord]
