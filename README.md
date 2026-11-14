# Agentic AI Recruitment

A recruitment platform that uses five specialized AI agents to extract CV information, verify documents, match candidates to job requirements, and generate an explainable report. Final recruitment decisions remain with a human recruiter.

## Current milestone

- [x] Initial repository structure
- [x] Development seed script (admin, candidate, published test offer)
- [ ] Authentication and role-based authorization
- [ ] Job offer CRUD
- [ ] Candidate application workflow
- [ ] Five AI agents and orchestrator

## Setup

```bash
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# macOS/Linux:
# source .venv/bin/activate

pip install -r requirements.txt
```

### Docker development environment

Docker is kept at the project root and runs PostgreSQL in its own container,
alongside Redis, the API, and the Celery worker. Copy `.env.example` to `.env`,
set `POSTGRES_PASSWORD` and `SECRET_KEY`, then run:

```powershell
docker compose up --build -d
docker compose exec api alembic upgrade head
```

The API is available at <http://localhost:8000/health>. PostgreSQL data is
stored in the `postgres_data` volume and Redis data in `redis_data`.
`docker compose down -v` removes those database volumes.

### Local development

Create a PostgreSQL database named `recruitment_db`, copy `.env.example` to
`.env`, and set the local `DATABASE_URL`, then run:

```bash
python -m scripts.seed
```

The seed script creates development data only. Replace the example passwords and never commit `.env` or real candidate documents.

## Offers API

Offers follow the lifecycle `draft → published → closed`.

```powershell
# Create a draft (creator_id must reference an existing user)
Invoke-RestMethod -Method Post http://localhost:8000/offers `
  -ContentType "application/json" `
  -Body '{"creator_id":1,"title":"Python Developer","description":"Backend role","required_skills":["Python"],"desired_skills":["Docker"],"languages":["French"],"experience_years":2}'

# Edit a draft
Invoke-RestMethod -Method Patch http://localhost:8000/offers/1 `
  -ContentType "application/json" `
  -Body '{"description":"Updated description"}'

# Publish, then close
Invoke-RestMethod -Method Post http://localhost:8000/offers/1/publish
Invoke-RestMethod -Method Post http://localhost:8000/offers/1/close
```

Available endpoints:

- `POST /offers` creates a draft.
- `GET /offers` lists offers; use `?status=draft`, `?status=published`, or `?status=closed`.
- `GET /offers/{id}` reads an offer.
- `PATCH /offers/{id}` edits a draft.
- `POST /offers/{id}/publish` publishes a draft.
- `POST /offers/{id}/close` closes a published offer.
- `DELETE /offers/{id}` deletes a draft.
