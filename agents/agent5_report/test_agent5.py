"""Tests de l'agent 5 complet SANS Ollama (faux modèle).
Lancer depuis la racine du dépôt :  python -m pytest agents/agent5_report/test_agent5.py -v

Correspondance avec la liste du cahier des charges (section 8) :
1 résumé · 2 conclusion · 3 points forts · 4 points manquants · 5 incohérences · 6 score exact · 7 détail exact ·
8 exclusion du CIN · 9 entrées manquantes/invalides · 10 erreurs et réponses invalides du LLM ·
11 validation RapportCandidature · 12 rappel de la décision du recruteur."""
import copy
import json
import logging

import pytest

from agents.agent5_report import agent5_prototype as proto
from agents.agent5_report.agent5 import (executer_agent5, generer_rapport, generer_rapport_avec_trace,
                                         rediger_repli, valider_entree)
from agents.agent5_report.erreurs_agent5 import (Agent5Error, EntreeInvalideError, ErreurLLM,
                                                 FuiteDonneesSensiblesError, RedactionInvalideError)
from agents.common.schemas import (ContexteCandidature, ExigencesStructurees, Incoherence, ProfilCandidat, RapportCandidature,
                                   ResultatMatching, VerificationDocuments)

CIN = "AB123456"
DECISION = "La décision finale appartient au responsable du recrutement."


# ---------------------------------------------------------------- outils
def chaine(cas="conforme"):
    return proto.charger_chaine(cas)


def entrees(cas="conforme"):
    a1, a2, a3, a4, attendu = chaine(cas)
    return a1, a2, a3, a4, attendu


def faux_llm(score="85.3", resume=None, conclusion=None, trace=None):
    def llm(modele, system, messages, schema):
        if trace is not None:
            trace.append({"system": system, "messages": messages})
        return json.dumps({
            "resume": resume if resume is not None else f"Sara Benali obtient {score}/100 pour le poste de Développeur Python. "
                                                        "Le profil couvre la plupart des exigences, Docker n'étant pas identifié.",
            "conclusion": conclusion if conclusion is not None else "Profil globalement adapté ; Docker pourra être vérifié en "
                                                                    "entretien. La décision finale appartient au recruteur."},
            ensure_ascii=False)
    return llm


def llm_qui_echoue(*_):
    raise ConnectionError("serveur Ollama éteint")


def matching_avec_scores(**scores):
    """ResultatMatching valide (score global recalculé) dont on fixe le score de certains critères."""
    _, _, _, a4, _ = chaine()
    donnees = a4.model_dump()
    for d in donnees["details"]:
        d["score"] = scores.get(d["critere"], d["score"])
    donnees["score_global"] = round(sum(d["ponderation"] * d["score"] / 100 for d in donnees["details"]), 1)
    return ResultatMatching.model_validate(donnees)


# ================================================================ 1. et 2. résumé et conclusion
def test_01_le_resume_est_celui_du_modele_valide():
    a1, a2, a3, a4, _ = entrees()
    rapport, trace = generer_rapport_avec_trace(a1, a2, a3, a4, llm=faux_llm())
    assert rapport.resume.startswith("Sara Benali obtient 85.3/100") and trace.redaction == "llm"


def test_02_la_conclusion_est_celle_du_modele_valide():
    a1, a2, a3, a4, _ = entrees()
    rapport = generer_rapport(a1, a2, a3, a4, llm=faux_llm(conclusion="Dossier solide, à confirmer en entretien. "
                                                                      "La décision finale appartient au recruteur."))
    assert rapport.conclusion == "Dossier solide, à confirmer en entretien. La décision finale appartient au recruteur."


# ================================================================ 3. points forts
def test_03_points_forts_assembles_par_le_code_depuis_les_resultats_des_agents():
    a1, a2, a3, a4, _ = entrees()
    forts = generer_rapport(a1, a2, a3, a4, llm=faux_llm()).points_forts
    texte = " | ".join(forts)
    assert "Python, SQL, FastAPI, Git" in texte and "PostgreSQL" in texte
    assert "3 ans d'expérience" in texte and "Master Informatique (vérifié)" in texte
    assert "Français (courant), Anglais (B2)" in texte and "cohérents entre eux" in texte
    assert "Docker" not in texte                                       # un manque n'est jamais un point fort


