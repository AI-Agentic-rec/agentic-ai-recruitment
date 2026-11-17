from datetime import datetime

from sqlalchemy import DateTime, Enum, Float, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import StatutCandidature, StatutOffre, TypeDocument


class Offre(Base):
    """Classe `Offre` : 0..* offres par administrateur."""

    __tablename__ = "offre"

    id: Mapped[int] = mapped_column(primary_key=True)
    id_admin: Mapped[int] = mapped_column(ForeignKey("utilisateur.id", ondelete="RESTRICT"), index=True)
    titre: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    diplome_demande: Mapped[str | None] = mapped_column(String(255))
    experience_annees: Mapped[float | None] = mapped_column(Float)
    competences_obligatoires: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    competences_souhaitees: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    langues: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    localisation: Mapped[str | None] = mapped_column(String(255))
    statut: Mapped[StatutOffre] = mapped_column(
        Enum(StatutOffre, name="statut_offre"), default=StatutOffre.BROUILLON, nullable=False, index=True
    )
    date_creation: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    date_publication: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    date_cloture: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    admin: Mapped["Utilisateur"] = relationship(back_populates="offres_creees")
    candidatures: Mapped[list["Candidature"]] = relationship(back_populates="offre", cascade="all, delete-orphan")
    exigences: Mapped["ExigencesStructurees | None"] = relationship(
        back_populates="offre", cascade="all, delete-orphan", uselist=False
    )


class Candidature(Base):
    """Classe `Candidature` : un candidat ne postule qu'une fois à une offre."""

    __tablename__ = "candidature"
    __table_args__ = (UniqueConstraint("id_candidat", "id_offre", name="uq_candidature_candidat_offre"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    id_candidat: Mapped[int] = mapped_column(ForeignKey("utilisateur.id", ondelete="CASCADE"), index=True)
    id_offre: Mapped[int] = mapped_column(ForeignKey("offre.id", ondelete="CASCADE"), index=True)
    date_candidature: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    statut: Mapped[StatutCandidature] = mapped_column(
        Enum(StatutCandidature, name="statut_candidature"),
        default=StatutCandidature.ENVOYEE,
        nullable=False,
        index=True,
    )
    message_erreur: Mapped[str | None] = mapped_column(Text)

    candidat: Mapped["Utilisateur"] = relationship(back_populates="candidatures")
    offre: Mapped["Offre"] = relationship(back_populates="candidatures")
    documents: Mapped[list["Document"]] = relationship(back_populates="candidature", cascade="all, delete-orphan")
    profil: Mapped["ProfilCandidat | None"] = relationship(
        back_populates="candidature", cascade="all, delete-orphan", uselist=False
    )
    verification: Mapped["VerificationDocuments | None"] = relationship(
        back_populates="candidature", cascade="all, delete-orphan", uselist=False
    )
    resultat: Mapped["ResultatAnalyse | None"] = relationship(
        back_populates="candidature", cascade="all, delete-orphan", uselist=False
    )


class Document(Base):
    """Classe `Document` : 1..3 par candidature (au plus un CV, un diplôme, une CIN)."""

    __tablename__ = "document"
    __table_args__ = (UniqueConstraint("id_candidature", "type", name="uq_document_candidature_type"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    id_candidature: Mapped[int] = mapped_column(ForeignKey("candidature.id", ondelete="CASCADE"), index=True)
    type: Mapped[TypeDocument] = mapped_column(Enum(TypeDocument, name="type_document"), nullable=False)
    chemin_fichier: Mapped[str] = mapped_column(String(1024), nullable=False)
    date_import: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    candidature: Mapped["Candidature"] = relationship(back_populates="documents")


__all__ = ["Offre", "Candidature", "Document"]
