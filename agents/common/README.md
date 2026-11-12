# agents/common : code partagé

**Propriétaire : Oumaima.** Toute modification passe par une pull request qu'elle approuve.

| Fichier attendu | Contenu |
|---|---|
| `schemas.py` | **Contrats** : format de sortie des 5 agents (Pydantic) |
| `llm_local.py` | Moteur Ollama : JSON forcé, validation, relance, choix du modèle par variable d'environnement |
| `niveaux_diplome.py` | Échelle des niveaux de diplôme (Bac+N), utilisée par les agents 3 et 4 |

N'ajouter ici que ce qui sert à **au moins deux agents**. Le reste va dans le dossier de l'agent concerné.
