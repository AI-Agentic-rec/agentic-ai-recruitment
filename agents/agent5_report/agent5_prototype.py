"""
AGENT 5 : PROTOTYPE (semaine 1)  ->  tâches « Agent 5 : prompt et prototype du rapport sur JSON d'exemple » et
« gabarit du rapport (points forts, manques, incohérences, conclusion) »

Répartition (règle 1 du cahier des charges) :
- le CODE assemble les faits : points forts, points manquants, incohérences, justification du score, avis indicatif,
  mention de la décision humaine ; il reprend à l'identique le score et le détail de l'Agent 4 ;
- le MODÈLE rédige seulement le résumé et la conclusion, à partir de ces faits ; sa réponse est ensuite contrôlée
  (score cité exact, aucun nombre inventé, aucune décision de recrutement, aucun CIN).

Confidentialité (règle 3) : le message envoyé au modèle est construit par LISTE BLANCHE (nom, poste, score, faits
assemblés). `infos_cin` n'en fait jamais partie, et le numéro de CIN est masqué partout où il pourrait apparaître.

Entrées : ExigencesStructurees (A1), ProfilCandidat (A2), VerificationDocuments (A3, sans CIN), ResultatMatching (A4).
Sortie  : RapportCandidature (agents/common/schemas.py).
Semaine 2 (agent5.py) : validation des entrées, repli si le modèle échoue, intégration à l'orchestrateur.

Lancer (depuis la racine du dépôt) :
    python -m agents.agent5_report.agent5_prototype --sans-modele    (faits seuls, sans Ollama)
    python -m agents.agent5_report.agent5_prototype                  (avec le vrai modèle local Ollama)
"""
import json
import logging
import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict

from agents.agent5_report.erreurs_agent5 import FuiteDonneesSensiblesError, RedactionInvalideError
from agents.agent5_report.llm_adapter_agent5 import executer_redaction
from agents.agent5_report.prompts_agent5 import PROMPT_REDACTION
from agents.common.schemas import (DetailCritere, ExigencesStructurees, Incoherence, ProfilCandidat,
                                   RapportCandidature, ResultatMatching, VerificationDocuments)

logger = logging.getLogger("agents.agent5")

# ---------------------------------------------------------------- constantes métier
SEUIL_FAVORABLE = 75          # score >= 75 (et aucun blocage) -> « favorable »
SEUIL_DEFAVORABLE = 50        # score < 50 -> « defavorable »
SEUIL_POINT_FORT = 70         # un critère de compétences ou de cohérence est un point fort à partir de ce score
MAX_TENTATIVES_REDACTION = 2  # appels au modèle si sa rédaction viole une règle métier (en plus des 3 essais JSON)
LONGUEUR_MIN, LONGUEUR_MAX = 20, 900

# Source unique du rappel : la valeur par défaut du schéma
DECISION_FINALE = RapportCandidature.model_fields["decision_finale"].default

MASQUE_CIN = "[CIN masqué]"
_CIN_REGEX = re.compile(r"\b[A-Za-z]{1,2}\s?\d{5,8}\b")          # forme d'un numéro de CIN : 1-2 lettres + 5-8 chiffres
_SCORE_REGEX = re.compile(r"(\d+(?:[.,]\d+)?)\s*(?:/|sur)\s*100\b")
_NOMBRE_REGEX = re.compile(r"\d+(?:[.,]\d+)?")
_DECISION_REGEX = re.compile(
    r"\b(embauch\w*|nous recommandons (?:de )?(?:recruter|retenir|rejeter|refuser)|candidat (?:retenu|rejete|refuse|elimine)"
    r"|a (?:rejeter|refuser|retenir|embaucher)|doit etre (?:recrute|rejete|retenu|refuse))\b")
_RAPPEL_REGEX = re.compile(r"recruteur|responsable du recrutement|decision finale")
_MAJUSCULE_REGEX = re.compile(r"\b[A-ZÀ-ÖØ-Þ][\w+#.\-]{2,}")
_MOTS_AUTORISES = {"bac", "cv"}                # capitalisés courants, même s'ils ne figurent pas dans les faits


