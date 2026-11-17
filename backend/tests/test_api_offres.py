"""CRUD des offres + healthcheck, via l'API FastAPI (base de test, pas de PostgreSQL requis)."""
import pytest

try:
    from fastapi.testclient import TestClient
except (ImportError, RuntimeError):  # client HTTP de test non installé
    pytest.skip("installer backend/requirements-dev.txt", allow_module_level=True)

from app.api.offers import get_db
from app.main import app


@pytest.fixture()
def client(db):
    app.dependency_overrides[get_db] = lambda: db
    yield TestClient(app)
    app.dependency_overrides.clear()


def corps(admin, **extra):
    return {"id_admin": admin.id, "titre": "Dev", "description": "desc", "experience_annees": 2.5,
            "competences_obligatoires": ["Python"], "langues": ["Français"], **extra}


def test_health_db(client):
    assert client.get("/health/db").json() == {"status": "ok", "database": "ok"}


def test_cycle_de_vie_d_une_offre(client, admin):
    cree = client.post("/offers", json=corps(admin))
    assert cree.status_code == 201
    offre = cree.json()
    assert offre["statut"] == "BROUILLON" and offre["experience_annees"] == 2.5

    assert client.patch(f"/offers/{offre['id']}", json={"titre": "Dev senior"}).json()["titre"] == "Dev senior"
    assert client.post(f"/offers/{offre['id']}/publish").json()["statut"] == "PUBLIEE"
    assert client.patch(f"/offers/{offre['id']}", json={"titre": "x"}).status_code == 409
    assert client.get("/offers?statut=PUBLIEE").json()[0]["id"] == offre["id"]
    assert client.post(f"/offers/{offre['id']}/close").json()["statut"] == "CLOTUREE"
    assert client.delete(f"/offers/{offre['id']}").status_code == 409


def test_suppression_d_un_brouillon(client, admin):
    offre = client.post("/offers", json=corps(admin)).json()
    assert client.delete(f"/offers/{offre['id']}").status_code == 204
    assert client.get(f"/offers/{offre['id']}").status_code == 404


def test_seul_un_admin_cree_une_offre(client, db, candidature):
    assert client.post("/offers", json={**corps(candidature), "id_admin": candidature.id_candidat}).status_code == 403
