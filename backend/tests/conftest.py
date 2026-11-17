"""Fixtures communes. Par défaut : SQLite en mémoire (aucun PostgreSQL requis, JSONB traduit en JSON).

Pour tester sur un vrai PostgreSQL :
    TEST_DATABASE_URL=postgresql+psycopg://user:pass@localhost:5432/test_db python -m pytest backend/tests
(la base indiquée est vidée puis recréée : utiliser une base de test dédiée).
"""
import os

import pytest
from sqlalchemy import create_engine
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.models import Candidature, Offre, RoleUtilisateur, StatutOffre, Utilisateur


@compiles(JSONB, "sqlite")
def _jsonb_sqlite(type_, compiler, **kw):
    return "JSON"


@pytest.fixture()
def engine():
    url = os.getenv("TEST_DATABASE_URL")
    if url:
        eng = create_engine(url)
        Base.metadata.drop_all(eng)
    else:
        eng = create_engine("sqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False})
    Base.metadata.create_all(eng)
    yield eng
    if url:
        Base.metadata.drop_all(eng)
    eng.dispose()


@pytest.fixture()
def db(engine):
    with sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)() as session:
        yield session


@pytest.fixture()
def admin(db):
    u = Utilisateur(nom="Admin", prenom="A", email="admin@test.test", mot_de_passe_hash="x", role=RoleUtilisateur.ADMIN)
    db.add(u)
    db.commit()
    return u


@pytest.fixture()
def candidature(db, admin):
    candidat = Utilisateur(nom="Cand", prenom="C", email="cand@test.test", mot_de_passe_hash="x",
                           role=RoleUtilisateur.CANDIDAT)
    offre = Offre(id_admin=admin.id, titre="Dev Python", description="desc", experience_annees=3,
                  statut=StatutOffre.PUBLIEE)
    db.add_all([candidat, offre])
    db.flush()
    c = Candidature(id_candidat=candidat.id, id_offre=offre.id)
    db.add(c)
    db.commit()
    return c
