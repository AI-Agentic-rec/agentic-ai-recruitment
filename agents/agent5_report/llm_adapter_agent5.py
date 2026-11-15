"""Adaptateur LLM de l'Agent 5 : UN SEUL point de contact avec le moteur commun `agents/common/llm_local.py`.

L'Agent 5 n'a ni configuration LLM ni appel Ollama propres : tout passe par `llm_local.executer_agent`
(JSON forcé, validation Pydantic, 3 essais avec relance). Le modèle est celui défini pour l'agent 5 dans `llm_local`
(`modele_pour(5)` : OLLAMA_MODEL_AGENT5, puis OLLAMA_MODEL, puis « mistral:7b » par défaut).

Cet adaptateur ne fait que deux choses :
- appeler `executer_agent(5, prompt, message_json, Schema, llm=llm)` ;
- convertir toute panne du moteur (`AgentError` après 3 essais invalides, serveur Ollama arrêté, modèle absent...) en
  `ErreurLLM`, dont le message ne contient ni le prompt, ni le message envoyé, ni la réponse du modèle.

`llm`, s'il est fourni (tests), est un faux modèle : `llm(modele, system, messages, schema) -> str (JSON)`.
"""
from typing import Callable, Optional, Type

from pydantic import BaseModel

from agents.agent5_report.erreurs_agent5 import Agent5Error, ErreurLLM
from agents.common import llm_local

NUMERO_AGENT = 5

FauxModele = Callable[[str, str, list, Type[BaseModel]], str]


def modele_agent5() -> str:
    """Modèle utilisé par l'agent 5 (défini dans `llm_local`, jamais dupliqué ici)."""
    return llm_local.modele_pour(NUMERO_AGENT)


def executer_redaction(system: str, message: str, schema: Type[BaseModel], llm: Optional[FauxModele] = None):
    """Appelle le moteur commun et renvoie une instance validée de `schema` (ou lève `ErreurLLM`)."""
    try:
        return llm_local.executer_agent(NUMERO_AGENT, system, message, schema, llm=llm)
    except Agent5Error:
        raise
    except Exception as exc:                                   # noqa: BLE001 - AgentError, ConnectionError, ResponseError...
        raise ErreurLLM(f"Échec de l'appel au modèle local ({type(exc).__name__}).") from exc
