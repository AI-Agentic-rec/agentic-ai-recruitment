from typing import Literal

from pydantic import BaseModel, Field, field_validator


class OffreCreate(BaseModel):
    titre: str = Field(min_length=1, max_length=255)
    description: str = Field(min_length=1)
    diplome_demande: str | None = Field(default=None, max_length=255)
    experience_annees: float | None = Field(default=None, ge=0)
    competences_obligatoires: list[str] = []
    competences_souhaitees: list[str] = []
    langues: list[str] = []
    localisation: str | None = Field(default=None, max_length=255)
    id_admin: int = Field(gt=0)
    action: Literal["brouillon", "publier"] = "brouillon"


class OffreUpdate(BaseModel):
    titre: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, min_length=1)
    diplome_demande: str | None = Field(default=None, max_length=255)
    experience_annees: float | None = Field(default=None, ge=0)
    competences_obligatoires: list[str] | None = None
    competences_souhaitees: list[str] | None = None
    langues: list[str] | None = None
    localisation: str | None = Field(default=None, max_length=255)
    action: str | None = None


class OffreRead(BaseModel):
    id: int
    titre: str
    description: str
    diplome_demande: str | None = None
    experience_annees: float | None = None
    competences_obligatoires: list[str] = []
    competences_souhaitees: list[str] = []
    langues: list[str] = []
    localisation: str | None = None
    id_admin: int
    statut: str
    date_creation: str
    date_publication: str | None = None
    date_cloture: str | None = None

    @field_validator("statut", mode="before")
    @classmethod
    def lowercase_statut(cls, v):
        if hasattr(v, "value"):
            return v.value.lower()
        if isinstance(v, str):
            return v.lower()
        return v


class OffreListeResponse(BaseModel):
    offres: list[OffreRead]
    counts: dict[str, int]


class OffreDetailResponse(BaseModel):
    offre: OffreRead