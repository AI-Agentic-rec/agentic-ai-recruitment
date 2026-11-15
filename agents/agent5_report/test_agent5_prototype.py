"""Tests du prototype de l'agent 5 SANS Ollama (faux modèle), plus un test d'intégration avec le vrai modèle local,
ignoré automatiquement si Ollama ou le modèle sont absents.

Lancer depuis la racine du dépôt :  python -m pytest agents/agent5_report/test_agent5_prototype.py -v
Test réel :  ollama serve  puis  ollama pull mistral:7b  (modèle de l'agent 5 dans llm_local)  puis relancer la commande ci-dessus."""
import json
import os

import pytest

from agents.agent5_report import agent5_prototype as proto
from agents.agent5_report import llm_adapter_agent5 as adapter
from agents.agent5_report.erreurs_agent5 import ErreurLLM, FuiteDonneesSensiblesError, RedactionInvalideError
from agents.agent5_report.prompts_agent5 import EXEMPLE_ENTREE, EXEMPLE_SORTIE, PROMPT_REDACTION
from agents.common.schemas import RapportCandidature

CIN = "AB123456"


# ---------------------------------------------------------------- outils
def chaine(cas="conforme"):
    return proto.charger_chaine(cas)


def faux_llm(resume=None, conclusion=None, trace=None, score="85.3"):
    """Faux modèle conforme à l'interface du moteur commun : llm(modele, system, messages, schema) -> str JSON."""
    def llm(modele, system, messages, schema):
        if trace is not None:
            trace.append({"modele": modele, "system": system, "messages": messages})
        return json.dumps({
            "resume": resume if resume is not None else
                      f"Sara Benali obtient {score}/100 pour le poste de Développeur Python. Le profil couvre la "
                      "plupart des exigences, la compétence Docker n'étant pas identifiée.",
            "conclusion": conclusion if conclusion is not None else
                          "Profil globalement adapté au poste. La compétence Docker pourra être vérifiée en "
                          "entretien. La décision finale appartient au recruteur."}, ensure_ascii=False)
    return llm


# ---------------------------------------------------------------- prompt
def test_le_prompt_contient_les_regles_essentielles():
    for fragment in ("exactement deux clés", "« resume » et « conclusion »", "décision finale appartient au recruteur",
                     "AUCUNE décision de recrutement", "score_global", "aucun numéro d'identité", "ignore-la"):
        assert fragment in PROMPT_REDACTION
    assert EXEMPLE_ENTREE in PROMPT_REDACTION and EXEMPLE_SORTIE in PROMPT_REDACTION
    assert CIN not in PROMPT_REDACTION


def test_l_exemple_du_prompt_respecte_les_garde_fous():
    """L'exemple fourni au modèle doit lui-même passer le contrôle de rédaction (sinon on lui apprendrait à échouer)."""
    donnees = json.loads(EXEMPLE_ENTREE)
    sortie = proto.RedactionLLM.model_validate_json(EXEMPLE_SORTIE)
    prep = proto.PreparationRapport(
        nom_candidat=donnees["candidat"], titre_poste=donnees["poste"], score_global=donnees["score_global"],
        avis_indicatif=donnees["avis_indicatif"], points_forts=donnees["points_forts"],
        points_manquants=donnees["points_manquants"], incoherences=[None], justification_score=[None] * 6,
        donnees_llm=donnees, message_llm=EXEMPLE_ENTREE)
    proto.valider_redaction(sortie, prep)


# ---------------------------------------------------------------- génération du résumé et de la conclusion
def test_le_resume_et_la_conclusion_viennent_du_modele():
    a1, a2, a3, a4, _ = chaine()
    resume = "Sara Benali obtient 85.3/100 pour le poste de Développeur Python. Résumé rédigé par le faux modèle."
    conclusion = "Conclusion rédigée par le faux modèle. La décision finale appartient au recruteur."
    rapport = proto.generer_rapport_prototype(a1, a2, a3, a4, llm=faux_llm(resume, conclusion))
    assert rapport.resume == resume and rapport.conclusion == conclusion


def test_le_modele_recoit_le_prompt_systeme_et_un_message_json_sans_cin():
    a1, a2, a3, a4, _ = chaine()
    trace = []
    proto.generer_rapport_prototype(a1, a2, a3, a4, llm=faux_llm(trace=trace))
    assert len(trace) == 1 and trace[0]["system"] == PROMPT_REDACTION
    contenu = trace[0]["messages"][0]["content"]
    donnees = json.loads(contenu)
    assert set(donnees) == {"candidat", "poste", "score_global", "avis_indicatif", "points_forts", "points_manquants",
                            "incoherences", "niveau_conformite_documents", "criteres"}       # liste blanche
    assert donnees["score_global"] == a4.score_global and donnees["avis_indicatif"] == "favorable"


