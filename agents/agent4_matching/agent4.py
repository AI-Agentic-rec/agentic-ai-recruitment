"""
AGENT 4 : Matching candidat / offre

Responsabilité unique :
Comparer le profil du candidat (agent 2) aux exigences de l'offre (agent 1)
et tenir compte de la cohérence des documents (agent 3).

Règles de calcul : celles de la fiche (section 5.2), identiques à
agent4_prototype.py. Toute modification doit être documentée et justifiée.

Principe : le LLM comprend le langage, le code prend la décision.
- Le score est calculé EN CODE.
- Aucune liste d'alias ni de familles de compétences dans Python.
- Le LLM ne compare jamais deux compétences : il donne seulement le nom
  canonique de chaque terme, indépendamment des autres.
- Le code décide : deux termes sont équivalents si leurs noms canoniques
  sont identiques après une normalisation de forme (casse, accents,
  ponctuation, mots décoratifs génériques).
- Une compétence du candidat ne satisfait qu'une seule exigence.
- Si le LLM est indisponible, les égalités normalisées restent comptées.
- Le diplôme vérifié par l'agent 3 prime sur celui déclaré dans le CV.

Pipeline :
1. Égalités normalisées en code.
2. Normalisation des termes restants par le LLM, comparaison en code.
3. Calcul des six critères.
4. Pondération fixe et score global.

Sortie : ResultatMatching, destinée à l'agent 5.
"""

import json
import logging
import re
import unicodedata
from pathlib import Path
from typing import Optional

from pydantic import Field

from agents.common.llm_local import AgentError, executer_agent
from agents.common.niveaux_diplome import niveau_diplome as _niveau
from agents.common.schemas import (
    CRITERES,
    BaseSchema,
    ContexteCandidature,
    DetailCritere,
    ExigencesStructurees,
    ProfilCandidat,
    ResultatMatching,
    VerificationDocuments,
)
from agents.agent4_matching.prompts_agent4 import PROMPT_NORMALISATION


logger = logging.getLogger("agent4")
NUMERO_AGENT = 4


# =============================================================================
# PARAMÈTRES DE LA FICHE (section 5.2)
# =============================================================================

PONDERATIONS = {
    "competences_obligatoires": 40,
    "experience": 20,
    "diplome_formation": 15,
    "competences_souhaitees": 10,
    "langues": 5,
    "coherence_documents": 10,
}

# Licence (Bac+3) pour Bac+5 demandé : 100 - 2 x 30 = 40
PENALITE_PAR_NIVEAU = 30

# Mots génériques sans valeur d'identification, ignorés à la comparaison
# (« Apache Spark » = « Spark », « Tableau Software » = « Tableau »).
# Ce n'est PAS une liste de technologies.
MOTS_DECORATIFS_DEBUT = {"apache", "microsoft"}
MOTS_DECORATIFS_FIN = {"software", "framework", "library", "language"}

# Alias de langues (nom de la langue uniquement).
ALIAS_LANGUES = {
    "francais": "francais", "french": "francais", "fr": "francais",
    "anglais": "anglais", "english": "anglais", "en": "anglais",
    "arabe": "arabe", "arabic": "arabe", "ar": "arabe",
    "espagnol": "espagnol", "spanish": "espagnol", "es": "espagnol",
    "allemand": "allemand", "german": "allemand", "de": "allemand",
}

# Niveaux de langue : CECRL (A1 à C2 = 1 à 6) et expressions courantes.
# « courant » est assimilé à C1.
ECHELLE_LANGUE = (
    ("langue maternelle", 7), ("maternelle", 7), ("natif", 7), ("bilingue", 7),
    ("c2", 6), ("c1", 5), ("courant", 5), ("avance", 5),
    ("b2", 4), ("b1", 3), ("intermediaire", 3),
    ("a2", 2), ("scolaire", 2), ("a1", 1), ("debutant", 1), ("notions", 1),
)


# =============================================================================
# SCHÉMA DE LA RÉPONSE DU MODÈLE
# =============================================================================

class TermeCanonique(BaseSchema):
    terme: str
    canonique: str


class NormalisationCompetences(BaseSchema):
    competences: list[TermeCanonique] = Field(default_factory=list)


# =============================================================================
# OUTILS GÉNÉRAUX
# =============================================================================

def _ascii(texte) -> str:
    """Supprime les accents et met le texte en minuscules."""
    s = unicodedata.normalize("NFKD", str(texte or ""))
    return s.encode("ascii", "ignore").decode().lower().strip()