def test_03b_le_modele_ne_peut_pas_inventer_de_competence():
    a1, a2, a3, a4, _ = entrees()
    ref = generer_rapport(a1, a2, a3, a4, llm=faux_llm()).points_forts
    invention = faux_llm(resume="Sara Benali obtient 85.3/100 et maîtrise Kubernetes, Rust et Scala à la perfection.")
    rapport, trace = generer_rapport_avec_trace(a1, a2, a3, a4, llm=invention)
    assert trace.redaction == "repli" and "Kubernetes" not in rapport.resume       # texte refusé, repli par gabarit
    assert rapport.points_forts == ref and "Kubernetes" not in " ".join(rapport.points_forts)


# ================================================================ 4. points manquants
def test_04_points_manquants_assembles_par_le_code():
    a1, a2, a3, a4, _ = entrees()
    manques = generer_rapport(a1, a2, a3, a4, llm=faux_llm()).points_manquants
    assert manques == ["Compétence obligatoire non identifiée dans le CV : Docker",
                       "Compétences souhaitées non identifiées dans le CV : Celery, AWS"]


def test_04b_diplome_experience_langues_et_documents_manquants():
    a1, a2, a3, a4, _ = entrees("incoherent")
    a1 = a1.model_copy(update={"experience_min_annees": 5.0})
    a3 = a3.model_copy(update={"documents_manquants": ["diplome"], "documents_illisibles": ["cin"]})
    d = a4.model_dump()
    for det in d["details"]:
        if det["critere"] == "experience":
            det["score"] = 60.0
        if det["critere"] == "langues":
            det["score"], det["justification"] = 50.0, "Anglais : niveau insuffisant."
    d["score_global"] = round(sum(x["ponderation"] * x["score"] / 100 for x in d["details"]), 1)
    manques = " | ".join(generer_rapport(a1, a2, a3, ResultatMatching.model_validate(d), llm=faux_llm(score=str(d["score_global"]))).points_manquants)
    assert "Diplôme non conforme" in manques and "Licence (Bac+3)" in manques
    assert "Expérience insuffisante : 3 ans pour 5 demandé(s)" in manques
    assert "Anglais : niveau insuffisant." in manques
    assert "non fourni(s) : diplome" in manques and "illisible(s), non analysé(s) : cin" in manques


def test_04c_sans_verification_le_manque_est_signale_sans_erreur():
    a1, a2, _, a4, _ = entrees()
    rapport = generer_rapport(a1, a2, None, a4, llm=faux_llm())
    assert any("Vérification des documents non disponible" in m for m in rapport.points_manquants)
    assert rapport.incoherences == []


# ================================================================ 5. incohérences
def test_05_incoherences_reprises_de_l_agent_3_sans_modification():
    a1, a2, a3, a4, attendu = entrees("incoherent")
    rapport = generer_rapport(a1, a2, a3, a4, llm=faux_llm(score="71.3"))
    assert rapport.incoherences == a3.incoherences == attendu.incoherences and len(rapport.incoherences) == 2
    assert [i.gravite for i in rapport.incoherences] == ["faible", "elevee"]


def test_05b_aucune_incoherence_quand_les_documents_sont_conformes():
    a1, a2, a3, a4, _ = entrees("conforme")
    assert generer_rapport(a1, a2, a3, a4, llm=faux_llm()).incoherences == []


def test_05c_le_modele_ne_voit_les_incoherences_que_comme_faits():
    a1, a2, a3, a4, _ = entrees("incoherent")
    trace = []
    generer_rapport(a1, a2, a3, a4, llm=faux_llm(score="71.3", trace=trace))
    donnees = json.loads(trace[0]["messages"][0]["content"])
    assert [i["gravite"] for i in donnees["incoherences"]] == ["faible", "elevee"]


# ================================================================ 6. et 7. score et détail identiques à l'Agent 4
@pytest.mark.parametrize("cas", ["conforme", "incoherent"])
def test_06_le_score_global_est_exactement_celui_de_l_agent_4(cas):
    a1, a2, a3, a4, _ = entrees(cas)
    rapport = generer_rapport(a1, a2, a3, a4, llm=faux_llm(score=str(a4.score_global)))
    assert rapport.score_global == a4.score_global and type(rapport.score_global) is type(a4.score_global)


