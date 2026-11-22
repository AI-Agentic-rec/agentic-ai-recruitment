from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings


DATABASE_URL = get_settings().database_url

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    """Dépendance FastAPI : fournit une session SQLAlchemy et la ferme en sortie."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()