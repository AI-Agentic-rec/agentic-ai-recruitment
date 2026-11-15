"""
AGENT 5 : REPORT (semaine 2, version complète appelée par l'orchestrateur)

Génère le `RapportCandidature` final à partir des sorties des agents 1 à 4.

    from agents.agent5_report.agent5 import executer_agent5
    rapport = executer_agent5({"agent1": a1, "agent2": a2, "agent3": a3, "agent4": a4})

Par rapport au prototype (agent5_prototype.py), l'agent complet ajoute :
- la validation des entrées (objets Pydantic ou dictionnaires JSON) avec des erreurs sans donnée personnelle ;
- le REPLI : si le modèle est indisponible ou répond de façon invalide, un résumé et une conclusion sont rédigés
  par gabarit à partir des mêmes faits, et le rapport reste valide (la trace indique `redaction="repli"`) ;
- le point d'entrée `executer_agent5` pour l'orchestrateur, et des logs sans donnée personnelle.

Règles métier garanties (testées dans test_agent5.py) :
1. le code assemble les faits ; le modèle ne rédige que résumé et conclusion ;
2. score et détail du score repris à l'identique de l'Agent 4 (jamais recalculés) ;
3. aucun CIN envoyé au modèle ni écrit dans les logs ;
4. la décision finale appartient toujours au recruteur ; l'avis est indicatif.
"""
import logging
from dataclasses import dataclass, field
from typing import Any, Literal, Mapping, Optional, Type

from pydantic import BaseModel, ValidationError

from agents.agent5_report.agent5_prototype import (DECISION_FINALE, PreparationRapport, RedactionLLM,
                                                   construire_rapport, fmt, preparer_rapport,
                                                   rediger_resume_conclusion)
from agents.agent5_report.erreurs_agent5 import (Agent5Error, EntreeInvalideError, ErreurLLM,
                                                 RapportInvalideError, RedactionInvalideError)
from agents.common.schemas import (ContexteCandidature, ExigencesStructurees, ProfilCandidat, RapportCandidature,
                                   ResultatMatching, VerificationDocuments)

logger = logging.getLogger("agents.agent5")


@dataclass
class TraceAgent5:
    """Comment le rapport a été produit (utile pour l'orchestrateur et les logs)."""
    redaction: Literal["llm", "repli"]
    avertissements: list[str] = field(default_factory=list)
    cause_repli: Optional[str] = None


# ---------------------------------------------------------------- validation des entrées
def _resume_erreurs(exc: ValidationError) -> str:
    """Emplacement et message de chaque erreur, SANS les valeurs saisies (elles peuvent contenir des données sensibles)."""
    return "; ".join(f"{'.'.join(str(p) for p in e['loc']) or '(racine)'} : {e['msg']}" for e in exc.errors())


def valider_entree(valeur: Any, schema: Type[BaseModel], nom: str, *, obligatoire: bool = True):
    """Accepte une instance du schéma, une autre instance Pydantic ou un dictionnaire ; sinon EntreeInvalideError."""
    if valeur is None:
        if obligatoire:
            raise EntreeInvalideError(f"Entrée manquante : {nom} ({schema.__name__}).")
        return None
    if isinstance(valeur, schema):
        return valeur
    if isinstance(valeur, BaseModel):                      # ex. une instance d'une ancienne copie des schémas
        valeur = valeur.model_dump()
    if not isinstance(valeur, Mapping):
        raise EntreeInvalideError(f"Entrée invalide : {nom} doit être un {schema.__name__} ou un dictionnaire "
                                  f"(reçu : {type(valeur).__name__}).")
    try:
        return schema.model_validate(dict(valeur))
    except ValidationError as exc:
        raise EntreeInvalideError(f"Entrée invalide : {nom} ne respecte pas {schema.__name__} "
                                  f"({_resume_erreurs(exc)}).") from None


# ---------------------------------------------------------------- repli (rédaction par gabarit)
def _poste(prep: PreparationRapport) -> str:
    return f"le poste de {prep.titre_poste}" if prep.titre_poste else "le poste proposé"


def rediger_repli(prep: PreparationRapport) -> RedactionLLM:
    """Résumé et conclusion écrits par le CODE, à partir des seuls faits établis (aucune invention possible)."""
    n_f, n_m, n_i = len(prep.points_forts), len(prep.points_manquants), len(prep.incoherences)
    resume = (f"{prep.nom_candidat} obtient {fmt(prep.score_global)}/100 pour {_poste(prep)}. "
              f"{n_f} point(s) fort(s) et {n_m} point(s) manquant(s) ont été identifiés")
    resume += (f", ainsi que {n_i} incohérence(s) entre les documents." if n_i else ", sans incohérence détectée entre les documents.")

    if prep.avis_indicatif == "favorable":
        corps = ("Le score et l'absence d'incohérence grave indiquent un profil globalement adapté au poste ; "
                 "les points manquants pourront être vérifiés en entretien.")
    elif prep.avis_indicatif == "defavorable":
        corps = "Le profil correspond faiblement aux exigences du poste d'après les critères évalués."
    else:
        raisons = []
        if any(i.gravite == "elevee" for i in prep.incoherences):
            raisons.append("des incohérences de gravité élevée ont été détectées entre les documents")
        if any(d.critere == "competences_obligatoires" and d.score == 0 for d in prep.justification_score):
            raisons.append("aucune compétence obligatoire n'est identifiée")
        raisons = raisons or ["le score se situe dans une zone intermédiaire"]
        corps = (f"Le dossier nécessite un examen approfondi : {' ; '.join(raisons)}. "
                 "Une vérification manuelle est recommandée avant toute conclusion.")
    return RedactionLLM(resume=resume, conclusion=f"{corps} Cet avis est indicatif. {DECISION_FINALE}")