# ---------------------------------------------------------------- schéma de la réponse du modèle (interne)
class RedactionLLM(BaseModel):
    """Ce que le modèle doit renvoyer : deux textes, rien d'autre. Les clés en trop sont ignorées."""
    model_config = ConfigDict(extra="ignore")
    resume: str
    conclusion: str


@dataclass
class PreparationRapport:
    """Tout ce que le code a établi AVANT l'appel au modèle (aucune donnée sensible : pas de CIN)."""
    nom_candidat: str
    titre_poste: Optional[str]
    score_global: float
    avis_indicatif: str
    points_forts: list[str]
    points_manquants: list[str]
    incoherences: list[Incoherence]
    justification_score: list[DetailCritere]
    donnees_llm: dict
    message_llm: str
    avertissements: list[str] = field(default_factory=list)


# ---------------------------------------------------------------- utilitaires
def _norm(texte: Any) -> str:
    """Minuscules, sans accents, espaces simplifiés (comparaison de compétences)."""
    t = unicodedata.normalize("NFKD", str(texte or "")).encode("ascii", "ignore").decode()
    return " ".join(t.casefold().split())


def fmt(nombre: float) -> str:
    """85.3 -> '85.3' ; 100.0 -> '100'."""
    return f"{nombre:g}"


def _pl(n: int, singulier: str, pluriel: str) -> str:
    return singulier if n <= 1 else pluriel


def _ans(x: float) -> str:
    return "an" if x <= 1 else "ans"


def _dedoublonner(elements: list[str]) -> list[str]:
    return list(dict.fromkeys(elements))


def _detail(matching: ResultatMatching, critere: str) -> DetailCritere:
    return next(d for d in matching.details if d.critere == critere)     # les 6 critères sont garantis par le schéma


def _parmi(reference: list[str], trouves: list[str]) -> list[str]:
    """Éléments de `reference` (liste de l'offre) présents dans `trouves` (liste de l'Agent 4), casse/accents ignorés."""
    cibles = {_norm(t) for t in trouves}
    return [r for r in reference if _norm(r) in cibles]


# ---------------------------------------------------------------- confidentialité
def masquer_cin(texte: Any, numero_cin: Optional[str] = None) -> Any:
    """Remplace le numéro de CIN connu, puis tout motif ressemblant à un CIN, par [CIN masqué]."""
    if not isinstance(texte, str):
        return texte
    if numero_cin and numero_cin.strip():
        texte = re.sub(re.escape(numero_cin.strip()), MASQUE_CIN, texte, flags=re.IGNORECASE)
    return _CIN_REGEX.sub(MASQUE_CIN, texte)


def _masquer_exact(texte: str, numero_cin: Optional[str]) -> str:
    if numero_cin and numero_cin.strip():
        return re.sub(re.escape(numero_cin.strip()), MASQUE_CIN, texte, flags=re.IGNORECASE)
    return texte


def _masquer_recursif(objet: Any, numero_cin: Optional[str]) -> Any:
    if isinstance(objet, str):
        return masquer_cin(objet, numero_cin)
    if isinstance(objet, list):
        return [_masquer_recursif(o, numero_cin) for o in objet]
    if isinstance(objet, dict):
        return {k: _masquer_recursif(v, numero_cin) for k, v in objet.items()}
    return objet


def retirer_donnees_sensibles(verification: Optional[VerificationDocuments]):
    """Copie de l'Agent 3 SANS `infos_cin`, textes expurgés du CIN. Renvoie (copie, numéro_cin_connu).
    Le numéro n'est gardé que le temps de la préparation, pour vérifier qu'il ne fuit nulle part."""
    if verification is None:
        return None, None
    numero = verification.infos_cin.numero_cin if verification.infos_cin else None
    incoherences = [i.model_copy(update={"description": masquer_cin(i.description, numero)})
                    for i in verification.incoherences]
    propre = verification.model_copy(update={"infos_cin": None, "incoherences": incoherences,
                                             "resume": masquer_cin(verification.resume, numero)})
    return propre, numero


def verifier_absence_cin(texte: str, numero_cin: Optional[str]) -> None:
    """Dernier garde-fou avant l'envoi au modèle : lève FuiteDonneesSensiblesError si un CIN subsiste."""
    if numero_cin and numero_cin.strip() and numero_cin.strip().casefold() in texte.casefold():
        raise FuiteDonneesSensiblesError("Le numéro de CIN figure dans le message destiné au modèle : envoi bloqué.")
    if _CIN_REGEX.search(texte):
        raise FuiteDonneesSensiblesError("Un motif de numéro de CIN figure dans le message destiné au modèle : envoi bloqué.")


