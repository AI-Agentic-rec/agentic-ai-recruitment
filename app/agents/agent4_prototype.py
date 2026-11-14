"""
AGENT 4 : PROTOTYPE (semaine 1)  ->  tâche ClickUp « Agent 4 : prototype du score sur JSON d'exemple »

Le score est calculé par le CODE (reproductible, explicable), avec les 6 critères et les pondérations de la fiche.
Le modèle ne sert qu'à reconnaître des compétences équivalentes (« JS » = « JavaScript »), uniquement pour les
compétences que le code n'a pas trouvées par lui-même.

Entrées : ExigencesStructurees (agent 1), ProfilCandidat (agent 2), VerificationDocuments (agent 3).
Sortie  : ResultatMatching (schemas.py).
Semaine 2 (agent4.py) : cas limites, intégration à l'orchestrateur, tests complets.

Lancer :  python agent4_prototype.py --sans-modele     (score seul, sans Ollama)
          python agent4_prototype.py                   (avec qwen3.5:4b pour les compétences équivalentes)
"""
import json
import logging
from pathlib import Path
from typing import Optional

from llm_local import executer_agent
from niveaux_diplome import niveau_diplome, normaliser
from prompts_agent4 import PROMPT_CORRESPONDANCE
from schemas import (BaseSchema, CRITERES, DetailCritere, ExigencesStructurees, Langue, ProfilCandidat,
                     ResultatMatching, VerificationDocuments)

# Pondérations de la fiche (section 5.2), somme = 100. Toute modification doit être documentée et justifiée.
PONDERATIONS = {"competences_obligatoires": 40, "experience": 20, "diplome_formation": 15,
                "competences_souhaitees": 10, "langues": 5, "coherence_documents": 10}
POINTS_PERDUS_PAR_ANNEE_DE_DIPLOME_MANQUANTE = 30     # Licence (Bac+3) pour Bac+5 demandé : 100 - 2 x 30 = 40

# Niveaux de langue : CECRL (A1 à C2 = 1 à 6) et expressions courantes. « courant » est assimilé à C1.
ECHELLE_LANGUE = (("langue maternelle", 7), ("maternelle", 7), ("natif", 7), ("bilingue", 7), ("c2", 6), ("c1", 5),
                  ("courant", 5), ("avance", 5), ("b2", 4), ("b1", 3), ("intermediaire", 3), ("a2", 2),
                  ("scolaire", 2), ("a1", 1), ("debutant", 1), ("notions", 1))


# ---------------------------------------------------------------- compétences (code + modèle)
class Correspondance(BaseSchema):
    exigee: str
    trouvee: Optional[str] = None


class CorrespondanceCompetences(BaseSchema):
    obligatoires: list[Correspondance]
    souhaitees: list[Correspondance]


def competences_du_candidat(profil: ProfilCandidat) -> list[str]:
    vues, resultat = set(), []
    for c in profil.competences + [c for e in profil.experiences for c in e.competences]:
        if normaliser(c) not in vues:
            vues.add(normaliser(c)); resultat.append(c)
    return resultat


def apparier_competences(obligatoires, souhaitees, candidat, llm=None, utiliser_modele=True) -> dict:
    """Renvoie {compétence exigée: compétence du candidat ou None}.
    1) le code cherche les correspondances exactes (casse et accents ignorés) ; 2) le modèle ne voit que le reste ;
    3) garde-fou : une correspondance du modèle n'est acceptée que si la compétence figure vraiment dans le profil."""
    index = {normaliser(c): c for c in candidat}
    trouvees, restantes = {}, {}
    for ex in list(obligatoires) + list(souhaitees):
        exact = index.get(normaliser(ex))
        if exact:
            trouvees[ex] = exact
        else:
            restantes[normaliser(ex)] = ex
    if restantes and utiliser_modele:
        r_o = [e for e in obligatoires if normaliser(e) in restantes]
        r_s = [e for e in souhaitees if normaliser(e) in restantes]
        message = json.dumps({"competences_exigees_obligatoires": r_o, "competences_exigees_souhaitees": r_s,
                              "competences_du_candidat": candidat}, ensure_ascii=False, indent=2)
        reponse = executer_agent(4, PROMPT_CORRESPONDANCE, message, CorrespondanceCompetences, llm=llm)
        for c in reponse.obligatoires + reponse.souhaitees:
            if c.trouvee and normaliser(c.trouvee) in index and normaliser(c.exigee) in restantes:
                trouvees[restantes[normaliser(c.exigee)]] = index[normaliser(c.trouvee)]
    return {ex: trouvees.get(ex) for ex in list(obligatoires) + list(souhaitees)}