# ---------------------------------------------------------------- agent complet
def generer_rapport_avec_trace(exigences: Any, profil: Any, verification: Any, matching: Any, *,
                               contexte: Optional[ContexteCandidature] = None, llm=None,
                               repli: bool = True) -> tuple[RapportCandidature, TraceAgent5]:
    """Produit le rapport et sa trace. `verification` peut être None (l'Agent 4 le tolère) ; les trois autres sont
    obligatoires. Si `repli` est False, une erreur du modèle est levée au lieu d'être remplacée par le gabarit."""
    ids = f"candidate_id={contexte.candidate_id} job_id={contexte.job_id}" if contexte else "candidature=?"
    logger.info("Agent 5 : début (%s)", ids)

    a1 = valider_entree(exigences, ExigencesStructurees, "agent1 (exigences)")
    a2 = valider_entree(profil, ProfilCandidat, "agent2 (profil)")
    a3 = valider_entree(verification, VerificationDocuments, "agent3 (vérification)", obligatoire=False)
    a4 = valider_entree(matching, ResultatMatching, "agent4 (matching)")

    prep = preparer_rapport(a1, a2, a3, a4)           # peut lever FuiteDonneesSensiblesError : jamais masquée par le repli
    trace = TraceAgent5(redaction="llm", avertissements=list(prep.avertissements))
    for a in prep.avertissements:
        logger.warning("Agent 5 : %s (%s)", a, ids)

    try:
        redaction = rediger_resume_conclusion(prep, llm=llm)
    except (ErreurLLM, RedactionInvalideError) as exc:
        if not repli:
            raise
        logger.warning("Agent 5 : repli par gabarit (%s) : %s", ids, exc)
        redaction = rediger_repli(prep)
        trace.redaction, trace.cause_repli = "repli", f"{type(exc).__name__}: {exc}"

    try:
        rapport = construire_rapport(prep, redaction)
    except ValidationError as exc:
        raise RapportInvalideError(f"Le rapport ne respecte pas RapportCandidature ({_resume_erreurs(exc)}).") from None

    logger.info("Agent 5 : rapport généré (%s) score=%s avis=%s rédaction=%s", ids, fmt(rapport.score_global),
                rapport.avis_indicatif, trace.redaction)
    return rapport, trace


def generer_rapport(exigences: Any, profil: Any, verification: Any, matching: Any, *,
                    contexte: Optional[ContexteCandidature] = None, llm=None, repli: bool = True) -> RapportCandidature:
    return generer_rapport_avec_trace(exigences, profil, verification, matching,
                                      contexte=contexte, llm=llm, repli=repli)[0]


def executer_agent5(sorties: Mapping[str, Any], *, contexte: Optional[ContexteCandidature] = None, llm=None,
                    repli: bool = True) -> RapportCandidature:
    """Point d'entrée de l'orchestrateur. `sorties` = {"agent1": ..., "agent2": ..., "agent3": ..., "agent4": ...}
    (objets Pydantic ou dictionnaires). Lève une `Agent5Error` (message sans donnée personnelle) en cas d'échec :
    l'orchestrateur la convertit en statut « Erreur de traitement »."""
    if not isinstance(sorties, Mapping):
        raise EntreeInvalideError("Les sorties des agents doivent être fournies sous forme de dictionnaire.")
    return generer_rapport(sorties.get("agent1"), sorties.get("agent2"), sorties.get("agent3"), sorties.get("agent4"),
                           contexte=contexte, llm=llm, repli=repli)


if __name__ == "__main__":
    import argparse
    from agents.agent5_report.agent5_prototype import charger_chaine
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s : %(message)s")
    ap = argparse.ArgumentParser(description="Agent 5 : génère le rapport sur les mocks de data/mocks/")
    ap.add_argument("--cas", choices=("conforme", "incoherent"), default="incoherent")
    ap.add_argument("--sans-modele", action="store_true", help="n'appelle pas le modèle : rédaction par gabarit")
    args = ap.parse_args()
    a1, a2, a3, a4, _ = charger_chaine(args.cas)

    def _sans_modele(*_):
        raise ErreurLLM("Modèle désactivé (--sans-modele).")
    try:
        rapport, trace = generer_rapport_avec_trace(a1, a2, a3, a4, llm=_sans_modele if args.sans_modele else None)
    except Agent5Error as exc:
        raise SystemExit(f"ERREUR Agent 5 : {exc}")
    print(f"# rédaction : {trace.redaction}" + (f" ({trace.cause_repli})" if trace.cause_repli else ""))
    print(rapport.model_dump_json(indent=2))
