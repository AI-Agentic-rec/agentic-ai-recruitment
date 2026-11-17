"""Données de départ (fictives) : un administrateur, un candidat et une offre publiée de test.

Lancer depuis la racine du dépôt (après `alembic upgrade head`) :
    python -m database.seed.seed          ou          docker compose run --rm seed

Idempotent : ne modifie ni ne duplique ce qui existe déjà.
"""
import os
import warnings

from dotenv import load_dotenv

from app.core.security import hash_password
from app.db.session import SessionLocal
from sqlalchemy import func

from app.models import Offre, RoleUtilisateur, StatutOffre, Utilisateur

load_dotenv()

TITRE_OFFRE_TEST = "Développeur Python – Offre de test"


def mot_de_passe_dev(variable: str) -> str:
    valeur = os.getenv(variable)
    if valeur:
        return valeur
    warnings.warn(
        f"{variable} n'est pas défini : mot de passe de développement utilisé. "
        "Le définir dans .env ; ne jamais l'utiliser en production.",
        stacklevel=2,
    )
    return "ChangeMe-Local-Only-123!"


def seed() -> None:
    email_admin = os.getenv("SEED_ADMIN_EMAIL", "admin@example.com").strip().lower()
    email_candidat = os.getenv("SEED_CANDIDATE_EMAIL", "candidate@example.com").strip().lower()

    with SessionLocal() as db:
        try:
            admin = db.query(Utilisateur).filter_by(email=email_admin).first()
            if admin is None:
                admin = Utilisateur(
                    nom="Recruitment",
                    prenom="Admin",
                    email=email_admin,
                    mot_de_passe_hash=hash_password(mot_de_passe_dev("SEED_ADMIN_PASSWORD")),
                    role=RoleUtilisateur.ADMIN,
                )
                db.add(admin)
                db.flush()  # obtient admin.id
                print(f"Administrateur créé : {email_admin}")
            else:
                print(f"Administrateur existant : {email_admin}")

            if db.query(Utilisateur).filter_by(email=email_candidat).first() is None:
                db.add(
                    Utilisateur(
                        nom="Candidat",
                        prenom="Test",
                        email=email_candidat,
                        mot_de_passe_hash=hash_password(mot_de_passe_dev("SEED_CANDIDATE_PASSWORD")),
                        role=RoleUtilisateur.CANDIDAT,
                        telephone="+212600000000",
                    )
                )
                print(f"Candidat créé : {email_candidat}")
            else:
                print(f"Candidat existant : {email_candidat}")

            if db.query(Offre).filter_by(titre=TITRE_OFFRE_TEST).first() is None:
                db.add(
                    Offre(
                        id_admin=admin.id,
                        titre=TITRE_OFFRE_TEST,
                        description=(
                            "Nous recherchons un développeur Python pour concevoir, "
                            "développer et maintenir des applications backend."
                        ),
                        diplome_demande="Licence en informatique",
                        experience_annees=2,
                        competences_obligatoires=["Python", "SQL"],
                        competences_souhaitees=["Docker", "Git", "FastAPI"],
                        langues=["Français", "Anglais"],
                        localisation="Agadir, Maroc",
                        statut=StatutOffre.PUBLIEE,
                        date_publication=func.now(),
                    )
                )
                print(f"Offre publiée créée : {TITRE_OFFRE_TEST}")
            else:
                print(f"Offre de test existante : {TITRE_OFFRE_TEST}")

            db.commit()
            print("Seed terminé.")
        except Exception:
            db.rollback()
            raise


if __name__ == "__main__":
    seed()
