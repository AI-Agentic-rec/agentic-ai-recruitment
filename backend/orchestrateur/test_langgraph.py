import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
DOSSIER = Path(__file__).resolve().parent
sys.path.insert(0, str(RACINE))
sys.path.insert(0, str(DOSSIER))

import asyncio
import json

from orchestrator_langgraph import run_workflow


async def test_workflow():

    paires = [
        (1, 1, "Nominal"),
        (1, 2, "Diplôme insuffisant"),
        (8, 5, "CIN expirée + offre minimaliste"),
        (12, 1, "CIN absente"),
    ]

    base = RACINE / "data" / "jeu_de_test" / "candidats"

    for cand_id, offre_id, description in paires:

        print(f"\n{'=' * 70}")
        print(f"Candidat {cand_id} × Offre {offre_id} — {description}")
        print(f"{'=' * 70}")

        dossier = base / f"candidat_{cand_id}"
        cin_file = dossier / "cin.jpg"
        cin_path = str(cin_file) if cin_file.exists() else None

        try:
            result = await run_workflow(
                job_description=(base / "offres" / f"offre_{offre_id}.txt").read_text(encoding="utf-8"),
                cv_path=str(dossier / "cv.pdf"),
                diplome_path=str(dossier / "diplome.jpg"),
                cin_path=cin_path,
                candidate_id=f"CANDIDAT_{cand_id:03d}",
                job_id=f"OFFRE_{offre_id:03d}",
            )

            print(f"Status       : {result['status']}")
            print(f"Fin          : {result['finished_at']}")

            for agent_id, state in result["agent_states"].items():
                print(
                    f"  {agent_id}: {state['status']:12} "
                    f"({state['attempts']} tentative(s), "
                    f"{state['duration_seconds']}s)"
                )

            if "matching" in result["results"]:
                print(f"  Score global : "
                      f"{result['results']['matching']['score_global']}/100")
            if "rapport" in result["results"]:
                print(f"  Avis : "
                      f"{result['results']['rapport']['avis_indicatif']}")

            if result["errors"]:
                print(f"  ERREURS : {result['errors']}")

        except Exception as e:
            print(f"EXCEPTION : {type(e).__name__}: {e}")

    print("\n\n" + "=" * 70)
    print("DÉTAIL CANDIDAT 1 × OFFRE 1")
    print("=" * 70)

    dossier = base / "candidat_1"

    result = await run_workflow(
        job_description=(base / "offres" / "offre_1.txt").read_text(encoding="utf-8"),
        cv_path=str(dossier / "cv.pdf"),
        diplome_path=str(dossier / "diplome.jpg"),
        cin_path=str(dossier / "cin.jpg"),
        candidate_id="CANDIDAT_001",
        job_id="OFFRE_001",
    )

    print("\n--- LOGS ---")
    for log in result["logs"]:
        print(
            f"[{log['timestamp'][:19]}] "
            f"{log['agent']:35} | "
            f"{log['event']:20} | "
            f"{log['message']}"
        )

    print("\n--- RAPPORT FINAL ---")
    if "rapport" in result["results"]:
        print(json.dumps(result["results"]["rapport"], indent=2, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(test_workflow())