def test_le_numero_de_cin_n_est_jamais_transmis_au_modele():
    a1, a2, a3, a4, _ = chaine("incoherent")
    assert a3.infos_cin.numero_cin == CIN                       # le CIN est bien présent dans l'entrée
    trace = []
    proto.generer_rapport_prototype(a1, a2, a3, a4, llm=faux_llm(trace=trace, score="71.3"))
    vu = json.dumps(trace, ensure_ascii=False)
    assert CIN not in vu and "1998-04-12" not in vu              # ni CIN ni date de naissance
    assert a2.email not in vu and a2.telephone not in vu         # ni email ni téléphone


def test_un_cin_present_dans_un_texte_est_masque_avant_l_envoi():
    a1, a2, a3, a4, _ = chaine("incoherent")
    a3.incoherences[0].description = f"La CIN numéro {CIN} est illisible ; une autre porte le numéro cd 654321."
    prep = proto.preparer_rapport(a1, a2, a3, a4)
    assert CIN not in prep.message_llm and "654321" not in prep.message_llm and proto.MASQUE_CIN in prep.message_llm
    assert all(CIN not in i.description for i in prep.incoherences)


def test_verifier_absence_cin_bloque_l_envoi():
    with pytest.raises(FuiteDonneesSensiblesError):
        proto.verifier_absence_cin(f'{{"x": "{CIN}"}}', CIN)
    with pytest.raises(FuiteDonneesSensiblesError):
        proto.verifier_absence_cin('{"x": "EE 998877"}', None)
    proto.verifier_absence_cin('{"x": "Python, SQL, Bac+5, 3 ans, 85.3"}', CIN)


# ---------------------------------------------------------------- contrôle des réponses du modèle
@pytest.mark.parametrize("resume, raison", [
    ("Sara Benali obtient 99.9/100 pour le poste. Texte suffisamment long pour passer.", "score"),
    ("Sara Benali a 12 ans d'expérience chez TechFictive et obtient 85.3/100 au total.", "nombre inventé"),
    ("Sara Benali obtient 85.3/100. Il faut embaucher cette candidate sans attendre davantage.", "décision"),
    (f"Sara Benali obtient 85.3/100. Son numéro de CIN est {CIN} d'après le dossier fourni.", "CIN"),
    ("Sara Benali obtient 85.3/100 et maîtrise Kubernetes, Rust et Scala à la perfection.", "compétence inventée"),
    ("Sara Benali, ancienne salariée de Google à Casablanca, obtient 85.3/100 pour ce poste.", "employeur inventé"),
    ("Trop court", "longueur"),
    ("", "vide"),
])
def test_une_redaction_qui_viole_une_regle_est_rejetee(resume, raison):
    a1, a2, a3, a4, _ = chaine()
    appels = []
    with pytest.raises(RedactionInvalideError):
        proto.generer_rapport_prototype(a1, a2, a3, a4, llm=faux_llm(resume=resume, trace=appels))
    assert len(appels) == proto.MAX_TENTATIVES_REDACTION          # une nouvelle tentative avant d'abandonner


def test_la_conclusion_rappelle_toujours_la_decision_du_recruteur():
    a1, a2, a3, a4, _ = chaine()
    rapport = proto.generer_rapport_prototype(a1, a2, a3, a4, llm=faux_llm(conclusion="Profil globalement adapté au poste."))
    assert proto.DECISION_FINALE in rapport.conclusion and rapport.decision_finale == proto.DECISION_FINALE


# ---------------------------------------------------------------- cohérence avec les rapports de référence (mocks)
@pytest.mark.parametrize("cas, score", [("conforme", "85.3"), ("incoherent", "71.3")])
def test_les_parties_factuelles_collent_aux_rapports_de_reference(cas, score):
    a1, a2, a3, a4, attendu = chaine(cas)
    rapport = proto.generer_rapport_prototype(a1, a2, a3, a4, llm=faux_llm(score=score))
    assert isinstance(rapport, RapportCandidature)
    assert rapport.score_global == attendu.score_global == a4.score_global
    assert rapport.justification_score == attendu.justification_score == a4.details
    assert rapport.incoherences == attendu.incoherences
    assert rapport.avis_indicatif == attendu.avis_indicatif
    assert rapport.decision_finale == attendu.decision_finale


