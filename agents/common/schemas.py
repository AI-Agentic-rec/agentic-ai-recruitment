
from typing import Literal, Optional
from pydantic import BaseModel, Field, ConfigDict, model_validator
import math


# ============================================================
# CONFIGURATION COMMUNE
# ============================================================

class BaseSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")

class ContexteCandidature(BaseSchema):
    candidate_id: str
    job_id: str


# Les six critères utilisés par les Agents 4 et 5
CRITERES = (
    "competences_obligatoires",
    "experience",
    "diplome_formation",
    "competences_souhaitees",
    "langues",
    "coherence_documents",
)

Critere = Literal[
    "competences_obligatoires",
    "experience",
    "diplome_formation",
    "competences_souhaitees",
    "langues",
    "coherence_documents",
]


# ============================================================
# AGENT 1 — ANALYSE DE L'OFFRE D'EMPLOI
# ============================================================

class Langue(BaseSchema):
    langue: str
    niveau: Optional[str] = None


class ExigencesStructurees(BaseSchema):

    titre_poste: Optional[str] = None

    # Facultatif si le diplôme n'est pas précisé dans l'offre
    diplome_demande: Optional[str] = None

    # Échelle à définir en équipe (Bac, Bac+2, Licence, Master...)
    niveau_diplome_min: Optional[int] = Field(
        default=None,
        ge=0,
        le=8
    )

    # 0 signifie qu'aucune expérience minimale n'est exigée
    experience_min_annees: float = Field(
        default=0,
        ge=0
    )

    competences_obligatoires: list[str] = Field(
        default_factory=list
    )

    competences_souhaitees: list[str] = Field(
        default_factory=list
    )

    langues: list[Langue] = Field(
        default_factory=list
    )

    missions: list[str] = Field(
        default_factory=list
    )


# ============================================================
# AGENT 2 — EXTRACTION DU CV
# ============================================================

class Formation(BaseSchema):
    diplome: str
    specialite: Optional[str] = None
    etablissement: Optional[str] = None

    # Format recommandé : AAAA-MM
    date_debut: Optional[str] = None
    date_fin: Optional[str] = None


class Experience(BaseSchema):
    poste: str
    entreprise: Optional[str] = None
    description: Optional[str] = None

    # Format recommandé : AAAA-MM
    # Pour une expérience actuelle, date_fin = None
    date_debut: Optional[str] = None
    date_fin: Optional[str] = None

    duree_annees: Optional[float] = Field(
        default=None,
        ge=0
    )

    competences: list[str] = Field(
        default_factory=list
    )


class ProfilCandidat(BaseSchema):
    nom: Optional[str] = None
    prenom: Optional[str] = None

    # Coordonnées extraites du CV
    email: Optional[str] = None
    telephone: Optional[str] = None

    formations: list[Formation] = Field(
        default_factory=list
    )

    experiences: list[Experience] = Field(
        default_factory=list
    )

    competences: list[str] = Field(
        default_factory=list
    )

    langues: list[Langue] = Field(
        default_factory=list
    )

    # Certifications obtenues par le candidat
    certifications: list[str] = Field(
        default_factory=list
    )

    experience_totale_annees: float = Field(
        default=0,
        ge=0
    )


# ============================================================
# AGENT 3 — VÉRIFICATION DES DOCUMENTS
# ============================================================

class InfosDiplome(BaseSchema):
    nom: Optional[str] = None
    prenom: Optional[str] = None
    diplome: Optional[str] = None
    specialite: Optional[str] = None
    etablissement: Optional[str] = None

    # Format recommandé : AAAA-MM-JJ
    date_obtention: Optional[str] = None


class InfosCIN(BaseSchema):
    nom: Optional[str] = None
    prenom: Optional[str] = None

    # Format recommandé : AAAA-MM-JJ
    date_naissance: Optional[str] = None

    # Information sensible : ne pas transmettre inutilement
    # aux Agents 4 et 5, ni inclure dans les rapports.
    numero_cin: Optional[str] = None


class Incoherence(BaseSchema):
    type: Literal[
        "identite",
        "diplome",
        "date",
        "autre"
    ]

    description: str

    gravite: Literal[
        "faible",
        "moyenne",
        "elevee"
    ]

    documents: list[str] = Field(
        default_factory=list
    )


class VerificationDocuments(BaseSchema):

    infos_diplome: Optional[InfosDiplome] = None

    infos_cin: Optional[InfosCIN] = None

    # Documents effectivement analysés
    documents_analyses: list[str] = Field(
        default_factory=list
    )

    # Documents attendus mais non fournis
    documents_manquants: list[str] = Field(
        default_factory=list
    )

    # Documents reçus mais impossibles à analyser
    documents_illisibles: list[str] = Field(
        default_factory=list
    )

    incoherences: list[Incoherence] = Field(
        default_factory=list
    )

    niveau_conformite: Literal[
        "conforme",
        "partiellement_conforme",
        "non_conforme"
    ]

    score_coherence: int = Field(
        ge=0,
        le=100
    )

    resume: str


