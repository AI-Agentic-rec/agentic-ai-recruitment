"""Énumérations du diagramme de classes (mêmes noms, mêmes valeurs).

Les valeurs sont stockées dans PostgreSQL sous forme de types ENUM (nom du type = nom en snake_case).
"""
from enum import StrEnum


class RoleUtilisateur(StrEnum):
    ADMIN = "ADMIN"
    CANDIDAT = "CANDIDAT"


class StatutOffre(StrEnum):
    BROUILLON = "BROUILLON"
    PUBLIEE = "PUBLIEE"
    CLOTUREE = "CLOTUREE"


class StatutCandidature(StrEnum):
    ENVOYEE = "ENVOYEE"
    EN_ATTENTE_DE_TRAITEMENT = "EN_ATTENTE_DE_TRAITEMENT"
    EN_COURS_DE_TRAITEMENT = "EN_COURS_DE_TRAITEMENT"
    ANALYSE_TERMINEE = "ANALYSE_TERMINEE"
    ERREUR_DE_TRAITEMENT = "ERREUR_DE_TRAITEMENT"


class TypeDocument(StrEnum):
    CV = "CV"
    DIPLOME = "DIPLOME"
    CIN = "CIN"


class NiveauConformite(StrEnum):
    CONFORME = "CONFORME"
    PARTIELLEMENT_CONFORME = "PARTIELLEMENT_CONFORME"
    NON_CONFORME = "NON_CONFORME"


class AvisIndicatif(StrEnum):
    FAVORABLE = "FAVORABLE"
    DEFAVORABLE = "DEFAVORABLE"
    A_ETUDIER = "A_ETUDIER"


class Critere(StrEnum):
    """Les 6 critères de ResultatAnalyse.details. Stockés dans le JSON `details`, pas en colonne."""
    COMPETENCES_OBLIGATOIRES = "COMPETENCES_OBLIGATOIRES"
    EXPERIENCE = "EXPERIENCE"
    DIPLOME_FORMATION = "DIPLOME_FORMATION"
    COMPETENCES_SOUHAITEES = "COMPETENCES_SOUHAITEES"
    LANGUES = "LANGUES"
    COHERENCE_DOCUMENTS = "COHERENCE_DOCUMENTS"
