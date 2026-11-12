# Agent 5 : Report

**Responsable : Fatima (prompt, rapport) et Amina (assemblage des entrées, validation)**

| | |
|---|---|
| **Entrée** | Sorties des agents 1 à 4 (sans le numéro de CIN) |
| **Sortie** | `RapportCandidature` (voir `agents/common/schemas.py`) |
| **Contenu de la sortie** | Résumé, points forts, points manquants, incohérences, justification du score, conclusion, avis indicatif. |
| **Modèle** | Voir `.env.example` et `agents/common/llm_local.py` |

## Règles propres à cet agent
- Le **code** assemble la partie factuelle (points, incohérences, justification du score) ; le modèle rédige le résumé et la conclusion.
- Le rapport reprend exactement le score et le détail de l'agent 4.
- Le rapport rappelle que la décision finale appartient au recruteur.

## Fichiers à créer dans ce dossier
- `prompts_agent5.py`
- `agent5_prototype.py` et `test_agent5_prototype.py` (semaine 1)
- `agent5.py` et `test_agent5.py` (semaine 2)

## État
- [ ] Prompt et prototype validés avec le vrai modèle
- [ ] Agent complet
- [ ] Tests
- [ ] Intégré à l'orchestrateur
