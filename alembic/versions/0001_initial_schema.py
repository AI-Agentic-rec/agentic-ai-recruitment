"""Create recruitment schema.

Revision ID: 0001_initial_schema
Revises:
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    user_role = sa.Enum("ADMIN", "RECRUITER", "CANDIDATE", name="user_role")
    offer_status = sa.Enum("DRAFT", "PUBLISHED", "CLOSED", name="offer_status")
    application_status = sa.Enum("SUBMITTED", "IN_REVIEW", "ACCEPTED", "REJECTED", name="application_status")
    document_type = sa.Enum("CV", "DIPLOMA", "CIN", name="document_type")
    for enum in (user_role, offer_status, application_status, document_type):
        enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("first_name", sa.String(100), nullable=False),
        sa.Column("last_name", sa.String(100), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("role", user_role, nullable=False),
        sa.Column("phone", sa.String(30)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_table(
        "offers",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("creator_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("diploma_required", sa.String(255)),
        sa.Column("experience_years", sa.Integer()),
        sa.Column("required_skills", postgresql.JSONB(), nullable=False),
        sa.Column("desired_skills", postgresql.JSONB(), nullable=False),
        sa.Column("languages", postgresql.JSONB(), nullable=False),
        sa.Column("location", sa.String(255)),
        sa.Column("status", offer_status, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True)),
        sa.Column("closed_at", sa.DateTime(timezone=True)),
    )
    op.create_table(
        "offer_requirements",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("offer_id", sa.Integer(), sa.ForeignKey("offers.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("content", postgresql.JSONB(), nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_table(
        "applications",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("candidate_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("offer_id", sa.Integer(), sa.ForeignKey("offers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("applied_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("status", application_status, nullable=False),
        sa.Column("error_message", sa.Text()),
        sa.UniqueConstraint("candidate_id", "offer_id", name="uq_application_candidate_offer"),
    )
    op.create_table(
        "documents",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("application_id", sa.Integer(), sa.ForeignKey("applications.id", ondelete="CASCADE"), nullable=False),
        sa.Column("document_type", document_type, nullable=False),
        sa.Column("file_name", sa.String(255), nullable=False),
        sa.Column("file_path", sa.String(1024), nullable=False),
        sa.Column("imported_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_table(
        "extracted_profiles",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("application_id", sa.Integer(), sa.ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("content", postgresql.JSONB(), nullable=False),
        sa.Column("extracted_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_table(
        "document_verifications",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("application_id", sa.Integer(), sa.ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("diploma_info", postgresql.JSONB()),
        sa.Column("cin_info", postgresql.JSONB()),
        sa.Column("analyzed_documents", postgresql.JSONB(), nullable=False),
        sa.Column("missing_documents", postgresql.JSONB(), nullable=False),
        sa.Column("unreadable_documents", postgresql.JSONB(), nullable=False),
        sa.Column("inconsistencies", postgresql.JSONB(), nullable=False),
        sa.Column("compliance_level", sa.String(30)),
        sa.Column("coherence_score", sa.Float()),
        sa.Column("summary", sa.Text()),
    )
    op.create_table(
        "analysis_results",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("application_id", sa.Integer(), sa.ForeignKey("applications.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("global_score", sa.Float()),
        sa.Column("criterion_scores", postgresql.JSONB(), nullable=False),
        sa.Column("matching_skills", postgresql.JSONB(), nullable=False),
        sa.Column("missing_skills", postgresql.JSONB(), nullable=False),
        sa.Column("diploma_compliant", sa.Boolean()),
        sa.Column("required_experience_years", sa.Integer()),
        sa.Column("report", postgresql.JSONB()),
        sa.Column("indicative_opinion", sa.String(30)),
        sa.Column("analyzed_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    for table in (
        "analysis_results",
        "document_verifications",
        "extracted_profiles",
        "documents",
        "applications",
        "offer_requirements",
        "offers",
        "users",
    ):
        op.drop_table(table)
    for enum_name in ("document_type", "application_status", "offer_status", "user_role"):
        sa.Enum(name=enum_name).drop(op.get_bind(), checkfirst=True)