# ---------------------------------------------------------------- assemblage des faits (100 % code)
def _libelle_diplome(profil: ProfilCandidat, verification: Optional[VerificationDocuments]):
    d = verification.infos_diplome if verification else None
    if d and d.diplome:
        return " ".join(x for x in (d.diplome, d.specialite) if x), "vérifié"
    for f in profil.formations:
        if f.diplome:
            return " ".join(x for x in (f.diplome, f.specialite) if x), "déclaré dans le CV"
    return None, ""


def assembler_points_forts(exigences: ExigencesStructurees, profil: ProfilCandidat,
                           verification: Optional[VerificationDocuments], matching: ResultatMatching) -> list[str]:
    forts: list[str] = []

    obligatoires = exigences.competences_obligatoires
    ok_obl = _parmi(obligatoires, matching.competences_correspondantes)
    if ok_obl and _detail(matching, "competences_obligatoires").score >= SEUIL_POINT_FORT:
        forts.append(f"{len(ok_obl)} {_pl(len(ok_obl), 'compétence obligatoire', 'compétences obligatoires')} "
                     f"sur {len(obligatoires)} identifiée(s) : {', '.join(ok_obl)}")

    souhaitees = exigences.competences_souhaitees
    ok_sou = _parmi(souhaitees, matching.competences_correspondantes)
    if ok_sou:
        forts.append(f"{len(ok_sou)} {_pl(len(ok_sou), 'compétence souhaitée', 'compétences souhaitées')} "
                     f"sur {len(souhaitees)} identifiée(s) : {', '.join(ok_sou)}")

    exp, requise = matching.experience_candidat_annees, exigences.experience_min_annees
    if exp > 0 and _detail(matching, "experience").score >= 100:
        forts.append(f"{fmt(exp)} {_ans(exp)} d'expérience pour {fmt(requise)} demandé(s)" if requise > 0
                     else f"{fmt(exp)} {_ans(exp)} d'expérience (aucun minimum exigé)")

    niveau = exigences.niveau_diplome_min
    if niveau is not None and matching.diplome_conforme and _detail(matching, "diplome_formation").score >= 100:
        libelle, source = _libelle_diplome(profil, verification)
        forts.append(f"Diplôme conforme au niveau demandé (Bac+{niveau})" + (f" : {libelle} ({source})" if libelle else ""))

    if exigences.langues and _detail(matching, "langues").score >= 100:
        langues = ", ".join(f"{l.langue} ({l.niveau})" if l.niveau else l.langue for l in exigences.langues)
        forts.append(f"Langues conformes aux exigences : {langues}")

    if (verification is not None and not verification.incoherences
            and _detail(matching, "coherence_documents").score >= SEUIL_POINT_FORT):
        docs = f" ({', '.join(verification.documents_analyses)})" if verification.documents_analyses else ""
        forts.append(f"Documents analysés cohérents entre eux{docs}, score de cohérence "
                     f"{fmt(verification.score_coherence)}")
    return _dedoublonner(forts)


