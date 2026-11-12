# Agent 2 : CV Extraction

**Responsable : Zineb et Salah**

| | |
|---|---|
| **Entrée** | Texte du CV (extrait du PDF ou DOCX par pdfplumber ou python-docx) |
| **Sortie** | `ProfilCandidat` (voir `agents/common/schemas.py`) |
| **Contenu de la sortie** | Identité, formations, expériences, compétences, langues, certifications, expérience totale. |
| **Modèle** | Voir `.env.example` et `agents/common/llm_local.py` |

## Règles propres à cet agent
- Aucun champ de genre, d'âge ou de photo dans le profil (limite les biais).
- L'expérience totale peut être recalculée en code à partir des durées.

## Fichiers à créer dans ce dossier
- `prompts_agent2.py`
- `agent2_prototype.py` et `test_agent2_prototype.py` (semaine 1)
- `agent2.py` et `test_agent2.py` (semaine 2)

## État
- [ ] Prompt et prototype validés avec le vrai modèle
- [ ] Agent complet
- [ ] Tests
- [ ] Intégré à l'orchestrateur
