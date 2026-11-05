# Agentic AI Recruitment — GitHub repository structure

## Technology choices
- FastAPI: backend API
- PostgreSQL: relational database
- SQLAlchemy 2.x: ORM
- Alembic: database migrations
- Pydantic: input/output validation
- bcrypt: password hashing
- python-dotenv: local environment configuration

## Repository layout

```text
agentic-ai-recruitment/
├── app/
│   ├── core/
│   │   ├── config.py
│   │   └── security.py
│   ├── db/
│   │   ├── base.py
│   │   └── session.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py
│   │   └── offer.py
│   ├── schemas/
│   ├── api/
│   ├── agents/
│   ├── orchestrator/
│   └── main.py
├── scripts/
│   └── seed.py
├── alembic/
├── tests/
├── uploads/              # Local only; never commit uploaded CV/CIN/diploma files
├── .env.example
├── .gitignore
├── requirements.txt
├── docker-compose.yml
└── README.md
```

## First implementation task: seed data

The `scripts/seed.py` script creates:
1. One administrator account.
2. One candidate account.
3. One published test job offer.

The script is idempotent: running it more than once does not create duplicate users or the same test offer again. Existing records are left unchanged.

## Run locally

1. Create and activate a Python virtual environment.
2. Install dependencies: `pip install -r requirements.txt`
3. Copy `.env.example` to `.env` and set your database URL and development passwords.
4. Create the database tables using Alembic migrations (recommended) or `Base.metadata.create_all()` for a quick local prototype.
5. Run: `python -m scripts.seed`

Do not use the example passwords outside local development. Never commit `.env` or real candidate documents.
