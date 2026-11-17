# Agentic AI Recruitment: structure du dépôt

## Choix techniques
- FastAPI : API du backend
- PostgreSQL 17 : base relationnelle (JSONB pour les sorties des agents)
- SQLAlchemy 2.x : ORM
- Alembic : migrations (`database/migrations/`)
- Pydantic : validation des entrées / sorties
- Celery + Redis : traitement asynchrone
- bcrypt : hachage des mots de passe
- Docker Compose : lance toute la pile

## Arborescence

```text
agentic-ai-recruitment/
├── agents/                  5 agents d'IA + contrats (agents/common/schemas.py)
├── backend/
│   ├── app/                 API FastAPI : main, api/routes, api/dependencies, core, db, models, schemas, services
│   ├── orchestrateur/       enchaînement des agents (à venir)
│   ├── tests/               tests du backend (PostgreSQL réel)
│   └── requirements.txt
├── database/
│   ├── schema/              MCD, diagramme de classes, schema.sql
│   ├── migrations/          Alembic (env.py, versions/)
│   └── seed/                seed.py : admin, candidat, offre de test
├── docker/                  backend.Dockerfile
├── docs/  data/  frontend/  scripts/  tests/
├── alembic.ini
├── docker-compose.yml
├── .env.example
├── pytest.ini
└── requirements.txt         backend + agents
```

## Règles de structure
- **Un seul endroit par chose.** Le schéma des agents est `agents/common/schemas.py` (contrat) : pas de copie ailleurs.
  Le code de chaque agent est dans `agents/agentN_*/`.
- Les tables sont créées **uniquement** par Alembic. Le service `migrate` de Docker Compose le fait au démarrage.
- `app` (le backend) et `agents` s'importent tous deux depuis la racine (`pytest.ini`, `PYTHONPATH` du Dockerfile).
- Les documents déposés vont dans `storage/uploads/` (hors Git, volume Docker `uploads_data`).

## Premier lancement
Voir le README principal (« Démarrage rapide avec Docker ») et `database/README.md`.
Ne pas utiliser les mots de passe d'exemple hors du développement local. Ne jamais envoyer `.env` ni de vrais documents sur Git.
