import asyncio
import json
import sys
from pathlib import Path

# Ajoute la racine du projet au path
RACINE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RACINE))

from backend.orchestrateur.orchestrator_langgraph import run_workflow

BASE_CANDIDATS = RACINE / "data" / "jeu_de_test" / "candidats"

# --- Offre 1 écrite directement (plus besoin du fichier .txt) ---
OFFRE_1 = """OFFRE D'EMPLOI (DOCUMENT FICTIF)

Poste : Développeur Python

Missions
- Développer des API REST
- Maintenir les scripts d'automatisation

Profil recherché
- Licence en informatique ou équivalent
- Minimum 2 ans d'expérience

Compétences requises
Python, SQL, Docker

Compétences appréciées
Git

Langues
Anglais niveau B2
"""


async def main():
    # --- Vérification des fichiers du candidat 1 ---
    dossier = BASE_CANDIDATS / "candidat_1"
    cv_path = str(dossier / "cv.pdf")
    diplome_path = str(dossier / "diplome.jpg")
    cin_path = str(dossier / "cin.jpg")

    print("=" * 60)
    print(f"Candidat   : {dossier}")
    print(f"CV         : {cv_path} (existe : {Path(cv_path).exists()})")
    print(f"Diplôme    : {diplome_path} (existe : {Path(diplome_path).exists()})")
    print(f"CIN        : {cin_path} (existe : {Path(cin_path).exists()})")
    print("=" * 60)

    if not (Path(cv_path).exists() and Path(diplome_path).exists() and Path(cin_path).exists()):
        print("⚠️  ATTENTION : certains fichiers sont manquants.")
        print("Vérifie le contenu du dossier candidat_1 avec :")
        print(f"  Get-ChildItem {dossier}")
        return

    print("\nLancement de l'orchestrateur (peut prendre 2 à 3 minutes)...\n")

    result = await run_workflow(
        job_description=OFFRE_1,
        cv_path=cv_path,
        diplome_path=diplome_path,
        cin_path=cin_path,
        candidate_id="1",
        job_id="1",
    )

    print("\n" + "=" * 60)
    print("RÉSULTAT FINAL")
    print("=" * 60)
    print(f"Statut final  : {result['status']}")
    print(f"Erreurs       : {result['errors']}")

    print("\n--- Statut de chaque agent ---")
    for agent_id, state in result["agent_states"].items():
        duree = state.get("duration_seconds")
        erreur = state.get("error")
        print(f"{agent_id} : {state['status']} | essais: {state['attempts']} | "
              f"durée: {duree}s" + (f" | erreur: {erreur}" if erreur else ""))

    print("\n--- Contenu des résultats (résumé) ---")
    results = result.get("results", {})
    for cle, valeur in results.items():
        print(f"\n▶ {cle.upper()} :")
        print(json.dumps(valeur, indent=2, ensure_ascii=False)[:1500])


if __name__ == "__main__":
    asyncio.run(main())