def _cle_comparaison(texte) -> str:
    """
    Clé de comparaison stricte : casse, accents, espaces, ponctuation et mots
    décoratifs génériques sont ignorés (« Node.js » = « NodeJS »,
    « Apache Spark » = « Spark »), mais « c » ≠ « c++ » ≠ « c# ».
    Ce n'est PAS une liste d'alias.
    """
    s = _ascii(texte)
    mots = s.split()

    while len(mots) > 1 and mots[0] in MOTS_DECORATIFS_DEBUT:
        mots = mots[1:]
    while len(mots) > 1 and mots[-1] in MOTS_DECORATIFS_FIN:
        mots = mots[:-1]

    cle = re.sub(r"[^a-z0-9+#]", "", "".join(mots))
    return cle or s


def _cle_langue(texte) -> str:
    s = re.sub(r"[^a-z]", "", _ascii(texte))
    return ALIAS_LANGUES.get(s, s)


def _niveau_langue(texte) -> Optional[int]:
    """Niveau numérique d'une langue (échelle de la fiche), ou None."""
    n = f" {_ascii(texte)} "
    valeurs = [v for mot, v in ECHELLE_LANGUE if f" {mot} " in n]
    return max(valeurs) if valeurs else None


def _nettoyer_liste(valeurs) -> list[str]:
    """Supprime les valeurs vides et les doublons exacts."""
    return list(
        dict.fromkeys(
            v.strip() for v in valeurs
            if isinstance(v, str) and v.strip()
        )
    )


def _competences_candidat(profil: ProfilCandidat) -> list[str]:
    """Compétences du CV et celles mentionnées dans les expériences."""
    brut = list(profil.competences)
    for exp in profil.experiences:
        brut.extend(exp.competences)
    return _nettoyer_liste(brut)


def _niveau_formation(f) -> Optional[int]:
    """Détermine le niveau d'une formation."""
    n = _niveau(f.diplome)
    return n if n is not None else _niveau(f.diplome, f.specialite)


# =============================================================================
# ÉTAPE 1 : APPARIEMENT DES COMPÉTENCES
# =============================================================================

def _normaliser_par_llm(
    termes: list[str], llm, max_essais: int, ref: str
) -> dict[str, str]:
    """
    Demande au LLM le nom canonique de chaque terme.
    Le modèle ne compare rien : la décision d'équivalence reste dans le code.
    Retourne {terme: nom canonique}. Un terme absent de la réponse reste inchangé.
    """
    if not termes:
        return {}

    # Exigences et compétences du candidat sont mélangées et triées :
    # le modèle ne voit pas de paires.
    payload = {"termes": sorted(termes, key=str.lower)}
    message = "Termes à normaliser :\n" + json.dumps(payload, ensure_ascii=False)

    try:
        reponse = executer_agent(
            NUMERO_AGENT,
            PROMPT_NORMALISATION,
            message,
            NormalisationCompetences,
            llm=llm,
            max_essais=max_essais,
        )
    except AgentError as e:
        logger.warning("%s Agent 4 : normalisation non obtenue (%s)", ref, e)
        return {}

    demandes = set(termes)
    canon = {}
    for p in reponse.competences:
        # Retire les précisions entre parenthèses :
        # « Django (web framework) » -> « Django ».
        nom = re.sub(r"\s*\(.*?\)", "", p.canonique).strip()
        if p.terme in demandes and p.terme not in canon and nom:
            canon[p.terme] = nom
            logger.info("%s Nom canonique : %s -> %s", ref, p.terme, nom)

    return canon


def _apparier_competences(obl, souh, competences_candidat, llm, max_essais, ref):
    """
    1. Égalités normalisées en code.
    2. Pour le reste : le LLM normalise chaque terme indépendamment ;
       le code compare ensuite les noms canoniques.
    Une compétence du candidat ne satisfait qu'une seule exigence.
    """
    if not competences_candidat or not (obl or souh):
        return {}

    exigences = list(dict.fromkeys(obl + souh))
    trouvees = {}

    # 1. Égalités normalisées
    par_cle = {}
    for c in competences_candidat:
        par_cle.setdefault(_cle_comparaison(c), c)

    for e in exigences:
        c = par_cle.get(_cle_comparaison(e))
        if c and c not in trouvees.values():
            trouvees[e] = c
            logger.info("%s Égalité normalisée : %s -> %s", ref, e, c)

    restantes = [e for e in exigences if e not in trouvees]
    prises = set(trouvees.values())
    libres = [c for c in competences_candidat if c not in prises]

    if not restantes or not libres:
        return trouvees

    # 2. Normalisation par le LLM, comparaison par le code
    canon = _normaliser_par_llm(
        list(dict.fromkeys(restantes + libres)), llm, max_essais, ref
    )

    def cle(terme):
        return _cle_comparaison(canon.get(terme, terme))

    index = {}
    for c in libres:
        index.setdefault(cle(c), c)

    for e in restantes:
        c = index.get(cle(e))
        if c and c not in prises:
            trouvees[e] = c
            prises.add(c)
            logger.info(
                "%s Correspondance acceptée : %s -> %s (nom canonique : %s)",
                ref, e, c, canon.get(e, e),
            )
        else:
            logger.info("%s Aucune correspondance pour : %s", ref, e)

    return trouvees


