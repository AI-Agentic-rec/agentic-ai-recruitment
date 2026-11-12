# Agent 3 : Document Verification

**Responsable : Oumaima et abderrahmane**

| | |
|---|---|
| **Entrée** | Profil du CV (agent 2), diplôme et CIN (texte ou image) |
| **Sortie** | `VerificationDocuments` (voir `agents/common/schemas.py`) |
| **Contenu de la sortie** | Informations du diplôme et de la CIN, liste des incohérences, niveau de conformité, score de cohérence. |
| **Modèle** | Voir `.env.example` et `agents/common/llm_local.py` |

## Règles propres à cet agent
- L'OCR Tesseract lit les images ; le modèle (`mistral:7b`) extrait les champs ; le **code** compare avec le CV et calcule le score.
- Le numéro de CIN est une donnée sensible : masqué dans les logs, retiré avant les agents 4 et 5 (`sans_donnees_sensibles`).
- Fichiers en plus : `ocr_tesseract.py`, `cas_test_agent3.py`, `test_ocr_tesseract.py`.

## Fichiers à créer dans ce dossier
- `prompts_agent3.py`
- `agent3_prototype.py` et `test_agent3_prototype.py` (semaine 1)
- `agent3.py` et `test_agent3.py` (semaine 2)

## État
- [ ] Prompt et prototype validés avec le vrai modèle
- [ ] Agent complet
- [ ] Tests
- [ ] Intégré à l'orchestrateur
