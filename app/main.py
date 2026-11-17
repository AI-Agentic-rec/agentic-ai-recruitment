from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.offers import get_db
from app.api.offers import router as offers_router

app = FastAPI(title="Agentic AI Recruitment API", version="0.1.0")
app.include_router(offers_router)


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health/db", tags=["system"])
def health_db(db: Session = Depends(get_db)) -> dict[str, str]:
    """Utilisé par le healthcheck Docker de l'API : 503 si PostgreSQL ne répond pas."""
    try:
        db.execute(text("SELECT 1"))
    except Exception as erreur:  # noqa: BLE001
        raise HTTPException(status_code=503, detail="Base de données indisponible") from erreur
    return {"status": "ok", "database": "ok"}