# =============================================================================
# ÉTAPE 2 : LES SIX CRITÈRES
# Chaque fonction retourne (score 0-100, justification), ou None si la donnée
# nécessaire est absente (le score par défaut est alors appliqué plus bas).
# =============================================================================

def _critere_competences(exigees, trouvees, nom):
    if not exigees:
        return None

    ok = [e for e in exigees if e in trouvees]
    ko = [e for e in exigees if e not in trouvees]

    just = f"{len(ok)}/{len(exigees)} compétences {nom} trouvées."
    if ok:
        just += " Présentes : " + ", ".join(ok) + "."
    if ko:
        just += " Manquantes : " + ", ".join(ko) + "."

    return round(100 * len(ok) / len(exigees), 1), just


def _experience_candidat(profil: ProfilCandidat) -> float:
    if profil.experience_totale_annees > 0:
        return float(profil.experience_totale_annees)
    return round(sum(e.duree_annees or 0 for e in profil.experiences), 1)


def _critere_experience(offre: ExigencesStructurees, annees: float):
    mini = offre.experience_min_annees
    if mini <= 0:
        return None

    score = min(100.0, round(100 * annees / mini, 1))
    return (
        score,
        f"{annees:g} an(s) d'expérience pour {mini:g} demandé(s) : "
        + ("critère atteint." if annees >= mini else "insuffisant."),
    )


def _critere_diplome(
    offre: ExigencesStructurees,
    profil: ProfilCandidat,
    verif: Optional[VerificationDocuments] = None,
):
    """
    Retourne (résultat ou None, diplome_conforme).
    Le diplôme VÉRIFIÉ (agent 3) prime sur ce que le CV déclare.
    """
    mini = offre.niveau_diplome_min
    if mini is None and offre.diplome_demande:
        mini = _niveau(offre.diplome_demande)

    if mini is None:
        return None, True

    niveau, source = None, ""

    d = verif.infos_diplome if verif else None
    if d:
        n = _niveau(d.diplome)
        n = n if n is not None else _niveau(d.diplome, d.specialite)
        if n is not None:
            niveau, source = n, "diplôme vérifié"

    if niveau is None:
        niveaux = [
            n for n in map(_niveau_formation, profil.formations)
            if n is not None
        ]
        if niveaux:
            niveau, source = max(niveaux), "d'après le CV, non vérifié"

    if niveau is None:
        return (
            (0.0, f"Niveau du diplôme non identifié pour Bac+{mini} demandé."),
            False,
        )

    if niveau >= mini:
        return (
            (100.0, f"Niveau Bac+{niveau} ({source}) pour Bac+{mini} demandé : conforme."),
            True,
        )

    score = max(0.0, 100.0 - PENALITE_PAR_NIVEAU * (mini - niveau))
    return (
        (
            score,
            f"Niveau Bac+{niveau} ({source}) pour Bac+{mini} demandé : "
            f"inférieur de {mini - niveau} an(s).",
        ),
        False,
    )


def _critere_langues(offre: ExigencesStructurees, profil: ProfilCandidat):
    if not offre.langues:
        return None

    candidat = {}
    for langue in profil.langues:
        candidat.setdefault(_cle_langue(langue.langue), langue)

    credits, notes = [], []

    for req in offre.langues:
        cand = candidat.get(_cle_langue(req.langue))
        requis = _niveau_langue(req.niveau)

        if cand is None:
            credits.append(0.0)
            notes.append(f"{req.langue} absente")
        elif requis is None:
            credits.append(1.0)
            notes.append(f"{req.langue} présente")
        elif _niveau_langue(cand.niveau) is None:
            credits.append(0.5)
            notes.append(f"{req.langue} : niveau non précisé")
        elif _niveau_langue(cand.niveau) >= requis:
            credits.append(1.0)
            notes.append(f"{req.langue} conforme")
        else:
            credits.append(_niveau_langue(cand.niveau) / requis)
            notes.append(f"{req.langue} : niveau insuffisant")

    return round(100 * sum(credits) / len(credits), 1), " ; ".join(notes) + "."


