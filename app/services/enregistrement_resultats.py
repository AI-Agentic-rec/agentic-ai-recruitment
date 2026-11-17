"""Enregistrement des résultats des agents en base (4 tables).

| Agent     | Contrat (agents/common/schemas.py)      | Table                    | Clé primaire   |
|-----------|-----------------------------------------|--------------------------|----------------|
| Agent 1   | ExigencesStructurees                    | exigences_structurees    | id_offre       |
| Agent 2   | ProfilCandidat                          | profil_candidat          | id_candidature |
| Agent 3   | VerificationDocuments                   | verification_documents   | id_candidature |
| Agents 4+5| ResultatMatching + RapportCandidature   | resultat_analyse         | id_candidature |

Utilisation (orchestrateur) :

    from app.services import enregistrer_exigences_structurees, enregistrer_resultats_candidature

    enregistrer_exigences_structurees(db, id_offre, sortie_agent1)
    enregistrer_resultats_candidature(db, id_candidature,
                                      profil=a2, verification=a3, matching=a4, rapport=a5)
    # en cas d'échec d'un agent :
    enregistrer_erreur_traitement(db, id_candidature, "Ollama indisponible")

Règles :
- Chaque fonction accepte un modèle Pydantic OU le dict JSON brut d'un agent ; il est validé avec le
  contrat avant écriture. Sortie invalide -> ``pydantic.ValidationError`` et RIEN n'est écrit.
- Relancer une analyse REMPLACE le résultat précédent (une ligne par offre / candidature).
- ``commit=True`` par défaut ; ``commit=False`` laisse l'appelant gérer la transaction.
  ``enregistrer_resultats_candidature`` écrit les 3 tables candidature en une transaction (tout ou rien).
- Le numéro de CIN (donnée sensible) est masqué avant stockage.
"""
from typing import Any, TypeVar

from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from agents.common import schemas as agent_schemas
from app import models

M = TypeVar("M", bound=BaseModel)

ENTREE_AGENT = dict[str, Any]


class CandidatureIntrouvableError(LookupError):
    """La candidature n'existe pas."""


class OffreIntrouvableError(LookupError):
    """L'offre n'existe pas."""


# ---------------------------------------------------------------- utilitaires

def _valider(contrat: type[M], donnees: M | ENTREE_AGENT) -> M:
    """Valide la sortie d'un agent (dict brut ou objet) avec son contrat."""
    if isinstance(donnees, contrat):
        return contrat.model_validate(donnees.model_dump())  # protège contre model_construct()
    return contrat.model_validate(donnees)


def _json(objet: BaseModel) -> dict[str, Any]:
    """Dict sérialisable en JSON, requis par les colonnes JSONB."""
    return objet.model_dump(mode="json")


def _masquer_cin(numero: str | None) -> str | None:
    if not numero:
        return numero
    numero = numero.strip()
    return "*" * len(numero) if len(numero) <= 3 else "*" * (len(numero) - 3) + numero[-3:]


def _candidature(db: Session, id_candidature: int) -> models.Candidature:
    candidature = db.get(models.Candidature, id_candidature)
    if candidature is None:
        raise CandidatureIntrouvableError(f"Candidature introuvable : {id_candidature}")
    return candidature


def _offre(db: Session, id_offre: int) -> models.Offre:
    offre = db.get(models.Offre, id_offre)
    if offre is None:
        raise OffreIntrouvableError(f"Offre introuvable : {id_offre}")
    return offre


def _ecrire(db: Session, table: type, cle: int, valeurs: dict[str, Any], commit: bool) -> Any:
    """Insère la ligne, ou la remplace si elle existe (clé primaire = id_offre / id_candidature)."""
    ligne = db.get(table, cle)
    if ligne is None:
        ligne = table(**{_nom_cle(table): cle}, **valeurs)
        db.add(ligne)
    else:
        for champ, valeur in valeurs.items():
            setattr(ligne, champ, valeur)
    if commit:
        db.commit()
        db.refresh(ligne)
    else:
        db.flush()
    return ligne


def _nom_cle(table: type) -> str:
    return "id_offre" if table is models.ExigencesStructurees else "id_candidature"


# ---------------------------------------------------------------- Agent 1

def enregistrer_exigences_structurees(
    db: Session, id_offre: int, exigences: agent_schemas.ExigencesStructurees | ENTREE_AGENT, *, commit: bool = True
) -> models.ExigencesStructurees:
    exigences = _valider(agent_schemas.ExigencesStructurees, exigences)
    _offre(db, id_offre)
    valeurs = _json(exigences)
    valeurs.pop("id_offre", None)  # la clé vient de l'argument, pas de la sortie de l'agent
    return _ecrire(db, models.ExigencesStructurees, id_offre, valeurs, commit)


# ---------------------------------------------------------------- Agent 2