# ============================================================
# AGENT 4 — MATCHING CANDIDAT / OFFRE
# ============================================================

class DetailCritere(BaseSchema):

    critere: Critere

    ponderation: float = Field(
        ge=0,
        le=100
    )

    score: float = Field(
        ge=0,
        le=100
    )

    justification: str


class ResultatMatching(BaseSchema):

    score_global: float = Field(
        ge=0,
        le=100
    )

    details: list[DetailCritere]

    competences_correspondantes: list[str] = Field(
        default_factory=list
    )

    competences_manquantes: list[str] = Field(
        default_factory=list
    )

    diplome_conforme: bool

    experience_candidat_annees: float = Field(
        ge=0
    )

    @model_validator(mode="after")
    def verifier_matching(self):

        # 1. Vérifier la présence exacte des six critères
        criteres = [
            detail.critere
            for detail in self.details
        ]

        if (
            len(criteres) != len(CRITERES)
            or set(criteres) != set(CRITERES)
        ):
            raise ValueError(
                "Le matching doit contenir exactement les six critères, "
                "sans doublon ni critère manquant."
            )

        # 2. Vérifier que les pondérations totalisent 100
        somme_ponderations = sum(
            detail.ponderation
            for detail in self.details
        )

        if not math.isclose(
            somme_ponderations,
            100.0,
            rel_tol=0,
            abs_tol=0.01
        ):
            raise ValueError(
                f"La somme des pondérations doit être égale à 100. "
                f"Valeur actuelle : {somme_ponderations}"
            )

        # 3. Vérifier le score global
        score_calcule = sum(
            detail.ponderation * detail.score / 100
            for detail in self.details
        )

        if not math.isclose(
            self.score_global,
            score_calcule,
            rel_tol=0,
            abs_tol=0.5
        ):
            raise ValueError(
                f"Score global incohérent. "
                f"Score déclaré : {self.score_global}, "
                f"score calculé : {score_calcule:.2f}"
            )

        # 4. Vérifier les compétences correspondantes/manquantes
        competences_communes = (
            set(self.competences_correspondantes)
            & set(self.competences_manquantes)
        )

        if competences_communes:
            raise ValueError(
                "Une compétence ne peut pas être à la fois "
                "correspondante et manquante : "
                f"{competences_communes}"
            )

        return self


# ============================================================
# AGENT 5 — GÉNÉRATION DU RAPPORT
# ============================================================

class RapportCandidature(BaseSchema):

    resume: str

    score_global: float = Field(
        ge=0,
        le=100
    )

    points_forts: list[str] = Field(
        default_factory=list
    )

    points_manquants: list[str] = Field(
        default_factory=list
    )

    # Réutilisation du modèle de l'Agent 3
    incoherences: list[Incoherence] = Field(
        default_factory=list
    )

    # Reprise des résultats détaillés de l'Agent 4
    justification_score: list[DetailCritere]

    conclusion: str

    avis_indicatif: Literal[
        "favorable",
        "defavorable",
        "a_etudier"
    ]

    decision_finale: str = (
        "La décision finale appartient au responsable du recrutement."
    )

    @model_validator(mode="after")
    def verifier_rapport(self):

        # 1. Vérifier les six critères
        criteres = [
            detail.critere
            for detail in self.justification_score
        ]

        if (
            len(criteres) != len(CRITERES)
            or set(criteres) != set(CRITERES)
        ):
            raise ValueError(
                "Le rapport doit contenir exactement les six critères, "
                "sans doublon ni critère manquant."
            )

        # 2. Vérifier que les pondérations totalisent 100
        somme_ponderations = sum(
            detail.ponderation
            for detail in self.justification_score
        )

        if not math.isclose(
            somme_ponderations,
            100.0,
            rel_tol=0,
            abs_tol=0.01
        ):
            raise ValueError(
                f"La somme des pondérations du rapport doit être égale à 100. "
                f"Valeur actuelle : {somme_ponderations}"
            )

        # 3. Vérifier la cohérence du score global
        score_calcule = sum(
            detail.ponderation * detail.score / 100
            for detail in self.justification_score
        )

        if not math.isclose(
            self.score_global,
            score_calcule,
            rel_tol=0,
            abs_tol=0.5
        ):
            raise ValueError(
                f"Score du rapport incohérent. "
                f"Score déclaré : {self.score_global}, "
                f"score calculé : {score_calcule:.2f}"
            )

        return self