def test_06b_un_score_different_cite_par_le_modele_est_refuse_le_score_du_rapport_reste_celui_de_l_agent_4():
    a1, a2, a3, a4, _ = entrees()
    rapport, trace = generer_rapport_avec_trace(a1, a2, a3, a4, llm=faux_llm(score="99.9"))
    assert rapport.score_global == 85.3 and "99.9" not in rapport.resume
    assert trace.redaction == "repli" and "85.3/100" in rapport.resume


@pytest.mark.parametrize("cas", ["conforme", "incoherent"])
def test_07_le_detail_du_score_est_strictement_identique_a_celui_de_l_agent_4(cas):
    a1, a2, a3, a4, _ = entrees(cas)
    rapport = generer_rapport(a1, a2, a3, a4, llm=faux_llm(score=str(a4.score_global)))
    assert rapport.justification_score == a4.details                     # mêmes critères, pondérations, scores, textes, ordre
    assert [d.model_dump() for d in rapport.justification_score] == [d.model_dump() for d in a4.details]
    assert rapport.justification_score is not a4.details and rapport.justification_score[0] is not a4.details[0]


def test_07b_modifier_le_rapport_ne_modifie_pas_l_agent_4():
    a1, a2, a3, a4, _ = entrees()
    avant = a4.model_dump()
    rapport = generer_rapport(a1, a2, a3, a4, llm=faux_llm())
    rapport.justification_score[0].score = 0.0
    assert a4.model_dump() == avant


# ================================================================ 8. exclusion du CIN
def test_08_le_cin_n_est_jamais_envoye_au_modele_ni_dans_le_rapport_ni_dans_les_logs(caplog):
    a1, a2, a3, a4, _ = entrees("incoherent")
    assert a3.infos_cin.numero_cin == CIN
    trace = []
    with caplog.at_level(logging.DEBUG):
        rapport = generer_rapport(a1, a2, a3, a4, llm=faux_llm(score="71.3", trace=trace),
                                  contexte=ContexteCandidature(candidate_id="c-42", job_id="j-7"))
    assert CIN not in json.dumps(trace, ensure_ascii=False)
    assert CIN not in rapport.model_dump_json()
    journal = "\n".join(r.getMessage() for r in caplog.records)
    assert "c-42" in journal                                              # les identifiants techniques sont loggés...
    assert CIN not in journal and "Benali" not in journal and "sara.benali" not in journal   # ...pas les données personnelles


def test_08b_le_cin_ecrit_dans_un_texte_des_agents_est_masque_partout():
    a1, a2, a3, a4, _ = entrees("incoherent")
    a3.incoherences[0].description = f"La CIN {CIN} ne correspond pas au CV."
    d = a4.model_dump()
    d["details"][0]["justification"] += f" (pièce {CIN})"
    a4 = ResultatMatching.model_validate(d)
    trace = []
    rapport = generer_rapport(a1, a2, a3, a4, llm=faux_llm(score="71.3", trace=trace))
    assert CIN not in json.dumps(trace, ensure_ascii=False) and CIN not in rapport.model_dump_json()
    assert proto.MASQUE_CIN in rapport.incoherences[0].description


def test_08c_une_fuite_detectee_bloque_l_envoi_et_n_est_pas_masquee_par_le_repli(monkeypatch):
    a1, a2, a3, a4, _ = entrees()
    a3 = a3.model_copy(update={"incoherences": [Incoherence(type="identite", description=f"CIN {CIN}", gravite="faible")]})
    monkeypatch.setattr(proto, "_masquer_recursif", lambda objet, numero: objet)     # simule un masquage défaillant
    monkeypatch.setattr(proto, "masquer_cin", lambda texte, numero=None: texte)
    appels = []
    with pytest.raises(FuiteDonneesSensiblesError):
        generer_rapport(a1, a2, a3, a4, llm=faux_llm(trace=appels))
    assert appels == []                                                   # le modèle n'a jamais été appelé


def test_08d_aucune_autre_donnee_personnelle_n_est_transmise():
    a1, a2, a3, a4, _ = entrees("incoherent")
    trace = []
    generer_rapport(a1, a2, a3, a4, llm=faux_llm(score="71.3", trace=trace))
    vu = json.dumps(trace, ensure_ascii=False)
    for secret in (a2.email, a2.telephone, a3.infos_cin.date_naissance, a3.infos_cin.numero_cin):
        assert secret not in vu


