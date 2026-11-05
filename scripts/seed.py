"""Insert development seed data: admin, candidate, and one test job offer.

Run from the repository root:
    python -m scripts.seed

This script is idempotent. It does not overwrite existing users or offers.
"""
import os
import warnings

from dotenv import load_dotenv

from app.core.security import hash_password
from app.db.base import Base
from app.db.session import SessionLocal, engine
from app.models import JobOffer, User  # noqa: F401 - registers models with Base

load_dotenv()


def get_required_dev_password(variable_name: str) -> str:
    value = os.getenv(variable_name)
    if value:
        return value

    # Convenient local-only defaults. Override these in .env.
    warnings.warn(
        f"{variable_name} is not set; using a development-only password. "
        "Set it in .env and never use this default in production.",
        stacklevel=2,
    )
    return "ChangeMe-Local-Only-123!"


def seed() -> None:
    # Convenient for a first local run. In a team/production workflow,
    # create tables with Alembic migrations instead.
    Base.metadata.create_all(bind=engine)

    admin_email = os.getenv("SEED_ADMIN_EMAIL", "admin@example.com").strip().lower()
    candidate_email = os.getenv("SEED_CANDIDATE_EMAIL", "candidate@example.com").strip().lower()

    admin_password = get_required_dev_password("SEED_ADMIN_PASSWORD")
    candidate_password = get_required_dev_password("SEED_CANDIDATE_PASSWORD")

    with SessionLocal() as db:
        try:
            admin = db.query(User).filter(User.email == admin_email).first()
            if admin is None:
                db.add(
                    User(
                        first_name="Admin",
                        last_name="Recruitment",
                        email=admin_email,
                        password_hash=hash_password(admin_password),
                        role="admin",
                    )
                )
                print(f"Created administrator: {admin_email}")
            else:
                print(f"Administrator already exists: {admin_email}")

            candidate = db.query(User).filter(User.email == candidate_email).first()
            if candidate is None:
                db.add(
                    User(
                        first_name="Test",
                        last_name="Candidate",
                        email=candidate_email,
                        password_hash=hash_password(candidate_password),
                        role="candidate",
                        phone="+212600000000",
                    )
                )
                print(f"Created candidate: {candidate_email}")
            else:
                print(f"Candidate already exists: {candidate_email}")

            offer_title = "Développeur Python – Offre de test"
            offer = db.query(JobOffer).filter(JobOffer.title == offer_title).first()
            if offer is None:
                db.add(
                    JobOffer(
                        title=offer_title,
                        description=(
                            "Nous recherchons un développeur Python pour concevoir, "
                            "développer et maintenir des applications backend."
                        ),
                        diploma_required="Licence en informatique",
                        experience_years=2,
                        mandatory_skills=["Python", "SQL"],
                        desired_skills=["Docker", "Git", "FastAPI"],
                        languages=["Français", "Anglais"],
                        location="Agadir, Maroc",
                        status="published",
                    )
                )
                print(f"Created published test offer: {offer_title}")
            else:
                print(f"Test offer already exists: {offer_title}")

            db.commit()
            print("Seed completed successfully.")
        except Exception:
            db.rollback()
            raise


if __name__ == "__main__":
    seed()