def assembler_points_manquants(exigences: ExigencesStructurees, verification: Optional[VerificationDocuments],
                               matching: ResultatMatching) -> list[str]:
    manques: list[str] = []

    manquantes = matching.competences_manquantes
    obl = _parmi(exigences.competences_obligatoires, manquantes)
    sou = _parmi(exigences.competences_souhaitees, manquantes)
    autres = [c for c in manquantes if _norm(c) not in {_norm(x) for x in obl + sou}]
    if obl:
        manques.append(f"{_pl(len(obl), 'Compétence obligatoire non identifiée', 'Compétences obligatoires non identifiées')}"
                       f" dans le CV : {', '.join(obl)}")
    if sou:
        manques.append(f"{_pl(len(sou), 'Compétence souhaitée non identifiée', 'Compétences souhaitées non identifiées')}"
                       f" dans le CV : {', '.join(sou)}")
    if autres:
        manques.append(f"{_pl(len(autres), 'Autre compétence manquante', 'Autres compétences manquantes')} : "
                       f"{', '.join(autres)}")

    requise, exp = exigences.experience_min_annees, matching.experience_candidat_annees
    if requise > 0 and _detail(matching, "experience").score < 100:
        manques.append(f"Expérience insuffisante : {fmt(exp)} {_ans(exp)} pour {fmt(requise)} demandé(s)")

    if exigences.niveau_diplome_min is not None and not matching.diplome_conforme:
        manques.append(f"Diplôme non conforme : {_detail(matching, 'diplome_formation').justification}")

    if exigences.langues and _detail(matching, "langues").score < 100:
        manques.append("Exigences linguistiques non pleinement satisfaites : "
                       f"{_detail(matching, 'langues').justification}")

    if verification is None:
        manques.append("Vérification des documents non disponible : cohérence des documents non évaluée")
    else:
        if verification.documents_manquants:
            manques.append(f"Document(s) attendu(s) non fourni(s) : {', '.join(verification.documents_manquants)}")
        if verification.documents_illisibles:
            manques.append(f"Document(s) illisible(s), non analysé(s) : {', '.join(verification.documents_illisibles)}")
    return _dedoublonner(manques)


def assembler_incoherences(verification: Optional[VerificationDocuments]) -> list[Incoherence]:
    """Reprise à l'identique des incohérences de l'Agent 3 (déjà expurgées du CIN par `retirer_donnees_sensibles`)."""
    return [i.model_copy(deep=True) for i in verification.incoherences] if verification else []


def determiner_avis(matching: ResultatMatching, incoherences: list[Incoherence]) -> str:
    """favorable : score >= 75 sans incohérence élevée ni compétences obligatoires à 0 ; defavorable : score < 50 ;
    a_etudier : tous les autres cas. Règle déterministe, jamais laissée au modèle."""
    score = matching.score_global
    if score < SEUIL_DEFAVORABLE:
        return "defavorable"
    bloque = (any(i.gravite == "elevee" for i in incoherences)
              or _detail(matching, "competences_obligatoires").score == 0)
    return "favorable" if score >= SEUIL_FAVORABLE and not bloque else "a_etudier"


def reprendre_justification(matching: ResultatMatching, numero_cin: Optional[str] = None) -> list[DetailCritere]:
    """Copie STRICTEMENT identique du détail de l'Agent 4 (jamais recalculé). Seule exception : si le numéro de CIN
    figurait par erreur dans une justification, il est masqué."""
    copie = []
    for d in matching.details:
        justification = _masquer_exact(d.justification, numero_cin)
        copie.append(d.model_copy(deep=True, update={"justification": justification})
                     if justification != d.justification else d.model_copy(deep=True))
    return copie


# ---------------------------------------------------------------- préparation du message destiné au modèle
def construire_donnees_llm(nom: str, titre: Optional[str], score: float, avis: str, forts: list[str],
                           manques: list[str], incoherences: list[Incoherence],
                           verification: Optional[VerificationDocuments], matching: ResultatMatching) -> dict:
    """LISTE BLANCHE : seuls ces champs sont transmis au modèle. Ni CIN, ni date de naissance, ni email, ni téléphone."""
    return {
        "candidat": nom,
        "poste": titre,
        "score_global": score,
        "avis_indicatif": avis,
        "points_forts": forts,
        "points_manquants": manques,
        "incoherences": [{"gravite": i.gravite, "description": i.description} for i in incoherences],
        "niveau_conformite_documents": verification.niveau_conformite if verification else None,
        "criteres": [{"critere": d.critere, "ponderation": d.ponderation, "score": d.score} for d in matching.details],
    }


