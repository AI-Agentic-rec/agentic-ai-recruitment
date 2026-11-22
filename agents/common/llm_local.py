import logging
import os
import re
from typing import TypeVar

from pydantic import BaseModel, ValidationError

logger = logging.getLogger("llm_local")
T = TypeVar("T", bound=BaseModel)


class AgentError(Exception):
    """Levée quand un agent n'arrive pas à produire une sortie valide."""


# ---------------- configuration (lue à chaque appel, donc modifiable par variable d'environnement) ----------------
MODELES_PAR_DEFAUT_PAR_AGENT = {
    1: "mistral:7b",
    2: "mistral:7b",
    3: "mistral:7b",
    #3: "qwen3-vl:8b-instruct-q4_K_M",
    4: "mistral:7b",
    5: "mistral:7b",
}


def modele_pour(numero_agent: int) -> str:
    """Ordre de priorité : OLLAMA_MODEL_AGENTn, puis OLLAMA_MODEL, puis le défaut de l'agent, puis le défaut général."""
    return (os.getenv(f"OLLAMA_MODEL_AGENT{numero_agent}") or os.getenv("OLLAMA_MODEL")
            or MODELES_PAR_DEFAUT_PAR_AGENT.get(numero_agent) or MODELE_PAR_DEFAUT)


def options_ollama() -> dict:
    return {"temperature": 0, "num_ctx": int(os.getenv("OLLAMA_NUM_CTX", "8192"))}


def keep_alive() -> str:
    return os.getenv("OLLAMA_KEEP_ALIVE", "30m")


def _think(modele: str):
    """Le paramètre « think » n'existe que pour certains modèles : on ne le transmet qu'aux modèles qwen (sinon Ollama refuse)."""
    if not modele.lower().startswith("qwen"):
        return None
    return {"true": True, "false": False}.get(os.getenv("OLLAMA_THINK", "").strip().lower())  # None : non transmis


# ---------------- utilitaires ----------------
def extraire_json(texte: str) -> str:
    """Retire un éventuel bloc de réflexion <think>, un bloc ```json et le texte autour de l'objet JSON."""
    texte = re.sub(r"<think>.*?</think>", "", texte, flags=re.S)
    texte = re.sub(r"```(?:json)?", "", texte).strip()
    debut, fin = texte.find("{"), texte.rfind("}")
    return texte[debut:fin + 1] if debut != -1 and fin != -1 else texte


def appeler_ollama(modele: str, system: str, messages: list[dict], schema: type[BaseModel]) -> str:
    """Appel réel d'Ollama. Remplacé par un faux LLM dans les tests."""
    import ollama
    parametres = dict(model=modele, messages=[{"role": "system", "content": system}] + messages,
                      format=schema.model_json_schema(), options=options_ollama(), keep_alive=keep_alive())
    if _think(modele) is not None:
        parametres["think"] = _think(modele)
    return ollama.chat(**parametres)["message"]["content"]


def transcrire_image(numero_agent: int, chemin_image: str, prompt: str, llm=None) -> str:
    """Image -> texte brut (OCR par le modèle de vision. OLLAMA_OCR_MODEL permet d'utiliser un autre modèle."""
    modele = os.getenv("OLLAMA_OCR_MODEL") or modele_pour(numero_agent)
    if llm:
        return llm(modele, prompt, chemin_image)
    import ollama
    parametres = dict(model=modele, messages=[{"role": "user", "content": prompt, "images": [chemin_image]}],
                      options=options_ollama(), keep_alive=keep_alive())
    if _think(modele) is not None:
        parametres["think"] = _think(modele)
    texte = ollama.chat(**parametres)["message"]["content"]
    return re.sub(r"<think>.*?</think>", "", texte, flags=re.S).strip()


# ---------------- exécution d'un agent ----------------
def executer_agent(numero_agent: int, system_prompt: str, message: str, schema: type[T],
                   llm=None, max_essais: int = 3, images: list[str] | None = None) -> T:
    """Exécute un agent : prompt -> JSON forcé -> validation Pydantic -> relance si invalide.
    images : chemins d'images ; le modèle gère la vision."""
    llm = llm or appeler_ollama
    modele = modele_pour(numero_agent)
    premier = {"role": "user", "content": message}
    if images:
        premier["images"] = images
    messages = [premier]
    derniere = None
    for essai in range(1, max_essais + 1):
        logger.info("Agent %d (%s), essai %d/%d", numero_agent, modele, essai, max_essais)
        brut = llm(modele, system_prompt, messages, schema)
        try:
            return schema.model_validate_json(extraire_json(brut))
        except ValidationError as erreur:
            derniere = erreur
            logger.warning("Agent %d : sortie invalide (essai %d) : %s", numero_agent, essai, erreur)
            messages = messages + [{"role": "assistant", "content": brut},
                                   {"role": "user", "content": f"Ta réponse n'est pas valide : {erreur}\nRenvoie uniquement le JSON corrigé."}]
    raise AgentError(f"Agent {numero_agent} : sortie invalide après {max_essais} essais : {derniere}")
