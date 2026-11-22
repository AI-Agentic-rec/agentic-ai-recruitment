FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# ─────────────────────────────────────────────────────────────────────────────
# 1) Dépendances système : Tesseract OCR + pack français + libs images
# ─────────────────────────────────────────────────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    tesseract-ocr-fra \
    libgl1 \
    libglib2.0-0 \
 && rm -rf /var/lib/apt/lists/*

# ─────────────────────────────────────────────────────────────────────────────
# 2) Dépendances Python : on installe les 3 fichiers de requirements
#    (backend, agents et racine — évite les modules manquants comme pdfplumber)
# ─────────────────────────────────────────────────────────────────────────────
COPY backend/requirements.txt backend/requirements.txt
COPY agents/requirements.txt agents/requirements.txt
COPY requirements.txt requirements.txt

RUN pip install --upgrade pip && \
    pip install -r backend/requirements.txt && \
    pip install -r agents/requirements.txt && \
    pip install -r requirements.txt

# ─────────────────────────────────────────────────────────────────────────────
# 3) Code applicatif
# ─────────────────────────────────────────────────────────────────────────────
COPY . .

RUN mkdir -p /app/storage/uploads

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]