def enregistrer_profil_candidat(
    db: Session, id_candidature: int, profil: agent_schemas.ProfilCandidat | ENTREE_AGENT, *, commit: bool = True
) -> models.ProfilCandidat:
    profil = _valider(agent_schemas.ProfilCandidat, profil)
    _candidature(db, id_candidature)
    valeurs = _json(profil)
    valeurs.pop("id_candidature", None)
    return _ecrire(db, models.ProfilCandidat, id_candidature, valeurs, commit)


# ---------------------------------------------------------------- Agent 3

def enregistrer_verification_documents(
    db: Session,
    id_candidature: int,
    verification: agent_schemas.VerificationDocuments | ENTREE_AGENT,
    *,
    commit: bool = True,
) -> models.VerificationDocuments:
    v = _valider(agent_schemas.VerificationDocuments, verification)
    _candidature(db, id_candidature)

    infos_cin = _json(v.infos_cin) if v.infos_cin else None
    if infos_cin is not None:
        infos_cin["numero_cin"] = _masquer_cin(infos_cin.get("numero_cin"))

    valeurs = dict(
        infos_diplome=_json(v.infos_diplome) if v.infos_diplome else None,
        infos_cin=infos_cin,
        documents_analyses=list(v.documents_analyses),
        documents_manquants=list(v.documents_manquants),
        documents_illisibles=list(v.documents_illisibles),
        incoherences=[_json(i) for i in v.incoherences],
        niveau_conformite=models.NiveauConformite(v.niveau_conformite.upper()),
        score_coherence=v.score_coherence,
        resume=v.resume,
    )
    return _ecrire(db, models.VerificationDocuments, id_candidature, valeurs, commit)


# ---------------------------------------------------------------- Agents 4 + 5

def enregistrer_resultat_analyse(
    db: Session,
    id_candidature: int,
    matching: agent_schemas.ResultatMatching | ENTREE_AGENT,
    rapport: agent_schemas.RapportCandidature | ENTREE_AGENT | None = None,
    *,
    commit: bool = True,
) -> models.ResultatAnalyse:
    """Matching (agent 4) et, quand il existe, rapport (agent 5) dans la même ligne.

    Le rapport peut arriver plus tard : rappeler la fonction avec le même matching et le rapport.
    Sans rapport, un rapport déjà enregistré est conservé.
    """
    m = _valider(agent_schemas.ResultatMatching, matching)
    r = _valider(agent_schemas.RapportCandidature, rapport) if rapport is not None else None
    _candidature(db, id_candidature)

    valeurs: dict[str, Any] = dict(
        score_global=m.score_global,
        details=[_json(d) for d in m.details],
        competences_correspondantes=list(m.competences_correspondantes),
        competences_manquantes=list(m.competences_manquantes),
        diplome_conforme=m.diplome_conforme,
        experience_candidat_annees=m.experience_candidat_annees,
        date_analyse=func.now(),
    )
    if r is not None:
        valeurs["rapport"] = _json(r)
        valeurs["avis_indicatif"] = models.AvisIndicatif(r.avis_indicatif.upper())
    return _ecrire(db, models.ResultatAnalyse, id_candidature, valeurs, commit)


# ---------------------------------------------------------------- orchestration

def enregistrer_resultats_candidature(
    db: Session,
    id_candidature: int,
    *,
    profil: agent_schemas.ProfilCandidat | ENTREE_AGENT,
    verification: agent_schemas.VerificationDocuments | ENTREE_AGENT,
    matching: agent_schemas.ResultatMatching | ENTREE_AGENT,
    rapport: agent_schemas.RapportCandidature | ENTREE_AGENT | None = None,
) -> dict[str, Any]:
    """Écrit profil_candidat, verification_documents et resultat_analyse en UNE transaction.

    En cas de succès : statut de la candidature = ANALYSE_TERMINEE et message_erreur effacé.
    En cas d'erreur : rollback complet (rien n'est écrit) puis l'exception est relancée.
    """
    try:
        lignes = {
            "profil": enregistrer_profil_candidat(db, id_candidature, profil, commit=False),
            "verification": enregistrer_verification_documents(db, id_candidature, verification, commit=False),
            "resultat": enregistrer_resultat_analyse(db, id_candidature, matching, rapport, commit=False),
        }
        candidature = _candidature(db, id_candidature)
        candidature.statut = models.StatutCandidature.ANALYSE_TERMINEE
        candidature.message_erreur = None
        db.commit()
    except Exception:
        db.rollback()
        raise
    for ligne in lignes.values():
        db.refresh(ligne)
    return lignes


def enregistrer_erreur_traitement(db: Session, id_candidature: int, message: str) -> models.Candidature:
    """Garde la trace d'un échec : statut ERREUR_DE_TRAITEMENT + message_erreur."""
    candidature = _candidature(db, id_candidature)
    candidature.statut = models.StatutCandidature.ERREUR_DE_TRAITEMENT
    candidature.message_erreur = message[:2000]
    db.commit()
    return candidature