def test_08e_l_entree_de_l_agent_3_n_est_pas_modifiee():
    a1, a2, a3, a4, _ = entrees("incoherent")
    avant = a3.model_dump()
    generer_rapport(a1, a2, a3, a4, llm=faux_llm(score="71.3"))
    assert a3.model_dump() == avant and a3.infos_cin.numero_cin == CIN


# ================================================================ 9. entrées manquantes ou invalides
@pytest.mark.parametrize("position", [0, 1, 3])
def test_09_une_entree_obligatoire_manquante_leve_une_erreur_claire(position):
    a1, a2, a3, a4, _ = entrees()
    args = [a1, a2, a3, a4]
    args[position] = None
    with pytest.raises(EntreeInvalideError, match="Entrée manquante"):
        generer_rapport(*args, llm=faux_llm())


def test_09b_dictionnaires_json_acceptes_et_types_invalides_refuses():
    a1, a2, a3, a4, _ = entrees()
    rapport = generer_rapport(a1.model_dump(), a2.model_dump(), a3.model_dump(), a4.model_dump(), llm=faux_llm())
    assert rapport.score_global == 85.3
    with pytest.raises(EntreeInvalideError, match="doit être"):
        generer_rapport("pas un objet", a2, a3, a4, llm=faux_llm())
    with pytest.raises(EntreeInvalideError):
        generer_rapport(a1, a2, a3, 42, llm=faux_llm())


def test_09c_un_dictionnaire_invalide_est_refuse_sans_reveler_les_valeurs():
    a1, a2, a3, a4, _ = entrees()
    mauvais = a3.model_dump()
    mauvais["infos_cin"]["numero_cin"] = CIN
    mauvais["champ_inconnu"] = CIN
    with pytest.raises(EntreeInvalideError) as exc:
        generer_rapport(a1, a2, mauvais, a4, llm=faux_llm())
    assert "champ_inconnu" in str(exc.value) and CIN not in str(exc.value)


def test_09d_un_matching_incoherent_est_refuse_par_le_schema_de_l_agent_4():
    a1, a2, a3, a4, _ = entrees()
    mauvais = a4.model_dump()
    mauvais["score_global"] = 12.0                                        # ne correspond pas à la somme pondérée
    with pytest.raises(EntreeInvalideError, match="agent4"):
        generer_rapport(a1, a2, a3, mauvais, llm=faux_llm())


def test_09e_executer_agent5_exige_un_dictionnaire_et_les_quatre_sorties():
    a1, a2, a3, a4, _ = entrees()
    with pytest.raises(EntreeInvalideError):
        executer_agent5([a1, a2, a3, a4])
    with pytest.raises(EntreeInvalideError, match="agent4"):
        executer_agent5({"agent1": a1, "agent2": a2, "agent3": a3})
    rapport = executer_agent5({"agent1": a1, "agent2": a2, "agent3": a3, "agent4": a4}, llm=faux_llm())
    assert isinstance(rapport, RapportCandidature)


def test_09f_les_champs_optionnels_absents_sont_geres():
    vide = ProfilCandidat()                                               # ni nom, ni prénom
    a1 = ExigencesStructurees()                                           # aucun titre, aucune exigence
    _, _, _, a4, _ = entrees()
    rapport = generer_rapport(a1, vide, None, a4, llm=llm_qui_echoue)
    assert rapport.resume.startswith("Le candidat obtient 85.3/100 pour le poste proposé.")


# ================================================================ 10. erreurs et réponses invalides du LLM
def test_10_modele_indisponible_repli_par_gabarit_et_rapport_valide():
    a1, a2, a3, a4, _ = entrees("incoherent")
    rapport, trace = generer_rapport_avec_trace(a1, a2, a3, a4, llm=llm_qui_echoue)
    assert trace.redaction == "repli" and "ErreurLLM" in trace.cause_repli
    assert rapport.resume.startswith("Sara Benali obtient 71.3/100 pour le poste de Développeur Python.")
    assert "2 incohérence(s)" in rapport.resume and "examen approfondi" in rapport.conclusion
    RapportCandidature.model_validate(rapport.model_dump())