def preparer_rapport(exigences: ExigencesStructurees, profil: ProfilCandidat,
                     verification: Optional[VerificationDocuments], matching: ResultatMatching) -> PreparationRapport:
    """Étape 100 % Python : faits, avis, copie du score, message expurgé. N'appelle PAS le modèle."""
    verif, numero_cin = retirer_donnees_sensibles(verification)
    avertissements: list[str] = []
    if verif is not None:
        coherence = _detail(matching, "coherence_documents").score
        if coherence != verif.score_coherence:
            avertissements.append("Le critère « cohérence » de l'Agent 4 diffère du score de cohérence de l'Agent 3.")

    incoherences = assembler_incoherences(verif)
    forts = assembler_points_forts(exigences, profil, verif, matching)
    manques = assembler_points_manquants(exigences, verif, matching)
    avis = determiner_avis(matching, incoherences)
    nom = " ".join(x for x in (profil.prenom, profil.nom) if x) or "Le candidat"

    donnees = _masquer_recursif(construire_donnees_llm(nom, exigences.titre_poste, matching.score_global, avis, forts,
                                                       manques, incoherences, verif, matching), numero_cin)
    message = json.dumps(donnees, ensure_ascii=False, indent=2)
    verifier_absence_cin(message, numero_cin)

    return PreparationRapport(
        nom_candidat=nom, titre_poste=exigences.titre_poste, score_global=matching.score_global, avis_indicatif=avis,
        points_forts=forts, points_manquants=manques, incoherences=incoherences,
        justification_score=reprendre_justification(matching, numero_cin),
        donnees_llm=donnees, message_llm=message, avertissements=avertissements)


# ---------------------------------------------------------------- rédaction par le modèle + contrôles
def _nombres(texte: str) -> set[float]:
    return {float(n.replace(",", ".")) for n in _NOMBRE_REGEX.findall(texte)}


def _termes_inconnus(texte: str, message: str) -> list[str]:
    """Termes capitalisés en milieu de phrase (compétences, outils, employeurs, lieux...) absents des faits fournis :
    signe d'une invention du modèle. Le début de phrase est ignoré (majuscule normale)."""
    base = _norm(message)
    inconnus = []
    for m in _MAJUSCULE_REGEX.finditer(texte):
        avant = texte[:m.start()].rstrip()
        if not avant or avant[-1] in ".!?:«\n":
            continue
        mot = _norm(m.group(0).rstrip(".-"))
        if mot and mot not in _MOTS_AUTORISES and mot not in base:
            inconnus.append(m.group(0))
    return inconnus


def valider_redaction(redaction: RedactionLLM, prep: PreparationRapport) -> None:
    """Lève RedactionInvalideError si le modèle a violé une règle : texte vide/trop long, CIN, décision de
    recrutement, score global différent, nombre ou terme (compétence, outil, employeur...) absent des faits fournis."""
    for nom, texte in (("resume", redaction.resume), ("conclusion", redaction.conclusion)):
        t = texte.strip()
        if not LONGUEUR_MIN <= len(t) <= LONGUEUR_MAX:
            raise RedactionInvalideError(f"« {nom} » vide ou de longueur inattendue.")
        if _CIN_REGEX.search(t) or MASQUE_CIN in t:
            raise RedactionInvalideError(f"« {nom} » contient un motif de numéro d'identité.")
        if _DECISION_REGEX.search(_norm(t)):
            raise RedactionInvalideError(f"« {nom} » formule une décision de recrutement.")
        for cite in _SCORE_REGEX.findall(t):
            if abs(float(cite.replace(",", ".")) - prep.score_global) > 0.05:
                raise RedactionInvalideError(f"« {nom} » cite un score différent de celui de l'Agent 4.")
        autorises = (_nombres(prep.message_llm) | {100.0}
                     | {float(len(prep.points_forts)), float(len(prep.points_manquants)), float(len(prep.incoherences)),
                        float(len(prep.justification_score))})
        if not _nombres(t) <= autorises:
            raise RedactionInvalideError(f"« {nom} » contient un nombre absent des faits fournis.")
        if _termes_inconnus(t, prep.message_llm):
            raise RedactionInvalideError(f"« {nom} » mentionne un terme absent des faits fournis.")


def ajouter_rappel_decision(conclusion: str) -> str:
    """Règle 4 : la conclusion rappelle toujours que la décision finale appartient au recruteur."""
    conclusion = conclusion.strip()
    return conclusion if _RAPPEL_REGEX.search(_norm(conclusion)) else f"{conclusion} {DECISION_FINALE}"