def _critere_coherence(verif: Optional[VerificationDocuments]):
    if verif is None:
        return None

    n = len(verif.incoherences)

    just = (
        f"Vérification des documents : "
        f"{verif.niveau_conformite.replace('_', ' ')} "
        f"({n} incohérence(s), score de cohérence {verif.score_coherence})."
    )

    if verif.documents_manquants:
        just += " Manquants : " + ", ".join(verif.documents_manquants) + "."
    if verif.documents_illisibles:
        just += " Illisibles : " + ", ".join(verif.documents_illisibles) + "."

    return float(verif.score_coherence), just


# =============================================================================
# PIPELINE PRINCIPAL
# =============================================================================

def faire_matching(
    exigences,
    profil_cv,
    verification=None,
    contexte: Optional[ContexteCandidature] = None,
    llm=None,
    max_essais: int = 3,
) -> ResultatMatching:

    offre = (
        exigences
        if isinstance(exigences, ExigencesStructurees)
        else ExigencesStructurees.model_validate(exigences)
    )

    profil = (
        profil_cv
        if isinstance(profil_cv, ProfilCandidat)
        else ProfilCandidat.model_validate(profil_cv)
    )

    verif = (
        None
        if verification is None
        else verification
        if isinstance(verification, VerificationDocuments)
        else VerificationDocuments.model_validate(verification)
    )

    ref = (
        f"[candidature {contexte.candidate_id} / offre {contexte.job_id}]"
        if contexte
        else "[candidature ?]"
    )

    # Compétences
    obl = _nettoyer_liste(offre.competences_obligatoires)
    souh = _nettoyer_liste(offre.competences_souhaitees)
    competences_candidat = _competences_candidat(profil)

    trouvees = _apparier_competences(
        obl, souh, competences_candidat, llm, max_essais, ref
    )

    # Critères
    annees = _experience_candidat(profil)
    res_diplome, diplome_conforme = _critere_diplome(offre, profil, verif)

    resultats = {
        "competences_obligatoires": _critere_competences(
            obl, trouvees, "obligatoires"
        ),
        "experience": _critere_experience(offre, annees),
        "diplome_formation": res_diplome,
        "competences_souhaitees": _critere_competences(
            souh, trouvees, "souhaitées"
        ),
        "langues": _critere_langues(offre, profil),
        "coherence_documents": _critere_coherence(verif),
    }

    # Pondérations fixes (fiche). Un critère sans exigence vaut 100,
    # sauf la cohérence des documents, qui vaut 0 sans vérification.
    details = []
    for c in CRITERES:
        r = resultats[c]

        if r is None:
            if c == "coherence_documents":
                score, just = 0.0, "Aucune vérification des documents disponible."
            else:
                score, just = 100.0, "Aucune exigence dans l'offre sur ce critère."
        else:
            score, just = r
            score = round(max(0.0, min(100.0, score)), 1)

        details.append(
            DetailCritere(
                critere=c,
                ponderation=float(PONDERATIONS[c]),
                score=score,
                justification=just,
            )
        )

    score_global = round(
        max(
            0.0,
            min(100.0, sum(d.ponderation * d.score / 100 for d in details)),
        ),
        1,
    )

    toutes = list(dict.fromkeys(obl + souh))
    correspondantes = [s for s in toutes if s in trouvees]
    manquantes = [s for s in toutes if s not in trouvees]

    logger.info("%s Compétences correspondantes : %s", ref, correspondantes)
    logger.info("%s Compétences manquantes : %s", ref, manquantes)
    logger.info("%s Agent 4 terminé : score global %.1f", ref, score_global)

    return ResultatMatching(
        score_global=score_global,
        details=details,
        competences_correspondantes=correspondantes,
        competences_manquantes=manquantes,
        diplome_conforme=diplome_conforme,
        experience_candidat_annees=round(annees, 2),
    )


# =============================================================================
# EXÉCUTION DIRECTE / TESTS MANUELS
# =============================================================================

if __name__ == "__main__":
    import argparse

    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s:%(name)s:%(message)s",
    )

    ap = argparse.ArgumentParser(
        description="Agent 4 : matching candidat / offre"
    )
    ap.add_argument(
        "--offre", required=True, help="JSON ExigencesStructurees (agent 1)"
    )
    ap.add_argument(
        "--cv", required=True, help="JSON ProfilCandidat (agent 2)"
    )
    ap.add_argument(
        "--docs", help="JSON VerificationDocuments (agent 3)"
    )
    args = ap.parse_args()

    def lire(chemin):
        return json.loads(Path(chemin).read_text(encoding="utf-8"))

    resultat = faire_matching(
        lire(args.offre),
        lire(args.cv),
        lire(args.docs) if args.docs else None,
    )

    print(resultat.model_dump_json(indent=2))