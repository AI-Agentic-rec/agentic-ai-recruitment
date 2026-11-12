# Agent 1 : Job Requirement

**Responsable : Zineb et Salah**

| | |
|---|---|
| **Entrée** | Texte de l'offre d'emploi (titre, description, exigences) |
| **Sortie** | `ExigencesStructurees` (voir `agents/common/schemas.py`) |
| **Contenu de la sortie** | Diplôme demandé et son niveau (`niveau_diplome_min`), expérience minimale, compétences obligatoires et souhaitées, langues, missions. |
| **Modèle** | Voir `.env.example` et `agents/common/llm_local.py` |

## Règles propres à cet agent
- Mettre `null` ou une liste vide plutôt que d'inventer une exigence absente de l'offre.
- Le niveau de diplôme suit l'échelle de `common/niveaux_diplome.py`.

## Fichiers à créer dans ce dossier
- `prompts_agent1.py`
- `agent1_prototype.py` et `test_agent1_prototype.py` (semaine 1)
- `agent1.py` et `test_agent1.py` (semaine 2)

## État
- [ ] Prompt et prototype validés avec le vrai modèle
- [ ] Agent complet
- [ ] Tests
- [ ] Intégré à l'orchestrateur