@pytest.mark.parametrize("brut", ["ceci n'est pas du JSON", "{}", '{"resume": "seulement"}', '{"resume": 1, "conclusion": 2}', ""])
def test_10b_reponse_json_invalide_trois_essais_puis_repli(brut):
    a1, a2, a3, a4, _ = entrees()
    appels = []
    llm = lambda m, s, msgs, sch: (appels.append(1), brut)[1]
    rapport, trace = generer_rapport_avec_trace(a1, a2, a3, a4, llm=llm)
    assert trace.redaction == "repli" and len(appels) == 3                  # 3 essais JSON puis repli
    assert rapport.score_global == 85.3


def test_10c_texte_qui_viole_une_regle_une_nouvelle_tentative_puis_repli():
    a1, a2, a3, a4, _ = entrees()
    appels = []
    mauvais = faux_llm(score="12.5", trace=appels)
    _, trace = generer_rapport_avec_trace(a1, a2, a3, a4, llm=mauvais)
    assert len(appels) == proto.MAX_TENTATIVES_REDACTION and trace.redaction == "repli"


def test_10d_une_seconde_tentative_peut_reussir():
    a1, a2, a3, a4, _ = entrees()
    reponses = [faux_llm(score="12.5"), faux_llm()]
    llm = lambda *a: reponses.pop(0)(*a)
    rapport, trace = generer_rapport_avec_trace(a1, a2, a3, a4, llm=llm)
    assert trace.redaction == "llm" and "85.3/100" in rapport.resume


def test_10e_sans_repli_l_erreur_est_levee_pour_l_orchestrateur():
    a1, a2, a3, a4, _ = entrees()
    with pytest.raises(ErreurLLM):
        generer_rapport(a1, a2, a3, a4, llm=llm_qui_echoue, repli=False)
    with pytest.raises(RedactionInvalideError):
        generer_rapport(a1, a2, a3, a4, llm=faux_llm(score="1.0"), repli=False)
    assert issubclass(ErreurLLM, Agent5Error)


def test_10f_le_modele_ne_peut_pas_prendre_de_decision_de_recrutement():
    a1, a2, a3, a4, _ = entrees()
    llm = faux_llm(conclusion="Il faut embaucher ce candidat immédiatement, sans autre vérification.")
    rapport, trace = generer_rapport_avec_trace(a1, a2, a3, a4, llm=llm)
    assert trace.redaction == "repli" and "embauch" not in rapport.conclusion.lower()


def test_10g_le_message_d_erreur_ne_contient_aucune_donnee_personnelle():
    a1, a2, a3, a4, _ = entrees("incoherent")
    _, trace = generer_rapport_avec_trace(a1, a2, a3, a4, llm=llm_qui_echoue)
    assert CIN not in (trace.cause_repli or "") and "Benali" not in (trace.cause_repli or "")


# ================================================================ 11. validation avec RapportCandidature
@pytest.mark.parametrize("cas, score", [("conforme", "85.3"), ("incoherent", "71.3")])
def test_11_le_rapport_respecte_le_schema_et_les_references(cas, score):
    a1, a2, a3, a4, attendu = entrees(cas)
    rapport = generer_rapport(a1, a2, a3, a4, llm=faux_llm(score=score))
    assert isinstance(rapport, RapportCandidature)
    assert RapportCandidature.model_validate(rapport.model_dump()) == rapport
    assert RapportCandidature.model_validate_json(rapport.model_dump_json()) == rapport
    assert set(rapport.model_dump()) == set(attendu.model_dump())        # mêmes champs, aucun en trop (extra="forbid")
    assert (rapport.avis_indicatif, rapport.score_global, rapport.incoherences, rapport.justification_score) == \
           (attendu.avis_indicatif, attendu.score_global, attendu.incoherences, attendu.justification_score)


def test_11b_les_six_criteres_et_les_ponderations_sont_conserves():
    a1, a2, a3, a4, _ = entrees()
    rapport = generer_rapport(a1, a2, a3, a4, llm=faux_llm())
    assert [d.critere for d in rapport.justification_score] == [d.critere for d in a4.details]
    assert sum(d.ponderation for d in rapport.justification_score) == 100


# ================================================================ 12. rappel de la décision du recruteur
@pytest.mark.parametrize("llm", [faux_llm(), faux_llm(conclusion="Profil globalement adapté au poste, à confirmer."),
                                 llm_qui_echoue])
