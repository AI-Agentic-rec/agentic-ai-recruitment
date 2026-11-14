from datetime import datetime
from enum import StrEnum
from typing import Any

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class OfferStatus(StrEnum):
    DRAFT = "draft"
    PUBLISHED = "published"
    CLOSED = "closed"


class ApplicationStatus(StrEnum):
    SUBMITTED = "submitted"
    IN_REVIEW = "in_review"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class DocumentType(StrEnum):
    CV = "cv"
    DIPLOMA = "diploma"
    CIN = "cin"


class Offer(Base):
    __tablename__ = "offers"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    creator_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    diploma_required: Mapped[str | None] = mapped_column(String(255))
    experience_years: Mapped[int | None] = mapped_column(Integer)
    required_skills: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    desired_skills: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    languages: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    location: Mapped[str | None] = mapped_column(String(255))
    status: Mapped[OfferStatus] = mapped_column(
        Enum(OfferStatus, name="offer_status"), default=OfferStatus.DRAFT, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    creator: Mapped["User"] = relationship(back_populates="created_offers")
    requirements: Mapped["OfferRequirements | None"] = relationship(
        back_populates="offer", uselist=False, cascade="all, delete-orphan"
    )
    applications: Mapped[list["Application"]] = relationship(back_populates="offer")


class OfferRequirements(Base):
    __tablename__ = "offer_requirements"

    id: Mapped[int] = mapped_column(primary_key=True)
    offer_id: Mapped[int] = mapped_column(
        ForeignKey("offers.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    content: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    offer: Mapped[Offer] = relationship(back_populates="requirements")


class Application(Base):
    __tablename__ = "applications"
    __table_args__ = (UniqueConstraint("candidate_id", "offer_id", name="uq_application_candidate_offer"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    candidate_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    offer_id: Mapped[int] = mapped_column(ForeignKey("offers.id", ondelete="CASCADE"), nullable=False)
    applied_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    status: Mapped[ApplicationStatus] = mapped_column(
        Enum(ApplicationStatus, name="application_status"),
        default=ApplicationStatus.SUBMITTED,
        nullable=False,
    )
    error_message: Mapped[str | None] = mapped_column(Text)

    candidate: Mapped["User"] = relationship(back_populates="applications")
    offer: Mapped[Offer] = relationship(back_populates="applications")
    documents: Mapped[list["Document"]] = relationship(back_populates="application", cascade="all, delete-orphan")
    profile: Mapped["ExtractedProfile | None"] = relationship(
        back_populates="application", uselist=False, cascade="all, delete-orphan"
    )
    verification: Mapped["DocumentVerification | None"] = relationship(
        back_populates="application", uselist=False, cascade="all, delete-orphan"
    )
    analysis: Mapped["AnalysisResult | None"] = relationship(
        back_populates="application", uselist=False, cascade="all, delete-orphan"
    )


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    application_id: Mapped[int] = mapped_column(
        ForeignKey("applications.id", ondelete="CASCADE"), nullable=False
    )
    document_type: Mapped[DocumentType] = mapped_column(Enum(DocumentType, name="document_type"), nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(1024), nullable=False)
    imported_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    application: Mapped[Application] = relationship(back_populates="documents")


class ExtractedProfile(Base):
    __tablename__ = "extracted_profiles"

    id: Mapped[int] = mapped_column(primary_key=True)
    application_id: Mapped[int] = mapped_column(
        ForeignKey("applications.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    content: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    extracted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    application: Mapped[Application] = relationship(back_populates="profile")


class DocumentVerification(Base):
    __tablename__ = "document_verifications"

    id: Mapped[int] = mapped_column(primary_key=True)
    application_id: Mapped[int] = mapped_column(
        ForeignKey("applications.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    diploma_info: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    cin_info: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    analyzed_documents: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    missing_documents: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    unreadable_documents: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    inconsistencies: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    compliance_level: Mapped[str | None] = mapped_column(String(30))
    coherence_score: Mapped[float | None] = mapped_column(Float)
    summary: Mapped[str | None] = mapped_column(Text)

    application: Mapped[Application] = relationship(back_populates="verification")


class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id: Mapped[int] = mapped_column(primary_key=True)
    application_id: Mapped[int] = mapped_column(
        ForeignKey("applications.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    global_score: Mapped[float | None] = mapped_column(Float)
    criterion_scores: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict, nullable=False)
    matching_skills: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    missing_skills: Mapped[list[str]] = mapped_column(JSONB, default=list, nullable=False)
    diploma_compliant: Mapped[bool | None] = mapped_column(Boolean)
    required_experience_years: Mapped[int | None] = mapped_column(Integer)
    report: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    indicative_opinion: Mapped[str | None] = mapped_column(String(30))
    analyzed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    application: Mapped[Application] = relationship(back_populates="analysis")


from app.models.user import User
