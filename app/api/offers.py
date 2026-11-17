from collections.abc import Generator

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.sql import func

from app.db.session import SessionLocal
from app.models import Offre, RoleUtilisateur, StatutOffre, Utilisateur
from app.schemas.offer import OffreCreate, OffreRead, OffreUpdate

router = APIRouter(prefix="/offers", tags=["offers"])


def get_db() -> Generator[Session, None, None]:
    with SessionLocal() as db:
        yield db


def get_offre_or_404(offre_id: int, db: Session) -> Offre:
    offre = db.get(Offre, offre_id)
    if offre is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Offre introuvable")
    return offre


def exiger_statut(offre: Offre, attendu: StatutOffre, action: str) -> None:
    if offre.statut is not attendu:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Seule une offre au statut {attendu.value} peut être {action}",
        )


@router.post("", response_model=OffreRead, status_code=status.HTTP_201_CREATED)
def creer_offre(payload: OffreCreate, db: Session = Depends(get_db)) -> Offre:
    admin = db.get(Utilisateur, payload.id_admin)
    if admin is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Administrateur introuvable")
    if admin.role is not RoleUtilisateur.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Seul un administrateur crée une offre")

    offre = Offre(**payload.model_dump())
    db.add(offre)
    db.commit()
    db.refresh(offre)
    return offre


@router.get("", response_model=list[OffreRead])
def lister_offres(
    statut: StatutOffre | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[Offre]:
    requete = select(Offre).order_by(Offre.date_creation.desc())
    if statut is not None:
        requete = requete.where(Offre.statut == statut)
    return list(db.scalars(requete).all())


@router.get("/{offre_id}", response_model=OffreRead)
def lire_offre(offre_id: int, db: Session = Depends(get_db)) -> Offre:
    return get_offre_or_404(offre_id, db)


@router.patch("/{offre_id}", response_model=OffreRead)
def modifier_offre(offre_id: int, payload: OffreUpdate, db: Session = Depends(get_db)) -> Offre:
    offre = get_offre_or_404(offre_id, db)
    exiger_statut(offre, StatutOffre.BROUILLON, "modifiée")
    for champ, valeur in payload.model_dump(exclude_unset=True).items():
        setattr(offre, champ, valeur)
    db.commit()
    db.refresh(offre)
    return offre


@router.post("/{offre_id}/publish", response_model=OffreRead)
def publier_offre(offre_id: int, db: Session = Depends(get_db)) -> Offre:
    offre = get_offre_or_404(offre_id, db)
    exiger_statut(offre, StatutOffre.BROUILLON, "publiée")
    offre.statut = StatutOffre.PUBLIEE
    offre.date_publication = db.scalar(select(func.now()))
    db.commit()
    db.refresh(offre)
    return offre


@router.post("/{offre_id}/close", response_model=OffreRead)
def cloturer_offre(offre_id: int, db: Session = Depends(get_db)) -> Offre:
    offre = get_offre_or_404(offre_id, db)
    exiger_statut(offre, StatutOffre.PUBLIEE, "clôturée")
    offre.statut = StatutOffre.CLOTUREE
    offre.date_cloture = db.scalar(select(func.now()))
    db.commit()
    db.refresh(offre)
    return offre


@router.delete("/{offre_id}", status_code=status.HTTP_204_NO_CONTENT)
def supprimer_offre(offre_id: int, db: Session = Depends(get_db)) -> None:
    offre = get_offre_or_404(offre_id, db)
    exiger_statut(offre, StatutOffre.BROUILLON, "supprimée")
    db.delete(offre)
    db.commit()