# ---------------------------------------------------------------- critères calculés par le code
def _liste(elements) -> str:
    return ", ".join(elements) if elements else "aucune"


def score_competences(exigees, trouvees, nom: str):
    ok = [e for e in exigees if trouvees[e]]
    ko = [e for e in exigees if not trouvees[e]]
    if not exigees:
        return 100.0, f"Aucune compétence {nom} exigée.", ok, ko
    score = round(100 * len(ok) / len(exigees), 1)
    return score, f"{len(ok)} compétence(s) {nom}(s) sur {len(exigees)} identifiée(s) ({_liste(ok)}) ; manquante(s) : {_liste(ko)}.", ok, ko


def experience_du_candidat(profil: ProfilCandidat) -> float:
    return profil.experience_totale_annees or round(sum(e.duree_annees or 0 for e in profil.experiences), 1)


def score_experience(requise: float, obtenue: float):
    if requise == 0:
        return 100.0, "Aucune expérience minimale exigée."
    score = min(100.0, round(100 * obtenue / requise, 1))
    return score, f"{obtenue:g} an(s) d'expérience pour {requise:g} demandé(s) : " + ("critère atteint." if obtenue >= requise else "insuffisant.")


def niveau_du_candidat(profil: ProfilCandidat, verification: Optional[VerificationDocuments]):
    """Le diplôme VÉRIFIÉ (agent 3) prime sur ce que le CV déclare."""
    d = verification.infos_diplome if verification else None
    if d:
        n = niveau_diplome(d.diplome) or niveau_diplome(d.diplome, d.specialite)
        if n is not None:
            return n, "diplôme vérifié"
    niveaux = [n for f in profil.formations if (n := niveau_diplome(f.diplome) or niveau_diplome(f.diplome, f.specialite)) is not None]
    return (max(niveaux), "d'après le CV, non vérifié") if niveaux else (None, "")


def score_diplome(requis: Optional[int], candidat: Optional[int], source: str):
    if requis is None:
        return 100.0, "Aucun niveau de diplôme minimal exigé.", True
    if candidat is None:
        return 0.0, f"Niveau du diplôme non identifié pour Bac+{requis} demandé.", False
    if candidat >= requis:
        return 100.0, f"Niveau Bac+{candidat} ({source}) pour Bac+{requis} demandé : conforme.", True
    score = max(0.0, 100.0 - POINTS_PERDUS_PAR_ANNEE_DE_DIPLOME_MANQUANTE * (requis - candidat))
    return score, f"Niveau Bac+{candidat} ({source}) pour Bac+{requis} demandé : inférieur de {requis - candidat} an(s).", False


def niveau_langue(texte) -> Optional[int]:
    n = f" {normaliser(texte)} "
    valeurs = [v for mot, v in ECHELLE_LANGUE if f" {mot} " in n]
    return max(valeurs) if valeurs else None


def score_langues(exigees: list[Langue], possedees: list[Langue]):
    if not exigees:
        return 100.0, "Aucune langue exigée."
    par_nom = {normaliser(l.langue): l for l in possedees}
    credits, notes = [], []
    for ex in exigees:
        l = par_nom.get(normaliser(ex.langue))
        requis = niveau_langue(ex.niveau)
        if l is None:
            credits.append(0); notes.append(f"{ex.langue} absente")
        elif requis is None:
            credits.append(1); notes.append(f"{ex.langue} présente")
        elif niveau_langue(l.niveau) is None:
            credits.append(0.5); notes.append(f"{ex.langue} : niveau non précisé")
        elif niveau_langue(l.niveau) >= requis:
            credits.append(1); notes.append(f"{ex.langue} conforme")
        else:
            credits.append(niveau_langue(l.niveau) / requis); notes.append(f"{ex.langue} : niveau insuffisant")
    return round(100 * sum(credits) / len(credits), 1), " ; ".join(notes) + "."


