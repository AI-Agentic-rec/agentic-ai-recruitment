"""Test end-to-end : Agent 1 → 2 → 3 → 4 → 5.

Choisit des paires (candidat, offre) qui couvrent tous les scénarios :
- nominal (candidat 1, offre 1)
- diplôme insuffisant (candidat 1, offre 2)
- Master OK (candidat 4, offre 2)
- compétences absentes (candidat 6, offre 3)
- CIN expirée + offre minimaliste (candidat 8, offre 5)
- CV contredit diplôme (candidat 14, offre 1)
- CIN absente (candidat 12, offre 1)
- nom composé divergent (candidat 7, offre 1)
"""

import json
import logging
from pathlib import Path
import sys

RACINE = Path(__file__).resolve().parents[2]   
sys.path.insert(0, str(RACINE))
from agents.agent1_job_requirement.job_requirement import job_requirement_agent
from agents.agent2_cv_extraction.cv_extraction import extraire_profil_depuis_fichier
from agents.agent3_document_verification.agent3 import verifier_documents, sans_donnees_sensibles
from agents.agent4_matching.agent4 import faire_matching
from agents.agent5_report.agent5 import executer_agent5


logging.basicConfig(
    level=logging.WARNING,
    format="%(levelname)s %(name)s : %(message)s",
)

BASE = RACINE / "data" / "jeu_de_test" / "candidats"

# (candidat, offre, description du scénario)
PAIRES = [
    (1, 1, "Nominal : Licence Info, 3 ans, Python/SQL/Git"),
    (1, 2, "Diplôme insuffisant : Licence vs Master demandé"),
    (4, 2, "Master Info → Offre Data Scientist"),
    (6, 3, "Bachelor CS → Offre Stagiaire Web (HTML/CSS/JS absents)"),
    (8, 5, "Licence Éco + CIN expirée → Offre minimaliste"),
    (12, 1, "CIN absente → Offre Dev Python"),
    (7, 1, "Nom composé divergent (OUAZZANI ALAMI / OUAZZANI)"),
    (14, 1, "CV contredit diplôme (autre établissement, autre année)"),
]


def trouver_cv(dossier: Path) -> Path:
    """Renvoie le CV disponible (PDF ou DOCX)."""
    for nom in ("cv.pdf", "cv.docx"):
        if (dossier / nom).exists():
            return dossier / nom
    raise FileNotFoundError(f"Aucun CV dans {dossier}")


def tester_paire(cand_id: int, offre_id: int) -> dict:
    """Exécute le pipeline complet et renvoie un dict récapitulatif."""
    dossier = BASE / f"candidat_{cand_id}"

    # --- Agent 1 ---
    texte_offre = (BASE / "offres" / f"offre_{offre_id}.txt").read_text(encoding="utf-8")
    a1 = job_requirement_agent(texte_offre)

    # --- Agent 2 ---
    a2 = extraire_profil_depuis_fichier(trouver_cv(dossier))

    # --- Agent 3 ---
    image_cin = dossier / "cin.jpg"
    a3 = verifier_documents(
        a2,
        image_diplome=str(dossier / "diplome.jpg"),
        image_cin=str(image_cin) if image_cin.exists() else None,
    )
    a3_propre = sans_donnees_sensibles(a3)

    # --- Agent 4 ---
    a4 = faire_matching(a1, a2, a3_propre)

    # --- Agent 5 ---
    a5 = executer_agent5({
        "agent1": a1,
        "agent2": a2,
        "agent3": a3_propre,
        "agent4": a4,
    })

    return {"a1": a1, "a2": a2, "a3": a3, "a3_propre": a3_propre, "a4": a4, "a5": a5}


