"""Les 4 classes `«Agent N»` du diagramme : ce que produisent les agents d'IA.

Chaque table a pour clé primaire la clé étrangère (relation 0..1 avec l'offre ou la candidature).
Les sous-objets `«JSON»` (Langue, Formation, Experience, InfosDiplome, InfosCIN, RapportCandidature,
DetailCritere, Incoherence) sont stockés en JSONB dans la colonne qui les porte.
Le contrat de ces JSON est `agents/common/schemas.py`.
"""
from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import AvisIndicatif, NiveauConformite


class ExigencesStructurees(Base):
    """«Agent 1» : exigences d'une offre (0..1 par offre)."""

    __tablename__ = "exigences_structurees"

    id_offre: Mapped[int] = mapped_column(ForeignKey("offre.id", ondelete="CASCADE"), primary_key=True)
    titre_poste: Mapped[str | None] = mapped_column(String(255))
    diplome_demande: Mapped[str | None] = mapped_column(String(255))
    niveau_diplome_min: Mapped[int | None] = mapped_column(Integer)  # 0..8
    experience_min_annees: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    competences_obligatoires: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    competences_souhaitees: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    langues: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, default=list, nullable=False)  # list[Langue]
    missions: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)

    offre: Mapped["Offre"] = relationship(back_populates="exigences")


class ProfilCandidat(Base):
    """«Agent 2» : profil extrait du CV (0..1 par candidature)."""

    __tablename__ = "profil_candidat"

    id_candidature: Mapped[int] = mapped_column(ForeignKey("candidature.id", ondelete="CASCADE"), primary_key=True)
    nom: Mapped[str | None] = mapped_column(String(100))
    prenom: Mapped[str | None] = mapped_column(String(100))
    email: Mapped[str | None] = mapped_column(String(255))
    telephone: Mapped[str | None] = mapped_column(String(50))
    formations: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, default=list, nullable=False)  # list[Formation]
    experiences: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, default=list, nullable=False)  # list[Experience]
    competences: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    langues: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, default=list, nullable=False)  # list[Langue]
    certifications: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    experience_totale_annees: Mapped[float] = mapped_column(Float, default=0, nullable=False)

    candidature: Mapped["Candidature"] = relationship(back_populates="profil")


class VerificationDocuments(Base):
    """«Agent 3» : vérification du diplôme et de la CIN (0..1 par candidature)."""

    __tablename__ = "verification_documents"

    id_candidature: Mapped[int] = mapped_column(ForeignKey("candidature.id", ondelete="CASCADE"), primary_key=True)
    infos_diplome: Mapped[dict[str, Any] | None] = mapped_column(JSONB)  # InfosDiplome (0..1)
    infos_cin: Mapped[dict[str, Any] | None] = mapped_column(JSONB)  # InfosCIN (0..1), numero_cin sensible
    documents_analyses: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    documents_manquants: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    documents_illisibles: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    incoherences: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, default=list, nullable=False)  # list[Incoherence]
    niveau_conformite: Mapped[NiveauConformite] = mapped_column(
        Enum(NiveauConformite, name="niveau_conformite"), nullable=False
    )
    score_coherence: Mapped[int] = mapped_column(Integer, nullable=False)  # 0..100
    resume: Mapped[str] = mapped_column(Text, default="", nullable=False)

    candidature: Mapped["Candidature"] = relationship(back_populates="verification")


class ResultatAnalyse(Base):
    """«Agents 4 et 5» : score de correspondance (agent 4) et rapport (agent 5), 0..1 par candidature."""

    __tablename__ = "resultat_analyse"

    id_candidature: Mapped[int] = mapped_column(ForeignKey("candidature.id", ondelete="CASCADE"), primary_key=True)
    score_global: Mapped[float] = mapped_column(Float, nullable=False)  # 0..100
    details: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, default=list, nullable=False)  # list[DetailCritere] {6}
    competences_correspondantes: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    competences_manquantes: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    diplome_conforme: Mapped[bool] = mapped_column(Boolean, nullable=False)
    experience_candidat_annees: Mapped[float] = mapped_column(Float, default=0, nullable=False)
    rapport: Mapped[dict[str, Any] | None] = mapped_column(JSONB)  # RapportCandidature (agent 5, peut arriver après)
    avis_indicatif: Mapped[AvisIndicatif | None] = mapped_column(Enum(AvisIndicatif, name="avis_indicatif"))
    date_analyse: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    candidature: Mapped["Candidature"] = relationship(back_populates="resultat")
