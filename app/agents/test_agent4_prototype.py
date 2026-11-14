"""Tests du prototype de l'agent 4 SANS Ollama (faux modèle).  Lancer : python test_agent4_prototype.py"""
import json
from agent4_prototype import (PONDERATIONS, apparier_competences, calculer_matching, dossier_samples, niveau_langue,
                              score_diplome, score_experience, score_langues)
from schemas import (CRITERES, ExigencesStructurees, Langue, ProfilCandidat, ResultatMatching, VerificationDocuments)

S = dossier_samples()
charger = lambda nom: json.loads((S / nom).read_text(encoding="utf-8"))


def faux(obligatoires=(), souhaitees=()):
    """Faux modèle qui répond avec les correspondances données : {exigee: trouvee}."""
    corps = {"obligatoires": [{"exigee": e, "trouvee": t} for e, t in dict(obligatoires).items()],
             "souhaitees": [{"exigee": e, "trouvee": t} for e, t in dict(souhaitees).items()]}
    return lambda modele, system, messages, schema: json.dumps(corps)


def interdit(*a):
    raise AssertionError("le modèle ne devait pas être appelé")


AUCUNE = faux({"Docker": None}, {"Celery": None, "AWS": None})     # le modèle ne reconnaît rien de plus


def test_les_deux_chaines_donnent_exactement_les_scores_des_mocks():
    if S is None:
        return
    ex, pr = ExigencesStructurees.model_validate(charger("agent1_exemple.json")), ProfilCandidat.model_validate(charger("agent2_exemple.json"))
    for cas in ("conforme", "incoherent"):
        attendu = ResultatMatching.model_validate(charger(f"agent4_exemple_{cas}.json"))
        r = calculer_matching(ex, pr, VerificationDocuments.model_validate(charger(f"agent3_exemple_{cas}.json")), llm=AUCUNE)
        assert r.score_global == attendu.score_global
        assert [(d.critere, d.score) for d in r.details] == [(d.critere, d.score) for d in attendu.details]
        assert (r.competences_correspondantes, r.competences_manquantes) == (attendu.competences_correspondantes, attendu.competences_manquantes)
        assert (r.diplome_conforme, r.experience_candidat_annees) == (attendu.diplome_conforme, attendu.experience_candidat_annees)


def test_ponderations_de_la_fiche():
    assert sum(PONDERATIONS.values()) == 100 and set(PONDERATIONS) == set(CRITERES)
    assert PONDERATIONS == {"competences_obligatoires": 40, "experience": 20, "diplome_formation": 15,
                            "competences_souhaitees": 10, "langues": 5, "coherence_documents": 10}


def test_correspondances_exactes_sans_appeler_le_modele():
    assert apparier_competences(["python", "SQL"], ["Postgresql"], ["Python", "sql", "PostgreSQL"], llm=interdit) == \
        {"python": "Python", "SQL": "sql", "Postgresql": "PostgreSQL"}


def test_le_modele_ne_voit_que_les_competences_restantes():
    vus = []
    def llm(modele, system, messages, schema):
        vus.append(messages[0]["content"]); return json.dumps({"obligatoires": [{"exigee": "JavaScript", "trouvee": "JS"}], "souhaitees": []})
    r = apparier_competences(["Python", "JavaScript"], [], ["Python", "JS"], llm=llm)
    assert r == {"Python": "Python", "JavaScript": "JS"} and '"JavaScript"' in vus[0] and '"Python"' not in vus[0].split("competences_du_candidat")[0]


def test_garde_fou_une_competence_inventee_par_le_modele_est_refusee():
    r = apparier_competences(["Docker"], [], ["Python"], llm=faux({"Docker": "Kubernetes"}))     # Kubernetes n'est pas dans le profil
    assert r == {"Docker": None}


def test_exigee_recopiee_avec_une_autre_casse_est_acceptee():
    assert apparier_competences(["JavaScript"], [], ["JS"], llm=faux({"javascript": "JS"})) == {"JavaScript": "JS"}


def test_sans_modele_pas_d_appel():
    assert apparier_competences(["Docker"], [], ["Python"], llm=interdit, utiliser_modele=False) == {"Docker": None}


def test_experience():
    assert score_experience(3, 3)[0] == 100.0 and score_experience(3, 1.5)[0] == 50.0 and score_experience(0, 0)[0] == 100.0
    assert score_experience(3, 5)[0] == 100.0


def test_experience_recalculee_depuis_les_durees_si_le_total_est_absent():
    pr = ProfilCandidat.model_validate({"experiences": [{"poste": "a", "duree_annees": 1.5}, {"poste": "b", "duree_annees": 2}]})
    r = calculer_matching(ExigencesStructurees(experience_min_annees=3), pr, None, llm=interdit)
    assert r.experience_candidat_annees == 3.5


def test_diplome():
    assert score_diplome(5, 5, "x")[::2] == (100.0, True) and score_diplome(5, 7, "x")[::2] == (100.0, True)
    assert score_diplome(5, 3, "x")[::2] == (40.0, False) and score_diplome(5, 2, "x")[::2] == (10.0, False)
    assert score_diplome(8, 2, "x")[0] == 0.0
    assert score_diplome(None, None, "")[::2] == (100.0, True) and score_diplome(5, None, "")[::2] == (0.0, False)


def test_le_diplome_verifie_prime_sur_le_cv():
    pr = ProfilCandidat.model_validate({"formations": [{"diplome": "Master"}]})
    ver = VerificationDocuments.model_validate({"infos_diplome": {"diplome": "Licence"}, "niveau_conformite": "non_conforme", "score_coherence": 50, "resume": "x"})
    assert calculer_matching(ExigencesStructurees(niveau_diplome_min=5), pr, ver, llm=interdit).diplome_conforme is False
    assert calculer_matching(ExigencesStructurees(niveau_diplome_min=5), pr, None, llm=interdit).diplome_conforme is True   # sans vérification : CV


def test_langues():
    L = lambda l, n=None: Langue(langue=l, niveau=n)
    assert score_langues([L("Anglais", "B2")], [L("anglais", "B2")])[0] == 100.0
    assert score_langues([L("Français", "courant")], [L("Français", "langue maternelle")])[0] == 100.0
    assert score_langues([L("Anglais", "B2")], [L("Anglais", "B1")])[0] == 75.0          # 3 / 4
    assert score_langues([L("Anglais", "B2")], [L("Anglais")])[0] == 50.0                # niveau non précisé
    assert score_langues([L("Anglais"), L("Arabe")], [L("Anglais", "A1")])[0] == 50.0    # une langue absente
    assert score_langues([], [])[0] == 100.0 and niveau_langue("Courant") == 5 and niveau_langue(None) is None


def test_sans_verification_la_coherence_vaut_zero():
    r = calculer_matching(ExigencesStructurees(), ProfilCandidat(), None, llm=interdit)
    assert next(d for d in r.details if d.critere == "coherence_documents").score == 0.0


def test_aucune_exigence_donne_100_partout_sauf_la_coherence():
    ver = VerificationDocuments.model_validate({"niveau_conformite": "conforme", "score_coherence": 100, "resume": "x"})
    r = calculer_matching(ExigencesStructurees(), ProfilCandidat(), ver, llm=interdit)
    assert r.score_global == 100.0 and r.competences_correspondantes == [] and r.competences_manquantes == []


if __name__ == "__main__":
    for nom, f in list(globals().items()):
        if nom.startswith("test_"):
            f(); print("OK ", nom)
