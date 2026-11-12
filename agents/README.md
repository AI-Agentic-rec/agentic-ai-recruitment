# Agents d'IA

Les 5 agents du workflow, leurs contrats et leurs tests. **Chaque agent a son dossier et son responsable.**

```
agents/
├── common/                         code partagé : contrats (schemas), moteur Ollama, outils communs
├── agent1_job_requirement/         Zineb et Salah
├── agent2_cv_extraction/           Zineb et Salah
├── agent3_document_verification/   Oumaima et Abderrahmane
├── agent4_matching/                Oumaima et Abderrahmane
├── agent5_report/                  Fatima et Amina
└── tests/                          tests qui concernent plusieurs agents (chaîne, mocks)
```

## Les fichiers d'un dossier d'agent (N = numéro de l'agent)

| Fichier | Contenu |
|---|---|
| `prompts_agentN.py` | Les prompts, et seulement eux |
| `agentN_prototype.py` | Prototype de la semaine 1 : vérifie que le prompt marche, compare la sortie à une vérité terrain |
| `agentN.py` | L'agent complet, appelé par l'orchestrateur |
| `test_agentN_prototype.py`, `test_agentN.py` | Tests sans Ollama (faux modèle) |
| `README.md` | Entrée, sortie, règles propres à l'agent (déjà écrit : le compléter) |

Les noms sont **uniques dans tout le dépôt** : c'est ce qui permet à `pytest` de lancer tous les tests ensemble.

## Règles communes

1. **Une seule responsabilité par agent**, avec son prompt dédié.
2. La sortie de chaque agent est un **schéma Pydantic** défini dans `common/schemas.py` (contrat).
3. L'appel au modèle passe **toujours** par le moteur commun de `common/` (JSON forcé, validation, 3 essais).
4. Le modèle lit et extrait ; le **code** compare et calcule quand c'est possible (reproductible, explicable).
5. Le prototype est testé **séparément** avant d'être intégré au workflow complet.

## Importer

Depuis la racine du dépôt, tout s'importe avec le chemin complet :

```python
from agents.common.schemas import ExigencesStructurees
from agents.common.llm_local import executer_agent
```
