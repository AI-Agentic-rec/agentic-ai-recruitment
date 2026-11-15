"""
Test de la chaîne Agent 3 -> Agent 4 sur le jeu de données de create_dataset.py.

Pour chaque candidat :
1. Agent 3 lit diplome.jpg et cin.jpg et vérifie le tout contre le CV.
2. sans_donnees_sensibles() retire le numéro de CIN (comme en production).
3. Agent 4 calcule le matching avec cette sortie.

Vérifie : niveau de conformité attendu, numéro de CIN retiré, score de cohérence
repris tel quel par l'Agent 4, et score global cohérent avec la fiche.

Lancer (depuis la racine du projet) :
    $env:PYTHONUTF8 = "1"
    python data/jeu_de_test/run_chaine.py                # tous les candidats
    python data/jeu_de_test/run_chaine.py 1 7 8 12       # seulement ceux-là
    python data/jeu_de_test/run_chaine.py --reutiliser   # réutilise resultats/candidat_N.json (agent 3 non relancé)
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import argparse
import csv
import json
import time

from agents.agent3_document_verification.agent3 import (
    sans_donnees_sensibles,
    verifier_documents,
)
from agents.agent4_matching.agent4 import faire_matching
from agents.common.schemas import VerificationDocuments

BASE = Path(__file__).parent / "candidats"
SORTIE = Path(__file__).parent / "resultats"
SORTIE.mkdir(exist_ok=True)

# Offre fixe : chaque candidat est comparé à la même offre.
OFFRE = {
    "titre_poste": "Développeur Python",
    "diplome_demande": "Licence",
    "niveau_diplome_min": 3,
    "experience_min_annees": 2,
    "competences_obligatoires": ["Python", "SQL", "Docker"],
    "competences_souhaitees": ["Git"],
    "langues": [{"langue": "Anglais", "niveau": "B2"}],
    "missions": [],
}

# Le CV du dataset ne contient que l'identité et la formation : on y ajoute
# les compétences, l'expérience et les langues, identiques pour tous.
COMPLEMENT_CV = {
    "competences": ["Python", "SQL", "Git"],
    "experience_totale_annees": 3.0,
    "langues": [
        {"langue": "Français", "niveau": "C1"},
        {"langue": "Anglais", "niveau": "B2"},
    ],
}

# Avec cette offre et ce complément (tous les critères à 100 sauf Docker manquant),
# le score global ne dépend que de la cohérence des documents :
# 40 x 66,7 % + 20 + 15 + 10 + 5 = 76,7 points, plus 10 % du score de cohérence.
BASE_SANS_COHERENCE = 76.7


def verifier_chaine(gt, v3, r4) -> list[str]:
    erreurs = []

    if v3.niveau_conformite not in gt["niveaux_acceptes"]:
        erreurs.append(
            f"agent 3 : niveau {v3.niveau_conformite!r}, attendu {gt['niveaux_acceptes']}"
        )

    if v3.infos_cin is not None and v3.infos_cin.numero_cin is not None:
        erreurs.append("le numéro de CIN n'a pas été retiré")

    coh = next(d for d in r4.details if d.critere == "coherence_documents")
    if abs(coh.score - v3.score_coherence) > 0.05:
        erreurs.append(
            f"cohérence : agent 3 = {v3.score_coherence}, agent 4 = {coh.score}"
        )

    if r4.diplome_conforme:
        attendu = round(BASE_SANS_COHERENCE + 0.1 * v3.score_coherence, 1)
        if abs(r4.score_global - attendu) > 0.15:
            erreurs.append(
                f"score global {r4.score_global}, attendu environ {attendu}"
            )

    return erreurs


def main():
    ap = argparse.ArgumentParser(description="Test de la chaîne agent 3 -> agent 4")
    ap.add_argument("ids", nargs="*", type=int)
    ap.add_argument("--reutiliser", action="store_true",
                    help="réutilise resultats/candidat_N.json au lieu de relancer l'agent 3")
    args = ap.parse_args()

    lignes = []

    for dossier in sorted(BASE.glob("candidat_*"),
                          key=lambda p: int(p.name.split("_")[1])):
        cid = int(dossier.name.split("_")[1])
        if args.ids and cid not in args.ids:
            continue

        gt = json.loads((dossier / "ground_truth.json").read_text(encoding="utf-8"))
        profil = json.loads((dossier / "profil_cv.json").read_text(encoding="utf-8"))
        profil.update(COMPLEMENT_CV)

        debut = time.time()
        try:
            # --- Agent 3 ---
            sauvegarde = SORTIE / f"candidat_{cid}.json"
            if args.reutiliser and sauvegarde.exists():
                v3 = VerificationDocuments.model_validate_json(
                    sauvegarde.read_text(encoding="utf-8")
                )
            else:
                img_dip, img_cin = dossier / "diplome.jpg", dossier / "cin.jpg"
                v3 = sans_donnees_sensibles(verifier_documents(
                    profil,
                    image_diplome=str(img_dip) if img_dip.exists() else None,
                    image_cin=str(img_cin) if img_cin.exists() else None,
                ))
                sauvegarde.write_text(v3.model_dump_json(indent=2), encoding="utf-8")

            # --- Agent 4 ---
            r4 = faire_matching(OFFRE, profil, v3)

            erreurs = verifier_chaine(gt, v3, r4)
            diplome = next(d for d in r4.details if d.critere == "diplome_formation")
            source = "vérifié" if "diplôme vérifié" in diplome.justification else "CV (non vérifié)"
            statut = "OK" if not erreurs else "KO"
            n3, s3, s4 = v3.niveau_conformite, v3.score_coherence, r4.score_global
        except Exception as e:  # noqa: BLE001
            erreurs, statut, source = [f"exception : {e}"], "KO", ""
            n3, s3, s4 = "", "", ""

        duree = round(time.time() - debut, 1)
        print(f"[{statut}] candidat {cid:>2} | agent 3 : {n3} ({s3}) | "
              f"agent 4 : {s4} | diplôme {source} | {duree}s")
        for err in erreurs:
            print(f"        - {err}")

        lignes.append({
            "candidat": cid, "scenario": gt["scenario"], "statut": statut,
            "agent3_niveau": n3, "agent3_score": s3, "agent4_score": s4,
            "diplome_source": source, "erreurs": " ; ".join(erreurs), "duree_s": duree,
        })

    if not lignes:
        print("Aucun candidat à tester.")
        sys.exit(1)

    with open(SORTIE / "chaine_agent3_agent4.csv", "w", newline="",
              encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(lignes[0].keys()), delimiter=";")
        w.writeheader()
        w.writerows(lignes)

    ok = sum(1 for l in lignes if l["statut"] == "OK")
    print(f"\nChaîne OK : {ok}/{len(lignes)}  (détail : resultats/chaine_agent3_agent4.csv)")
    sys.exit(0 if ok == len(lignes) else 1)


if __name__ == "__main__":
    main()