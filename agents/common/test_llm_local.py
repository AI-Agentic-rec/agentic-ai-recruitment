"""Tests du socle commun SANS Ollama.  Lancer : python -m pytest agents/common/test_llm_local.py"""
import json, logging, os
from agents.common.llm_local import AgentError, _think, executer_agent, extraire_json, modele_pour, transcrire_image
from agents.common.schemas import ExigencesStructurees

BON = json.dumps({"titre_poste": "Développeur Python", "diplome_demande": "Bac+5", "niveau_diplome_min": 5,
                  "experience_min_annees": 3, "competences_obligatoires": ["Python", "SQL"]})

logging.disable(logging.CRITICAL)      # les tests simulent des erreurs : pas d'avertissements à l'écran


def faux(*reponses):
    it, appels = iter(reponses), []
    def llm(modele, system, messages, schema):
        appels.append({"modele": modele, "messages": messages, "schema": schema}); return next(it)
    llm.appels = appels
    return llm


def test_agent_valide_et_modele_par_defaut():
    for v in ("OLLAMA_MODEL", "OLLAMA_MODEL_AGENT1"): os.environ.pop(v, None)
    llm = faux(BON)
    r = executer_agent(1, "prompt", "offre", ExigencesStructurees, llm=llm)
    assert r.titre_poste == "Développeur Python" and llm.appels[0]["modele"] == "qwen3.5:4b"
    assert llm.appels[0]["schema"] is ExigencesStructurees   # le schéma est transmis pour forcer le JSON


def test_modele_configurable_par_variable():
    os.environ["OLLAMA_MODEL"] = "qwen3.5:2b"; os.environ["OLLAMA_MODEL_AGENT5"] = "mistral"
    try:
        assert (modele_pour(1), modele_pour(5)) == ("qwen3.5:2b", "mistral")
    finally:
        os.environ.pop("OLLAMA_MODEL"); os.environ.pop("OLLAMA_MODEL_AGENT5")


def test_relance_puis_succes_et_message_d_erreur_renvoye():
    llm = faux("réponse en texte libre", BON)
    assert executer_agent(1, "p", "m", ExigencesStructurees, llm=llm).experience_min_annees == 3
    assert "pas valide" in llm.appels[1]["messages"][-1]["content"]


def test_erreur_apres_trois_essais():
    try:
        executer_agent(2, "p", "m", ExigencesStructurees, llm=faux("a", "b", "c")); assert False
    except AgentError:
        pass


def test_bloc_reflexion_et_markdown_retires():
    assert json.loads(extraire_json("<think>je réfléchis {x}</think>\n```json\n" + BON + "\n```"))["titre_poste"] == "Développeur Python"


def test_images_transmises_pour_l_agent_3():
    llm = faux(BON)
    executer_agent(3, "p", "m", ExigencesStructurees, llm=llm, images=["cin.png"])
    assert llm.appels[0]["messages"][0]["images"] == ["cin.png"]


def test_agent_3_utilise_mistral_par_defaut_et_reste_configurable():
    for v in ("OLLAMA_MODEL", "OLLAMA_MODEL_AGENT3"): os.environ.pop(v, None)
    assert (modele_pour(3), modele_pour(1)) == ("mistral:7b", "qwen3.5:4b")
    os.environ["OLLAMA_MODEL"] = "qwen3.5:2b"                      # portable : tout passe sur le petit modèle
    try:
        assert modele_pour(3) == "qwen3.5:2b"
        os.environ["OLLAMA_MODEL_AGENT3"] = "mistral:7b"
        assert modele_pour(3) == "mistral:7b"
    finally:
        os.environ.pop("OLLAMA_MODEL"); os.environ.pop("OLLAMA_MODEL_AGENT3", None)


def test_think_seulement_pour_les_modeles_qwen():
    os.environ["OLLAMA_THINK"] = "false"
    try:
        assert _think("qwen3.5:4b") is False and _think("mistral:7b") is None
    finally:
        os.environ.pop("OLLAMA_THINK")


def test_transcrire_image_utilise_le_modele_de_l_agent():
    os.environ.pop("OLLAMA_OCR_MODEL", None); os.environ.pop("OLLAMA_MODEL", None)
    assert transcrire_image(3, "cin.png", "lis", llm=lambda m, p, c: f"{m}|{c}") == "mistral:7b|cin.png"


if __name__ == "__main__":
    echecs = 0
    for nom, f in list(globals().items()):
        if nom.startswith("test_"):
            try:
                f(); print("OK ", nom)
            except Exception as erreur:          # on continue : on voit tous les tests en échec, pas seulement le premier
                echecs += 1; print(f"KO  {nom} : {type(erreur).__name__} {erreur}")
    print("\nTous les tests passent." if not echecs else f"\n{echecs} test(s) en échec.")
    raise SystemExit(1 if echecs else 0)      # code d'erreur pour la vérification automatique (GitHub Actions)