# ---------------------------------------------------------------- assemblage
def calculer_matching(exigences: ExigencesStructurees, profil: ProfilCandidat,
                      verification: Optional[VerificationDocuments] = None,
                      llm=None, utiliser_modele: bool = True) -> ResultatMatching:
    trouvees = apparier_competences(exigences.competences_obligatoires, exigences.competences_souhaitees,
                                    competences_du_candidat(profil), llm, utiliser_modele)
    s_obl, j_obl, ok_o, ko_o = score_competences(exigences.competences_obligatoires, trouvees, "obligatoire")
    s_sou, j_sou, ok_s, ko_s = score_competences(exigences.competences_souhaitees, trouvees, "souhaitée")

    exp = experience_du_candidat(profil)
    s_exp, j_exp = score_experience(exigences.experience_min_annees, exp)

    niveau, source = niveau_du_candidat(profil, verification)
    s_dip, j_dip, diplome_conforme = score_diplome(exigences.niveau_diplome_min, niveau, source)

    s_lan, j_lan = score_langues(exigences.langues, profil.langues)

    if verification is None:
        s_coh, j_coh = 0.0, "Aucune vérification des documents disponible."
    else:
        s_coh = float(verification.score_coherence)
        j_coh = f"Vérification des documents : {verification.niveau_conformite.replace('_', ' ')} ({len(verification.incoherences)} incohérence(s), score de cohérence {verification.score_coherence})."

    scores = {"competences_obligatoires": (s_obl, j_obl), "experience": (s_exp, j_exp), "diplome_formation": (s_dip, j_dip),
              "competences_souhaitees": (s_sou, j_sou), "langues": (s_lan, j_lan), "coherence_documents": (s_coh, j_coh)}
    details = [DetailCritere(critere=c, ponderation=PONDERATIONS[c], score=scores[c][0], justification=scores[c][1]) for c in CRITERES]
    return ResultatMatching(
        score_global=round(sum(d.ponderation * d.score / 100 for d in details), 1), details=details,
        competences_correspondantes=list(dict.fromkeys(ok_o + ok_s)), competences_manquantes=list(dict.fromkeys(ko_o + ko_s)),
        diplome_conforme=diplome_conforme, experience_candidat_annees=exp)


# ---------------------------------------------------------------- démonstration sur les mocks
def dossier_samples():
    ici = Path(__file__).parent
    return next((p for p in (ici / "samples", ici.parent / "samples") if p.is_dir()), None)


if __name__ == "__main__":
    import argparse
    logging.basicConfig(level=logging.WARNING)
    ap = argparse.ArgumentParser(description="Agent 4 : prototype du score")
    ap.add_argument("--sans-modele", action="store_true", help="n'appelle pas le modèle (compétences équivalentes ignorées)")
    sans_modele = ap.parse_args().sans_modele
    samples = dossier_samples()
    if samples is None:
        raise SystemExit("Dossier samples/ introuvable : placez-le à côté des fichiers Python ou un niveau au-dessus.")
    charger = lambda nom: json.loads((samples / nom).read_text(encoding="utf-8"))
    exigences = ExigencesStructurees.model_validate(charger("agent1_exemple.json"))
    profil = ProfilCandidat.model_validate(charger("agent2_exemple.json"))
    for cas in ("conforme", "incoherent"):
        verification = VerificationDocuments.model_validate(charger(f"agent3_exemple_{cas}.json"))
        attendu = ResultatMatching.model_validate(charger(f"agent4_exemple_{cas}.json"))
        r = calculer_matching(exigences, profil, verification, utiliser_modele=not sans_modele)
        print(f"\n=== Chaîne {cas} : score {r.score_global} (attendu {attendu.score_global}) ===")
        for d, a in zip(r.details, attendu.details):
            print(f"  {'OK ' if d.score == a.score else 'KO '} {d.critere:<26} pondération {d.ponderation:>4.0f}  score {d.score:>5}  attendu {a.score:>5}")
            print(f"       {d.justification}")
        print(f"  Correspondantes : {r.competences_correspondantes}\n  Manquantes      : {r.competences_manquantes}")
        print(f"  Diplôme conforme : {r.diplome_conforme}   Expérience : {r.experience_candidat_annees} an(s)")
