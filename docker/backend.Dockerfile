# Image unique du backend : sert l'API, le worker Celery, `migrate` (Alembic) et `seed`.
# Construire à la racine du dépôt :  docker build -f docker/backend.Dockerfile -t recruitment-backend .
# (docker compose le fait tout seul : docker compose up --build)
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Dépendances du backend : FastAPI, SQLAlchemy 2, Alembic, psycopg (binaire : pas besoin de libpq ni de gcc),
# bcrypt, Celery. Les agents d'IA (Ollama, OCR) ont leurs propres dépendances : agents/requirements.txt.
ARG REQUIREMENTS=backend/requirements.txt
COPY backend/requirements.txt backend/requirements.txt
COPY agents/requirements.txt agents/requirements.txt
COPY requirements.txt requirements.txt
RUN pip install -r ${REQUIREMENTS}

# Code : app/ (API + modèles), agents/ (contrat agents/common/schemas.py utilisé pour l'enregistrement),
# database/ (migrations Alembic + seed), alembic.ini. En développement, docker-compose.yml monte le dépôt
# par-dessus /app : les changements de code sont pris en compte sans reconstruire.
COPY . .

RUN mkdir -p /app/storage/uploads

EXPOSE 8000

# Commande par défaut (surchargée par docker-compose.yml pour api, worker, migrate et seed).
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
