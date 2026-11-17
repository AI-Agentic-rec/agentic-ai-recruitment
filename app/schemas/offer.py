from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models import StatutOffre


class OffreChamps(BaseModel):
    titre: str = Field(min_length=1, max_length=255)
    description: str = Field(min_length=1)
    diplome_demande: str | None = Field(default=None, max_length=255)
    experience_annees: float | None = Field(default=None, ge=0)
    competences_obligatoires: list[str] = Field(default_factory=list)
    competences_souhaitees: list[str] = Field(default_factory=list)
    langues: list[str] = Field(default_factory=list)
    localisation: str | None = Field(default=None, max_length=255)


class OffreCreate(OffreChamps):
    id_admin: int = Field(gt=0)


class OffreUpdate(BaseModel):
    titre: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, min_length=1)
    diplome_demande: str | None = Field(default=None, max_length=255)
    experience_annees: float | None = Field(default=None, ge=0)
    competences_obligatoires: list[str] | None = None
    competences_souhaitees: list[str] | None = None
    langues: list[str] | None = None
    localisation: str | None = Field(default=None, max_length=255)


class OffreRead(OffreChamps):
    model_config = ConfigDict(from_attributes=True)

    id: int
    id_admin: int
    statut: StatutOffre
    date_creation: datetime
    date_publication: datetime | None
    date_cloture: datetime | None
