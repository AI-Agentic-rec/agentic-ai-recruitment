from sqlalchemy import Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.enums import RoleUtilisateur


class Utilisateur(Base):
    """Classe `Utilisateur` du diagramme."""

    __tablename__ = "utilisateur"

    id: Mapped[int] = mapped_column(primary_key=True)
    nom: Mapped[str] = mapped_column(String(100), nullable=False)
    prenom: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    mot_de_passe_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[RoleUtilisateur] = mapped_column(
        Enum(RoleUtilisateur, name="role_utilisateur"), default=RoleUtilisateur.CANDIDAT, nullable=False
    )
    telephone: Mapped[str | None] = mapped_column(String(30))

    offres_creees: Mapped[list["Offre"]] = relationship(back_populates="admin")
    candidatures: Mapped[list["Candidature"]] = relationship(back_populates="candidat")
