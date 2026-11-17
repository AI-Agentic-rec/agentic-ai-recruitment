"""Schéma aligné sur le diagramme de classes UML (v2).

Revision ID: 0002_schema_uml
Revises: 0001_initial_schema

Remplace les 8 tables de 0001 (noms anglais) par les 8 tables du diagramme :
utilisateur, offre, candidature, document, exigences_structurees, profil_candidat,
verification_documents, resultat_analyse. Les anciennes données de test sont supprimées
(le projet ne contient que des données fictives : relancer le seed).
"""
import importlib.util
from pathlib import Path
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0002_schema_uml"
down_revision: Union[str, None] = "0001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

OLD_TABLES = ["analysis_results", "document_verifications", "extracted_profiles", "documents",
              "applications", "offer_requirements", "offers", "users"]
OLD_ENUMS = ["user_role", "offer_status", "application_status", "document_type"]

NEW_TABLES = ["resultat_analyse", "verification_documents", "profil_candidat", "document",
              "candidature", "exigences_structurees", "offre", "utilisateur"]
NEW_ENUMS = {
    "role_utilisateur": ("ADMIN", "CANDIDAT"),
    "statut_offre": ("BROUILLON", "PUBLIEE", "CLOTUREE"),
    "statut_candidature": ("ENVOYEE", "EN_ATTENTE_DE_TRAITEMENT", "EN_COURS_DE_TRAITEMENT",
                           "ANALYSE_TERMINEE", "ERREUR_DE_TRAITEMENT"),
    "type_document": ("CV", "DIPLOME", "CIN"),
    "niveau_conformite": ("CONFORME", "PARTIELLEMENT_CONFORME", "NON_CONFORME"),
    "avis_indicatif": ("FAVORABLE", "DEFAVORABLE", "A_ETUDIER"),
}


def _enum(name: str) -> postgresql.ENUM:
    return postgresql.ENUM(*NEW_ENUMS[name], name=name, create_type=False)


def _liste(name: str) -> sa.Column:
    return sa.Column(name, postgresql.JSONB, nullable=False, server_default=sa.text("'[]'::jsonb"))


def upgrade() -> None:
    for table in OLD_TABLES:
        op.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
    for enum in OLD_ENUMS:
        op.execute(f"DROP TYPE IF EXISTS {enum}")
    for name, values in NEW_ENUMS.items():
        postgresql.ENUM(*values, name=name).create(op.get_bind(), checkfirst=True)

    op.create_table(
        "utilisateur",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("nom", sa.String(100), nullable=False),
        sa.Column("prenom", sa.String(100), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("mot_de_passe_hash", sa.String(255), nullable=False),
        sa.Column("role", _enum("role_utilisateur"), nullable=False, server_default="CANDIDAT"),
        sa.Column("telephone", sa.String(30)),
    )
    op.create_index("ix_utilisateur_email", "utilisateur", ["email"], unique=True)

    op.create_table(
        "offre",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("id_admin", sa.Integer, sa.ForeignKey("utilisateur.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("titre", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=False),
        sa.Column("diplome_demande", sa.String(255)),
        sa.Column("experience_annees", sa.Float),
        _liste("competences_obligatoires"),
        _liste("competences_souhaitees"),
        _liste("langues"),
        sa.Column("localisation", sa.String(255)),
        sa.Column("statut", _enum("statut_offre"), nullable=False, server_default="BROUILLON"),
        sa.Column("date_creation", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("date_publication", sa.DateTime(timezone=True)),
        sa.Column("date_cloture", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_offre_id_admin", "offre", ["id_admin"])
    op.create_index("ix_offre_statut", "offre", ["statut"])

    op.create_table(
        "candidature",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("id_candidat", sa.Integer, sa.ForeignKey("utilisateur.id", ondelete="CASCADE"), nullable=False),
        sa.Column("id_offre", sa.Integer, sa.ForeignKey("offre.id", ondelete="CASCADE"), nullable=False),
        sa.Column("date_candidature", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("statut", _enum("statut_candidature"), nullable=False, server_default="ENVOYEE"),
        sa.Column("message_erreur", sa.Text),
        sa.UniqueConstraint("id_candidat", "id_offre", name="uq_candidature_candidat_offre"),
    )
    op.create_index("ix_candidature_id_candidat", "candidature", ["id_candidat"])
    op.create_index("ix_candidature_id_offre", "candidature", ["id_offre"])
    op.create_index("ix_candidature_statut", "candidature", ["statut"])

    op.create_table(
        "document",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("id_candidature", sa.Integer, sa.ForeignKey("candidature.id", ondelete="CASCADE"), nullable=False),
        sa.Column("type", _enum("type_document"), nullable=False),
        sa.Column("chemin_fichier", sa.String(1024), nullable=False),
        sa.Column("date_import", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("id_candidature", "type", name="uq_document_candidature_type"),
    )
    op.create_index("ix_document_id_candidature", "document", ["id_candidature"])

    op.create_table(  # Agent 1
        "exigences_structurees",
        sa.Column("id_offre", sa.Integer, sa.ForeignKey("offre.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("titre_poste", sa.String(255)),
        sa.Column("diplome_demande", sa.String(255)),
        sa.Column("niveau_diplome_min", sa.Integer),
        sa.Column("experience_min_annees", sa.Float, nullable=False, server_default="0"),
        _liste("competences_obligatoires"),
        _liste("competences_souhaitees"),
        _liste("langues"),
        _liste("missions"),
    )

    op.create_table(  # Agent 2
        "profil_candidat",
        sa.Column("id_candidature", sa.Integer, sa.ForeignKey("candidature.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("nom", sa.String(100)),
        sa.Column("prenom", sa.String(100)),
        sa.Column("email", sa.String(255)),
        sa.Column("telephone", sa.String(50)),
        _liste("formations"),
        _liste("experiences"),
        _liste("competences"),
        _liste("langues"),
        _liste("certifications"),
        sa.Column("experience_totale_annees", sa.Float, nullable=False, server_default="0"),
    )

    op.create_table(  # Agent 3
        "verification_documents",
        sa.Column("id_candidature", sa.Integer, sa.ForeignKey("candidature.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("infos_diplome", postgresql.JSONB),
        sa.Column("infos_cin", postgresql.JSONB),
        _liste("documents_analyses"),
        _liste("documents_manquants"),
        _liste("documents_illisibles"),
        _liste("incoherences"),
        sa.Column("niveau_conformite", _enum("niveau_conformite"), nullable=False),
        sa.Column("score_coherence", sa.Integer, nullable=False),
        sa.Column("resume", sa.Text, nullable=False, server_default=""),
    )

    op.create_table(  # Agents 4 et 5
        "resultat_analyse",
        sa.Column("id_candidature", sa.Integer, sa.ForeignKey("candidature.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("score_global", sa.Float, nullable=False),
        _liste("details"),
        _liste("competences_correspondantes"),
        _liste("competences_manquantes"),
        sa.Column("diplome_conforme", sa.Boolean, nullable=False),
        sa.Column("experience_candidat_annees", sa.Float, nullable=False, server_default="0"),
        sa.Column("rapport", postgresql.JSONB),
        sa.Column("avis_indicatif", _enum("avis_indicatif")),
        sa.Column("date_analyse", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    for table in NEW_TABLES:
        op.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
    for enum in NEW_ENUMS:
        op.execute(f"DROP TYPE IF EXISTS {enum}")
    # Recrée l'ancien schéma en rejouant la migration 0001.
    chemin = Path(__file__).with_name("0001_initial_schema.py")
    spec = importlib.util.spec_from_file_location("migration_0001", chemin)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.upgrade()