def test_12_le_rapport_rappelle_que_la_decision_appartient_au_recruteur(llm):
    a1, a2, a3, a4, _ = entrees()
    rapport = generer_rapport(a1, a2, a3, a4, llm=llm)
    assert rapport.decision_finale == DECISION
    assert "recruteur" in rapport.conclusion.lower() or "responsable du recrutement" in rapport.conclusion.lower()


def test_12b_la_decision_finale_ne_peut_pas_etre_remplacee_par_le_modele():
    a1, a2, a3, a4, _ = entrees()
    assert generer_rapport(a1, a2, a3, a4, llm=faux_llm()).decision_finale == RapportCandidature.model_fields["decision_finale"].default


# ================================================================ règles de l'avis indicatif
@pytest.mark.parametrize("scores, attendu", [
    ({}, "favorable"),                                                    # 85.3
    ({"competences_obligatoires": 0.0}, "a_etudier"),                     # critère obligatoire à 0 -> jamais favorable
    ({"competences_obligatoires": 60.0, "experience": 60.0, "diplome_formation": 40.0, "coherence_documents": 50.0}, "a_etudier"),   # 55.3
    ({"competences_obligatoires": 40.0, "experience": 20.0, "diplome_formation": 20.0, "competences_souhaitees": 0.0,
      "langues": 20.0, "coherence_documents": 0.0}, "defavorable"),
])
def test_avis_selon_le_score(scores, attendu):
    a1, a2, a3, _, _ = entrees()
    m = matching_avec_scores(**scores)
    assert proto.determiner_avis(m, a3.incoherences) == attendu


def test_avis_aux_bornes_75_et_50():
    from agents.common.schemas import Incoherence
    _, _, _, a4, _ = entrees()

    def avec_global(valeur):
        d = a4.model_dump()
        facteur = valeur / a4.score_global
        for det in d["details"]:
            det["score"] = min(100.0, det["score"] * facteur)
        d["score_global"] = valeur
        return ResultatMatching.model_construct(**{**d, "details": [proto.DetailCritere(**x) for x in d["details"]]})
    assert proto.determiner_avis(avec_global(75.0), []) == "favorable"
    assert proto.determiner_avis(avec_global(74.9), []) == "a_etudier"
    assert proto.determiner_avis(avec_global(50.0), []) == "a_etudier"
    assert proto.determiner_avis(avec_global(49.9), []) == "defavorable"
    grave = [Incoherence(type="diplome", description="x", gravite="elevee")]
    assert proto.determiner_avis(avec_global(90.0), grave) == "a_etudier"             # incohérence élevée : jamais favorable
    assert proto.determiner_avis(avec_global(90.0), [Incoherence(type="date", description="x", gravite="faible")]) == "favorable"
    assert proto.determiner_avis(avec_global(40.0), grave) == "defavorable"           # le score bas l'emporte
    sans_obligatoire = avec_global(90.0)
    sans_obligatoire.details[0].score = 0.0                                          # critère obligatoire à 0, score global élevé
    assert proto.determiner_avis(sans_obligatoire, []) == "a_etudier"


def test_l_avis_du_rapport_suit_la_regle_sur_les_deux_chaines():
    for cas, avis in (("conforme", "favorable"), ("incoherent", "a_etudier")):
        a1, a2, a3, a4, attendu = entrees(cas)
        assert generer_rapport(a1, a2, a3, a4, llm=faux_llm(score=str(a4.score_global))).avis_indicatif == avis == attendu.avis_indicatif


# ================================================================ repli
@pytest.mark.parametrize("cas", ["conforme", "incoherent"])
def test_le_repli_respecte_lui_meme_les_garde_fous(cas):
    a1, a2, a3, a4, _ = entrees(cas)
    prep = proto.preparer_rapport(a1, a2, a3, a4)
    redaction = rediger_repli(prep)
    proto.valider_redaction(redaction, prep)                              # le gabarit passe le même contrôle que le modèle
    assert DECISION in redaction.conclusion


def test_la_chaine_reste_utilisable_avec_les_mocks_de_reference():
    """Même histoire que agents/tests/test_mocks.py : le rapport produit est cohérent avec le rapport de référence."""
    for cas in ("conforme", "incoherent"):
        a1, a2, a3, a4, attendu = entrees(cas)
        rapport = generer_rapport(a1, a2, a3, a4, llm=llm_qui_echoue)
        assert rapport.incoherences == a3.incoherences and rapport.justification_score == a4.details
        assert rapport.score_global == attendu.score_global
