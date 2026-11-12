"""Vérifie que les mocks de data/mocks/ respectent les schémas ET racontent la même histoire.
Lancer depuis la racine du dépôt :  python -m pytest agents/tests/test_mocks.py"""
import json
from pathlib import Path

import pytest

from agents.common.schemas import (ExigencesStructurees, ProfilCandidat, ResultatMatching,
                                   RapportCandidature, VerificationDocuments)

MOCKS = Path(__file__).resolve().parents[2] / "data" / "mocks"     


def charger(nom):
    return json.loads((MOCKS / nom).read_text(encoding="utf-8"))


def test_agents_1_et_2_respectent_leur_schema():
    ExigencesStructurees.model_validate(charger("agent1_exemple.json"))
    ProfilCandidat.model_validate(charger("agent2_exemple.json"))


@pytest.mark.parametrize("cas", ["conforme", "incoherent"])
def test_la_chaine_des_agents_raconte_la_meme_histoire(cas):
    a1 = ExigencesStructurees.model_validate(charger("agent1_exemple.json"))
    a2 = ProfilCandidat.model_validate(charger("agent2_exemple.json"))
    a3 = VerificationDocuments.model_validate(charger(f"agent3_exemple_{cas}.json"))
    a4 = ResultatMatching.model_validate(charger(f"agent4_exemple_{cas}.json"))
    a5 = RapportCandidature.model_validate(charger(f"agent5_exemple_{cas}.json"))

    coherence = next(d for d in a4.details if d.critere == "coherence_documents")
    assert coherence.score == a3.score_coherence, "cohérence agent 4 différente du score_coherence de l'agent 3"
    assert a5.score_global == a4.score_global, "score du rapport différent de celui de l'agent 4"
    assert a5.justification_score == a4.details, "justifications du rapport différentes du détail de l'agent 4"
    assert a5.incoherences == a3.incoherences, "incohérences du rapport différentes de celles de l'agent 3"
    assert set(a4.competences_manquantes) >= set(a1.competences_obligatoires) - set(a2.competences), \
        "compétences obligatoires manquantes non listées par l'agent 4"
    assert a3.infos_cin.nom.lower() == a2.nom.lower(), "nom de la CIN différent du nom du profil"
    assert a1.niveau_diplome_min is not None, "agent 1 : niveau_diplome_min attendu dans le mock"