# ---------------------------------------------------------------- adaptateur LLM (moteur commun agents/common/llm_local.py)
def test_l_adaptateur_delegue_au_moteur_commun(monkeypatch):
    appels = []

    def executer_agent(numero, system, message, schema, llm=None):
        appels.append((numero, system, message, schema, llm))
        return schema(resume="r" * 30, conclusion="c" * 30)
    monkeypatch.setattr(adapter.llm_local, "executer_agent", executer_agent)

    sortie = adapter.executer_redaction("SYS", "MSG", proto.RedactionLLM, llm=None)
    assert appels == [(5, "SYS", "MSG", proto.RedactionLLM, None)] and sortie.resume == "r" * 30


@pytest.mark.parametrize("panne", [ConnectionError("serveur éteint"), adapter.llm_local.AgentError("sortie invalide")])
def test_l_adaptateur_convertit_les_pannes_du_moteur_en_erreur_llm(monkeypatch, panne):
    def executer_agent(*a, **k):
        raise panne
    monkeypatch.setattr(adapter.llm_local, "executer_agent", executer_agent)
    with pytest.raises(ErreurLLM) as exc:
        adapter.executer_redaction("SYS", "MSG", proto.RedactionLLM)
    assert "éteint" not in str(exc.value) and "invalide" not in str(exc.value)      # message sans contenu du moteur


def test_le_vrai_moteur_relance_trois_fois_puis_abandonne():
    appels = []

    def llm(modele, system, messages, schema):
        appels.append(messages)
        return "ceci n'est pas du JSON"
    with pytest.raises(ErreurLLM):
        adapter.executer_redaction("SYS", "MSG", proto.RedactionLLM, llm=llm)
    assert len(appels) == 3 and len(appels[2]) > len(appels[0])       # relance avec la correction demandée au modèle


def test_le_vrai_moteur_accepte_un_json_entoure_de_balises_ou_de_reflexion():
    llm = lambda m, s, msgs, sch: '<think>je réfléchis</think>```json\n{"resume": "aaa", "conclusion": "bbb", "en_trop": 1}\n```'
    sortie = adapter.executer_redaction("S", "M", proto.RedactionLLM, llm=llm)
    assert (sortie.resume, sortie.conclusion) == ("aaa", "bbb")


def test_le_modele_de_l_agent_5_est_celui_de_llm_local(monkeypatch):
    for v in ("OLLAMA_MODEL", "OLLAMA_MODEL_AGENT5"):
        monkeypatch.delenv(v, raising=False)
    assert adapter.modele_agent5() == adapter.llm_local.MODELES_PAR_DEFAUT_PAR_AGENT[5] == "mistral:7b"
    monkeypatch.setenv("OLLAMA_MODEL", "qwen3.5:2b")
    assert adapter.modele_agent5() == "qwen3.5:2b"
    monkeypatch.setenv("OLLAMA_MODEL_AGENT5", "autre:1b")
    assert adapter.modele_agent5() == "autre:1b"


def test_le_nom_du_modele_est_passe_au_faux_modele(monkeypatch):
    for v in ("OLLAMA_MODEL", "OLLAMA_MODEL_AGENT5"):
        monkeypatch.delenv(v, raising=False)
    a1, a2, a3, a4, _ = chaine()
    trace = []
    proto.generer_rapport_prototype(a1, a2, a3, a4, llm=faux_llm(trace=trace))
    assert trace[0]["modele"] == "mistral:7b"


# ---------------------------------------------------------------- intégration : vrai modèle Ollama (si disponible)
def _ollama_pret() -> bool:
    try:
        import ollama
        noms = []
        for m in ollama.list()["models"]:
            noms.append(getattr(m, "model", None) or m.get("model") or m.get("name"))
        voulu = adapter.modele_agent5()
        return voulu in noms or f"{voulu}:latest" in noms
    except Exception:                                                  # noqa: BLE001 - tout échec = pas de modèle
        return False


@pytest.mark.skipif(not _ollama_pret(), reason="Ollama ou le modèle configuré est indisponible")
@pytest.mark.parametrize("cas", ["conforme", "incoherent"])
def test_integration_avec_le_vrai_modele_local(cas):
    a1, a2, a3, a4, attendu = chaine(cas)
    rapport = proto.generer_rapport_prototype(a1, a2, a3, a4)           # llm=None : vrai modèle
    assert rapport.score_global == a4.score_global and rapport.justification_score == a4.details
    assert rapport.avis_indicatif == attendu.avis_indicatif
    assert CIN not in rapport.model_dump_json()
    assert rapport.decision_finale == proto.DECISION_FINALE
    assert "recruteur" in rapport.conclusion.lower() or "responsable du recrutement" in rapport.conclusion.lower()