def afficher_recap(cand_id, offre_id, description, r):
    a1, a2, a3, a4, a5 = r["a1"], r["a2"], r["a3"], r["a4"], r["a5"]

    print(f"\n{'='*70}")
    print(f"Candidat {cand_id} × Offre {offre_id} — {description}")
    print(f"{'='*70}")

    print(f"\n[Agent 1] Offre extraite")
    print(f"  Poste        : {a1.titre_poste}")
    print(f"  Niveau min   : Bac+{a1.niveau_diplome_min}")
    print(f"  Expérience   : {a1.experience_min_annees} ans")
    print(f"  Obligatoires : {a1.competences_obligatoires}")
    print(f"  Souhaitées   : {a1.competences_souhaitees}")

    print(f"\n[Agent 2] CV extrait")
    print(f"  Identité     : {a2.prenom} {a2.nom}")
    print(f"  Formations   : {[(f.diplome, f.specialite) for f in a2.formations]}")
    print(f"  Expérience   : {a2.experience_totale_annees} ans")
    print(f"  Compétences  : {a2.competences}")
    print(f"  Langues      : {[(l.langue, l.niveau) for l in a2.langues]}")

    print(f"\n[Agent 3] Documents vérifiés")
    print(f"  Niveau       : {a3.niveau_conformite} (score {a3.score_coherence}/100)")
    print(f"  Manquants    : {a3.documents_manquants}")
    print(f"  Incohérences : {len(a3.incoherences)}")
    for inc in a3.incoherences:
        print(f"    - [{inc.gravite}] {inc.description[:120]}")

    print(f"\n[Agent 4] Matching")
    print(f"  Score global : {a4.score_global}/100")
    print(f"  Diplôme OK   : {a4.diplome_conforme}")
    print(f"  Expérience   : {a4.experience_candidat_annees} ans")
    print(f"  Présentes    : {a4.competences_correspondantes}")
    print(f"  Manquantes   : {a4.competences_manquantes}")
    print(f"  Détail :")
    for d in a4.details:
        print(f"    {d.critere:25} {d.score:5.1f}/100 × {d.ponderation:4.0f}%")

    print(f"\n[Agent 5] Rapport final")
    print(f"  Avis         : {a5.avis_indicatif}")
    print(f"  Résumé       : {a5.resume}")
    print(f"  Points forts : {len(a5.points_forts)}")
    print(f"  Manquants    : {len(a5.points_manquants)}")
    print(f"  Conclusion   : {a5.conclusion}")


def main():
    resultats = {}

    for cand_id, offre_id, description in PAIRES:
        print(f"\n>>> Traitement candidat {cand_id} × offre {offre_id}...")
        try:
            r = tester_paire(cand_id, offre_id)
            resultats[(cand_id, offre_id)] = r
            afficher_recap(cand_id, offre_id, description, r)
        except Exception as e:
            print(f"\n❌ ERREUR candidat {cand_id} × offre {offre_id} : "
                  f"{type(e).__name__}: {e}")

    # --- Résumé final ---
    print(f"\n\n{'='*70}")
    print("RÉSUMÉ FINAL")
    print(f"{'='*70}")
    print(f"{'Candidat':>10} {'Offre':>6} {'Score':>7} {'Avis':>15} {'Docs':>20}")
    print("-" * 70)
    for (cand_id, offre_id), r in resultats.items():
        a4, a5, a3 = r["a4"], r["a5"], r["a3"]
        print(f"{cand_id:>10} {offre_id:>6} {a4.score_global:>7.1f} "
              f"{a5.avis_indicatif:>15} {a3.niveau_conformite:>20}")

    # Sauvegarde JSON pour inspection ultérieure
    sortie = BASE / "resultats_e2e.json"
    with open(sortie, "w", encoding="utf-8") as f:
        json.dump(
            {
                f"cand{cand_id}_offre{offre_id}": {
                    "score": r["a4"].score_global,
                    "avis": r["a5"].avis_indicatif,
                    "niveau_docs": r["a3"].niveau_conformite,
                    "competences_manquantes": r["a4"].competences_manquantes,
                    "resume": r["a5"].resume,
                }
                for (cand_id, offre_id), r in resultats.items()
            },
            f, indent=2, ensure_ascii=False,
        )
    print(f"\nRésultats sauvegardés dans {sortie}")


if __name__ == "__main__":
    main()