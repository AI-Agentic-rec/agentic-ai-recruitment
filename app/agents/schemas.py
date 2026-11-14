from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class BaseSchema(BaseModel):
    model_config = ConfigDict(extra="ignore")


class Langue(BaseSchema):
    langue: str
    niveau: str | None = None


class Formation(BaseSchema):
    diplome: str = ""
    specialite: str | None = None
    etablissement: str | None = None
    date_debut: str | None = None
    date_fin: str | None = None


class Experience(BaseSchema):
    poste: str = ""
    entreprise: str | None = None
    description: str | None = None
    duree_annees: float | None = None
    competences: list[str] = Field(default_factory=list)


class ExigencesStructurees(BaseSchema):
    id_offre: int | None = None
    titre_poste: str = ""
    diplome_requis: str | None = None
    niveau_diplome_min: int | None = None
    experience_min_annees: float = 0
    competences_obligatoires: list[str] = Field(default_factory=list)
    competences_souhaitees: list[str] = Field(default_factory=list)
    langues: list[Langue] = Field(default_factory=list)
    missions: list[str] = Field(default_factory=list)


class ProfilCandidat(BaseSchema):
    id_candidature: int | None = None
    nom: str | None = None
    prenom: str | None = None
    email: str | None = None
    telephone: str | None = None
    competences: list[str] = Field(default_factory=list)
    formations: list[Formation] = Field(default_factory=list)
    experiences: list[Experience] = Field(default_factory=list)
    langues: list[Langue] = Field(default_factory=list)
    certifications: list[str] = Field(default_factory=list)
    experience_totale_annees: float | None = None


class InfoDiplome(BaseSchema):
    nom: str | None = None
    prenom: str | None = None
    diplome: str = ""
    specialite: str | None = None
    etablissement: str | None = None
    date_obtention: str | None = None


class InfoCIN(BaseSchema):
    nom: str | None = None
    prenom: str | None = None
    numero: str | None = None
    date_naissance: str | None = None
    date_expiration: str | None = None


class Incoherence(BaseSchema):
    type: str
    description: str
    gravite: Literal["faible", "moyenne", "elevee"] = "moyenne"


class VerificationDocuments(BaseSchema):
    id_candidature: int | None = None
    infos_diplome: InfoDiplome | None = None
    infos_cin: InfoCIN | None = None
    documents_analyses: list[str] = Field(default_factory=list)
    documents_manquants: list[str] = Field(default_factory=list)
    documents_illisibles: list[str] = Field(default_factory=list)
    incoherences: list[Incoherence] = Field(default_factory=list)
    niveau_conformite: str = "non_conforme"
    score_coherence: float = 0
    resume: str = ""


CRITERES = (
    "competences_obligatoires",
    "experience",
    "diplome_formation",
    "competences_souhaitees",
    "langues",
    "coherence_documents",
)


class DetailCritere(BaseSchema):
    critere: str
    ponderation: float
    score: float
    justification: str


class RapportCandidature(BaseSchema):
    resume_global: str = ""
    score_global: float = 0
    points_forts: list[str] = Field(default_factory=list)
    points_faibles: list[str] = Field(default_factory=list)
    recommandations: list[str] = Field(default_factory=list)
    justification: str = ""
    avis_indicatif: str | None = None


class ResultatMatching(BaseSchema):
    id_candidature: int | None = None
    score_global: float = 0
    details: list[DetailCritere] = Field(default_factory=list)
    competences_correspondantes: list[str] = Field(default_factory=list)
    competences_manquantes: list[str] = Field(default_factory=list)
    diplome_conforme: bool = False
    experience_candidat_annees: float = 0
    rapport: RapportCandidature | None = None
    avis_indicatif: str | None = None


class AgentInput(BaseSchema):
    id_candidature: int
    donnees: dict[str, Any] = Field(default_factory=dict)
