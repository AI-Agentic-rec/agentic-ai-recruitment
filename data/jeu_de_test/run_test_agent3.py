"""
Test de l'agent 3 sur le jeu de données généré par create_dataset.py.
Compare le résultat au ground_truth.json (succès technique ET métier).

Lancer (depuis la racine du projet) :
    $env:PYTHONUTF8 = "1"
    python data/jeu_de_test/run_test.py            # tous les candidats
    python data/jeu_de_test/run_test.py 11 12      # seulement ceux-là
"""
import sys
from pathlib import Path

# Racine du projet = 2 niveaux au-dessus de data/jeu_de_test/
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import csv
import difflib
import json
import time
import unicodedata
from datetime import date

from agents.agent3_document_verification.agent3 import (
    verifier_documents,
    sans_donnees_sensibles,
)

BASE = Path(__file__).parent / "candidats"
SORTIE = Path(__file__).parent / "resultats"
SORTIE.mkdir(exist_ok=True)


def norm(s) -> str:
    s = unicodedata.normalize("NFKD", str(s or "")).encode("ascii", "ignore").decode()
    return " ".join(s.lower().split())


def proche(a, b, seuil=0.85) -> bool:
    return difflib.SequenceMatcher(None, norm(a), norm(b)).ratio() >= seuil


def iso(d):
    if d and "/" in d:
        j, m, a = d.split("/")
        return f"{a}-{m}-{j}"
    return d


def verifier_champ(erreurs, label, lu, attendu, flou=False, seuil=0.85):
    """Valeur lue vs valeur affichée. Si le document est flou, null est accepté
    mais une valeur fausse ou inventée ne l'est jamais."""
    if attendu is None:
        if lu:
            erreurs.append(f"{label} inventé : {lu!r}")
    elif lu is None:
        if not flou:
            erreurs.append(f"{label} non lu")
    elif not proche(lu, attendu, seuil):
        erreurs.append(f"{label} : {lu!r} != {attendu!r}")


def evaluer(res, gt) -> dict:
    dip, cin = res.infos_diplome, res.infos_cin
    flou = gt.get("flou", False)
    erreurs = []

    # --- CIN ---
    if gt.get("cin_absente"):
        if "cin" not in res.documents_manquants:
            erreurs.append("CIN absente non signalée dans documents_manquants")
    elif cin is None:
        erreurs.append("CIN non extraite")
    else:
        verifier_champ(erreurs, "nom CIN", cin.nom, gt["nom_cin"])
        verifier_champ(erreurs, "prénom CIN", cin.prenom, gt["prenom"])
        if cin.date_expiration != iso(gt["date_expiration_cin"]):
            erreurs.append(f"expiration : {cin.date_expiration!r}")

    # --- Diplôme ---
    if dip is None:
        if not flou:
            erreurs.append("diplôme non extrait")
    else:
        verifier_champ(erreurs, "nom diplôme", dip.nom, gt["nom_diplome"], flou, 0.8)
        verifier_champ(erreurs, "établissement", dip.etablissement,
                       gt["etablissement"], flou, 0.8)

        annee = (dip.date_obtention or "")[:4] or None
        if gt["annee_obtention"] is None:
            if annee:
                erreurs.append(f"année inventée : {annee!r}")
        elif annee is None:
            if not flou:
                erreurs.append("année non lue")
        elif annee != gt["annee_obtention"]:
            erreurs.append(f"année : {annee!r} != {gt['annee_obtention']!r}")

    # --- Niveau de conformité ---
    if res.niveau_conformite not in gt["niveaux_acceptes"]:
        erreurs.append(
            f"niveau {res.niveau_conformite!r}, attendu {gt['niveaux_acceptes']}"
        )

    # --- Signaux attendus ---
    for mot in gt.get("signal_mots_cles", []):
        if not any(mot in norm(i.description) for i in res.incoherences):
            erreurs.append(f"signal absent : « {mot} »")
    if "signal_documents" in gt:
        attendus = sorted(gt["signal_documents"])
        if not any(sorted(i.documents) == attendus for i in res.incoherences):
            erreurs.append(f"incohérence {attendus} non détectée")
    if "signal_gravite" in gt:
        if not any(i.gravite == gt["signal_gravite"] for i in res.incoherences):
            erreurs.append(f"aucune incohérence de gravité {gt['signal_gravite']!r}")

    return {"ok": not erreurs, "erreurs": erreurs}


def main():
    ids = {int(x) for x in sys.argv[1:]}
    lignes = []

    for dossier in sorted(BASE.glob("candidat_*"),
                          key=lambda p: int(p.name.split("_")[1])):
        cid = int(dossier.name.split("_")[1])
        if ids and cid not in ids:
            continue

        gt = json.loads((dossier / "ground_truth.json").read_text(encoding="utf-8"))
        profil = json.loads((dossier / "profil_cv.json").read_text(encoding="utf-8"))

        img_dip = dossier / "diplome.jpg"
        img_cin = dossier / "cin.jpg"

        debut = time.time()
        try:
            res = verifier_documents(
                profil,
                image_diplome=str(img_dip) if img_dip.exists() else None,
                image_cin=str(img_cin) if img_cin.exists() else None,
                aujourdhui=date.today(),
            )
            technique = "SUCCES"
            ev = evaluer(res, gt)
            # Sortie telle que transmise aux agents 4 et 5.
            (SORTIE / f"candidat_{cid}.json").write_text(
                sans_donnees_sensibles(res).model_dump_json(indent=2),
                encoding="utf-8",
            )
            niveau, score = res.niveau_conformite, res.score_coherence
        except Exception as e:  # noqa: BLE001
            technique = "ECHEC"
            ev = {"ok": False, "erreurs": [f"exception : {e}"]}
            niveau, score = "", ""

        duree = round(time.time() - debut, 2)
        metier = "OK" if ev["ok"] else "KO"
        print(f"[{metier}] candidat {cid:>2} | {technique} | {niveau} ({score}) | {duree}s")
        for err in ev["erreurs"]:
            print(f"        - {err}")

        lignes.append({
            "candidat": cid,
            "scenario": gt["scenario"],
            "succes_technique": technique,
            "succes_metier": metier,
            "niveau_obtenu": niveau,
            "score": score,
            "niveaux_acceptes": "|".join(gt["niveaux_acceptes"]),
            "erreurs": " ; ".join(ev["erreurs"]),
            "duree_s": duree,
        })

    if not lignes:
        print("Aucun candidat à tester.")
        sys.exit(1)

    # utf-8-sig : accents corrects à l'ouverture dans Excel.
    with open(SORTIE / "resume_tests.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(lignes[0].keys()), delimiter=";")
        w.writeheader()
        w.writerows(lignes)

    ok = sum(1 for l in lignes if l["succes_metier"] == "OK")
    print(f"\nSuccès métier : {ok}/{len(lignes)}  (détail : resultats/resume_tests.csv)")
    sys.exit(0 if ok == len(lignes) else 1)


if __name__ == "__main__":
    main()