from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

# ✅ AJOUT de candidatures
from app.api import offers, auth, candidatures
from app.db.session import get_db


app = FastAPI(title="Agentic AI Recruitment API", version="0.1.0")

# --- CORS : autorise le frontend Vite (dev) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes métier sous /api
app.include_router(offers.router, prefix="/api")
app.include_router(auth.router,   prefix="/api")

# ✅ AJOUT du routeur des candidatures
app.include_router(candidatures.router, prefix="/api")


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health/db", tags=["system"])
def health_db(db: Session = Depends(get_db)) -> dict[str, str]:
    """Utilisé par le healthcheck Docker : 503 si PostgreSQL ne répond pas."""
    try:
        db.execute(text("SELECT 1"))
    except Exception as erreur:  # noqa: BLE001
        raise HTTPException(status_code=503, detail="Base de données indisponible") from erreur
    return {"status": "ok", "database": "ok"}