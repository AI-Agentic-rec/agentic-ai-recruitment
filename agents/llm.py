"""Point d'entrée UNIQUE vers le modèle de langage.

Fournisseur choisi par LLM_PROVIDER dans le fichier .env :
  ollama     (défaut) — Mistral 7B en local : gratuit, sans clé, sans internet
  gemini               — API gratuite de Google AI Studio (clé gratuite, quotas)
  anthropic            — payant (pip install anthropic)

Les agents appellent seulement call_llm(system, user) : changer de fournisseur ne touche qu'à ce fichier.
"""
import os
import time
import httpx
from dotenv import load_dotenv

load_dotenv()

GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


def _post(url: str, *, headers: dict | None = None, json: dict, timeout: float, nom: str, aide: str = "") -> httpx.Response:
    """POST avec nouvelle tentative si le service est saturé (429 / 503)."""
    for pause in (5, 15, 30, None):
        try:
            r = httpx.post(url, headers=headers, json=json, timeout=timeout)
        except httpx.TransportError as e:
            raise RuntimeError(f"{nom} injoignable ({e.__class__.__name__}). {aide}") from e
        if r.status_code in (429, 503) and pause is not None:
            time.sleep(pause)
            continue
        return r
    return r


def _ollama(system: str, user: str, max_tokens: int, json_mode: bool, schema: dict | None) -> str:
    base = os.getenv("OLLAMA_URL", "http://localhost:11434")
    modele = os.getenv("OLLAMA_MODEL", "mistral")
    corps = {"model": modele, "stream": False,
             "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
             "options": {"temperature": 0, "num_predict": max_tokens,
                         "num_ctx": int(os.getenv("OLLAMA_NUM_CTX", "8192"))}}   # fenêtre assez grande pour un CV entier
    if json_mode:
        corps["format"] = schema or "json"          # « schema » force la structure exacte de la réponse
    aide = "Lancez l'application Ollama (ou « ollama serve » dans un terminal) puis réessayez."
    r = _post(f"{base}/api/chat", json=corps, timeout=600, nom="Ollama", aide=aide)
    if r.status_code == 400 and schema and json_mode:   # Ollama ancien : pas de schéma → simple mode JSON
        corps["format"] = "json"
        r = _post(f"{base}/api/chat", json=corps, timeout=600, nom="Ollama", aide=aide)
    if r.status_code != 200:
        raise RuntimeError(f"Ollama a répondu {r.status_code} : {r.text[:300]}  (avez-vous fait « ollama pull {modele} » ?)")
    try:
        return r.json()["message"]["content"]
    except (KeyError, ValueError) as e:
        raise RuntimeError(f"Réponse Ollama inattendue : {r.text[:300]}") from e


def _gemini(system: str, user: str, max_tokens: int, json_mode: bool, schema: dict | None) -> str:
    cle = os.getenv("GEMINI_API_KEY")
    if not cle:
        raise RuntimeError("GEMINI_API_KEY est absente : créez une clé gratuite sur aistudio.google.com puis ajoutez-la dans .env")
    modele = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    config = {"temperature": 0.1, "maxOutputTokens": max(max_tokens, 4096)}
    if json_mode:
        config["responseMimeType"] = "application/json"
    corps = {"system_instruction": {"parts": [{"text": system}]},
             "contents": [{"role": "user", "parts": [{"text": user}]}], "generationConfig": config}
    r = _post(GEMINI_URL.format(model=modele), headers={"x-goog-api-key": cle}, json=corps, timeout=90, nom="Gemini",
              aide="Vérifiez votre connexion internet.")
    if r.status_code != 200:
        raise RuntimeError(f"Gemini a répondu {r.status_code} : {r.text[:300]}  (modèle utilisé : {modele})")
    try:
        return r.json()["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError, ValueError) as e:
        raise RuntimeError(f"Réponse Gemini inattendue : {r.text[:300]}") from e


def _anthropic(system: str, user: str, max_tokens: int, json_mode: bool, schema: dict | None) -> str:
    if not os.getenv("ANTHROPIC_API_KEY"):
        raise RuntimeError("ANTHROPIC_API_KEY est absente : ajoutez-la dans .env")
    from anthropic import Anthropic
    r = Anthropic().messages.create(model=os.getenv("LLM_MODEL", "claude-haiku-5-5"), max_tokens=max_tokens,
                                    system=system, messages=[{"role": "user", "content": user}])
    return r.content[0].text


_FOURNISSEURS = {"ollama": _ollama, "gemini": _gemini, "anthropic": _anthropic}


def call_llm(system: str, user: str, max_tokens: int = 1000, json_mode: bool = True, schema: dict | None = None) -> str:
    """json_mode=True : réponse forcée en JSON (agents 1 à 4) ; False pour le rapport texte (agent 5).
    schema : schéma JSON (Pydantic .model_json_schema()) pour contraindre la structure — utilisé par Ollama."""
    nom = os.getenv("LLM_PROVIDER", "ollama").strip().lower()
    if nom not in _FOURNISSEURS:
        raise RuntimeError(f"LLM_PROVIDER « {nom} » inconnu : choisissez ollama, gemini ou anthropic")
    return _FOURNISSEURS[nom](system, user, max_tokens, json_mode, schema)
