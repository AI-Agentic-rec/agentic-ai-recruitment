# Agent 4 : Matching

**Responsable : Oumaima et abderrahmane**

| | |
|---|---|
| **Entrée** | Exigences (agent 1), profil (agent 2) et vérification (agent 3) |
| **Sortie** | `ResultatMatching` (voir `agents/common/schemas.py`) |
| **Contenu de la sortie** | Score global, détail des 6 critères (pondération, score, justification), compétences correspondantes et manquantes, diplôme conforme, expérience. |
| **Modèle** | Voir `.env.example` et `agents/common/llm_local.py` |

## Règles propres à cet agent
- Le score est **calculé en code** avec les pondérations de la fiche (40, 20, 15, 10, 5, 10). Toute modification des pondérations est documentée et justifiée.
- Le modèle sert seulement à reconnaître des compétences équivalentes (« JS » = « JavaScript »), avec un garde-fou contre les compétences inventées.
- Le critère « diplôme » utilise le diplôme **vérifié** par l'agent 3.

## Fichiers à créer dans ce dossier
- `prompts_agent4.py`
- `agent4_prototype.py` et `test_agent4_prototype.py` (semaine 1)
- `agent4.py` et `test_agent4.py` (semaine 2)

## État
- [ ] Prompt et prototype validés avec le vrai modèle
- [ ] Agent complet
- [ ] Tests
- [ ] Intégré à l'orchestrateur
