"""Modèles SQLAlchemy = classes du diagramme de classes (mêmes noms, mêmes attributs).

Utilisateur, Offre, Candidature, Document          -> gestion
ExigencesStructurees, ProfilCandidat,
VerificationDocuments, ResultatAnalyse             -> résultats des agents 1 à 5
"""
from app.models.enums import (
    AvisIndicatif,
    Critere,
    NiveauConformite,
    RoleUtilisateur,
    StatutCandidature,
    StatutOffre,
    TypeDocument,
)
from app.models.recrutement import Candidature, Document, Offre
from app.models.resultats_agents import (
    ExigencesStructurees,
    ProfilCandidat,
    ResultatAnalyse,
    VerificationDocuments,
)
from app.models.utilisateur import Utilisateur

__all__ = [
    "AvisIndicatif", "Candidature", "Critere", "Document", "ExigencesStructurees", "NiveauConformite",
    "Offre", "ProfilCandidat", "ResultatAnalyse", "RoleUtilisateur", "StatutCandidature", "StatutOffre",
    "TypeDocument", "Utilisateur", "VerificationDocuments",
]
