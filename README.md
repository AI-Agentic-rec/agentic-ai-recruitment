# Plateforme de recrutement intelligente (Agentic AI)

Matching **CV ↔ offre d'emploi** par cinq agents d'IA spécialisés. Mini-projet 2, module Intelligence Artificielle / Agentic AI.

> **Règles centrales** : aucune analyse n'est lancée automatiquement (seul l'administrateur déclenche le traitement). Le score est une **aide à la décision** : la décision finale appartient au recruteur. Toutes les données du projet sont **fictives**.

## Où mettre quoi

```
recrutement-agentic-ai/
├── agents/                          Les 5 agents d'IA
│   ├── common/                      contrats (schemas), moteur Ollama, outils partagés
│   ├── agent1_job_requirement/      analyse de l'offre
│   ├── agent2_cv_extraction/        extraction du CV
│   ├── agent3_document_verification/ vérification diplôme et CIN (OCR)
│   ├── agent4_matching/             score de correspondance
│   ├── agent5_report/               rapport final
│   └── tests/                       tests qui concernent plusieurs agents
├── backend/                         API FastAPI et orchestrateur
│   ├── app/                         routes, sécurité, modèles, services
│   ├── orchestrateur/               enchaînement des agents
│   └── tests/
├── database/                        schéma, migrations, données de départ
├── frontend/                        espaces public, candidat, administrateur
├── data/
│   ├── mocks/                       exemples de sorties des 5 agents (JSON)
│   └── jeu_de_test/                 offres et candidats fictifs
├── docs/                            architecture, contrats, UML, API, planning
├── docker/                          Dockerfiles (docker-compose.yml à la racine)
├── scripts/                         scripts utiles à l'équipe
├── tests/                           tests de bout en bout
├── .github/                         tests automatiques et modèle de pull request
└── requirements.txt                 dépendances Python
```

Chaque dossier contient un `README.md` qui explique ce qu'on y met et qui en est responsable.

## Qui travaille où

| Membre | Dossiers |
|---|---|
| **Oumaima** (cheffe de projet) | `agents/common/`, `agents/agent3_document_verification/`, `data/mocks/`, `docs/contrats/`, `docs/` assemblage du rapport |
| **Abderrahmane** | `database/`, `docker/`, `docker-compose.yml`, `agents/agent4_matching/`, upload des documents |
| **Zineb** | `agents/agent1_job_requirement/`, `frontend/src/espace_public/` |
| **Salah** | `agents/agent2_cv_extraction/`, `frontend/src/espace_candidat/` |
| **Fatima** | `backend/app/core/`, `backend/orchestrateur/`, `docs/api/`, `agents/agent5_report/` |
| **Amina** | offres, candidatures et emails du backend, `frontend/src/espace_admin/`, `agents/agent5_report/` |

Si ton travail touche le dossier de quelqu'un d'autre, passe par une pull request et demande-lui de relire.

## Conventions

- Noms de dossiers et de fichiers : minuscules, avec des underscores, **sans accents ni espaces**.
- Fichiers de test : `test_*.py`, avec un **nom unique** dans tout le dépôt.
- Un agent N a ses fichiers `prompts_agentN.py`, `agentN_prototype.py`, `agentN.py`, `test_agentN*.py`.
- Imports Python depuis la racine : `from agents.common.schemas import ...`.
- Aucun fichier de configuration personnel dans Git (`.env`, `.vscode/`).

## Prérequis

- Python 3.10 ou plus, Git
- [Ollama](https://ollama.com/download) (modèles locaux)
- [Tesseract](https://github.com/UB-Mannheim/tesseract/wiki) avec le pack de langue **français** (OCR de l'agent 3)
- Docker et Docker Compose

## Installation (Windows, PowerShell)

```powershell
git clone <URL-DU-DEPOT>
cd <NOM-DU-DEPOT>
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
copy .env.example .env
```

Modèles locaux :

```powershell
ollama pull mistral:7b      
```

## Lancer les tests

Depuis la racine du dépôt :

```powershell
python -m pytest -q
```

Aucun test n'appelle Ollama : les modèles y sont simulés.

## Règles du projet

1. **Aucune analyse IA sans action explicite de l'administrateur.**
2. **Données fictives uniquement** pour les CV, diplômes et CIN.
3. **Aucune clé, aucun mot de passe dans Git** : tout passe par `.env`.
4. **Sorties JSON validées** (Pydantic) pour chaque agent.
5. `agents/common/schemas.py` et `data/mocks/` sont les **contrats** : modification seulement après accord de la cheffe de projet.
6. Le numéro de CIN est une donnée sensible : masqué dans les logs, retiré avant les agents 4 et 5.

## Travailler avec Git

## État d'avancement

À compléter au fil des semaines.