def rediger_resume_conclusion(prep: PreparationRapport, *, llm=None,
                              tentatives: int = MAX_TENTATIVES_REDACTION) -> RedactionLLM:
    """Appelle le modèle. Lève ErreurLLM (moteur) ou RedactionInvalideError (règle métier violée à chaque tentative)."""
    derniere: Optional[RedactionInvalideError] = None
    for essai in range(1, tentatives + 1):
        redaction = executer_redaction(PROMPT_REDACTION, prep.message_llm, RedactionLLM, llm=llm)
        try:
            valider_redaction(redaction, prep)
            return redaction
        except RedactionInvalideError as exc:
            derniere = exc
            logger.warning("Agent 5 : rédaction rejetée (%d/%d) : %s", essai, tentatives, exc)
    raise derniere


def construire_rapport(prep: PreparationRapport, redaction: RedactionLLM) -> RapportCandidature:
    """Assemble le RapportCandidature : faits du code + textes du modèle. Le schéma Pydantic revalide le tout."""
    return RapportCandidature(
        resume=redaction.resume.strip(),
        score_global=prep.score_global,
        points_forts=prep.points_forts,
        points_manquants=prep.points_manquants,
        incoherences=prep.incoherences,
        justification_score=prep.justification_score,
        conclusion=ajouter_rappel_decision(redaction.conclusion),
        avis_indicatif=prep.avis_indicatif,
        decision_finale=DECISION_FINALE,
    )


def generer_rapport_prototype(exigences: ExigencesStructurees, profil: ProfilCandidat,
                              verification: Optional[VerificationDocuments], matching: ResultatMatching,
                              llm=None) -> RapportCandidature:
    """Chemin nominal du prototype (strict : toute erreur du modèle est levée, sans repli)."""
    prep = preparer_rapport(exigences, profil, verification, matching)
    return construire_rapport(prep, rediger_resume_conclusion(prep, llm=llm))


# ---------------------------------------------------------------- démonstration sur les mocks
def dossier_mocks() -> Path:
    return Path(__file__).resolve().parents[2] / "data" / "mocks"


def charger_chaine(cas: str):
    m = dossier_mocks()
    lire = lambda nom: json.loads((m / nom).read_text(encoding="utf-8"))
    return (ExigencesStructurees.model_validate(lire("agent1_exemple.json")),
            ProfilCandidat.model_validate(lire("agent2_exemple.json")),
            VerificationDocuments.model_validate(lire(f"agent3_exemple_{cas}.json")),
            ResultatMatching.model_validate(lire(f"agent4_exemple_{cas}.json")),
            RapportCandidature.model_validate(lire(f"agent5_exemple_{cas}.json")))


if __name__ == "__main__":
    import argparse
    from agents.agent5_report.erreurs_agent5 import Agent5Error
    logging.basicConfig(level=logging.WARNING)
    ap = argparse.ArgumentParser(description="Agent 5 : prototype du rapport")
    ap.add_argument("--sans-modele", action="store_true", help="n'appelle pas le modèle : affiche seulement les faits")
    ap.add_argument("--cas", choices=("conforme", "incoherent"), help="un seul cas (défaut : les deux)")
    args = ap.parse_args()
    code_retour = 0
    for cas in ([args.cas] if args.cas else ["conforme", "incoherent"]):
        a1, a2, a3, a4, attendu = charger_chaine(cas)
        prep = preparer_rapport(a1, a2, a3, a4)
        print(f"\n=== Chaîne {cas} : score {prep.score_global} | avis {prep.avis_indicatif} (attendu {attendu.avis_indicatif}) ===")
        print("  Points forts   :", *prep.points_forts, sep="\n    - ")
        print("  Points manquants :", *prep.points_manquants, sep="\n    - ")
        print(f"  Incohérences    : {len(prep.incoherences)} (attendu {len(attendu.incoherences)}) -> "
              f"{'OK' if prep.incoherences == attendu.incoherences else 'KO'}")
        print(f"  Justification du score identique à l'Agent 4 : {'OK' if prep.justification_score == a4.details else 'KO'}")
        if args.sans_modele:
            continue
        try:
            rapport = construire_rapport(prep, rediger_resume_conclusion(prep))
        except Agent5Error as exc:
            print(f"  ERREUR modèle : {exc}")
            code_retour = 2
            continue
        print(f"\n  RÉSUMÉ     : {rapport.resume}\n  CONCLUSION : {rapport.conclusion}")
        print(f"  Score repris tel quel : {'OK' if rapport.score_global == a4.score_global else 'KO'}")
    raise SystemExit(code_retour)
