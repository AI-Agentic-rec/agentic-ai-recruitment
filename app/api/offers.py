from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import Offre, RoleUtilisateur, StatutOffre, Utilisateur
from app.schemas.offer import (
    OffreCreate,
    OffreUpdate,
    OffreRead,
    OffreListeResponse,
    OffreDetailResponse,
)

router = APIRouter(prefix="/offers", tags=["offers"])


def get_offre_or_404(offre_id: int, db: Session) -> Offre:
    offre = db.get(Offre, offre_id)
    if offre is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Offre introuvable")
    return offre


def exiger_statut(offre: Offre, attendu: StatutOffre, action: str) -> None:
    if offre.statut != attendu:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Seule une offre au statut {attendu.value} peut être {action}",
        )


def _serialize(offre: Offre) -> OffreRead:
    return OffreRead(
        id=offre.id,
        titre=offre.titre,
        description=offre.description,
        diplome_demande=offre.diplome_demande,
        experience_annees=offre.experience_annees,
        competences_obligatoires=offre.competences_obligatoires or [],
        competences_souhaitees=offre.competences_souhaitees or [],
        langues=offre.langues or [],
        localisation=offre.localisation,
        id_admin=offre.id_admin,
        statut=offre.statut,
        date_creation=offre.date_creation.isoformat() if offre.date_creation else "",
        date_publication=offre.date_publication.isoformat() if offre.date_publication else None,
        date_cloture=offre.date_cloture.isoformat() if offre.date_cloture else None,
    )


@router.post("", response_model=OffreRead, status_code=status.HTTP_201_CREATED)
def creer_offre(payload: OffreCreate, db: Session = Depends(get_db)) -> OffreRead:
    admin = db.get(Utilisateur, payload.id_admin)
    if admin is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Administrateur introuvable")
    if admin.role != RoleUtilisateur.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Seul un administrateur crée une offre")

    data = payload.model_dump()
    action = data.pop("action", "brouillon")

    offre = Offre(**data, statut=StatutOffre.BROUILLON)
    db.add(offre)
    db.commit()
    db.refresh(offre)

    if action == "publier":
        offre.statut = StatutOffre.PUBLIEE
        offre.date_publication = db.scalar(select(func.now()))
        db.commit()
        db.refresh(offre)

    return _serialize(offre)


@router.get("", response_model=OffreListeResponse)
def lister_offres(
    statut: StatutOffre | None = Query(default=None),
    db: Session = Depends(get_db),
) -> OffreListeResponse:
    requete = select(Offre).order_by(Offre.date_creation.desc())
    if statut is not None:
        requete = requete.where(Offre.statut == statut)
    toutes = list(db.scalars(requete).all())
    counts = {
        "brouillon": sum(1 for o in toutes if o.statut.value == "BROUILLON"),
        "publiee": sum(1 for o in toutes if o.statut.value == "PUBLIEE"),
        "cloturee": sum(1 for o in toutes if o.statut.value == "CLOTUREE"),
    }
    return OffreListeResponse(offres=[_serialize(o) for o in toutes], counts=counts)


@router.get("/{offre_id}", response_model=OffreDetailResponse)
def lire_offre(offre_id: int, db: Session = Depends(get_db)) -> OffreDetailResponse:
    return OffreDetailResponse(offre=_serialize(get_offre_or_404(offre_id, db)))


@router.patch("/{offre_id}", response_model=OffreDetailResponse)
def modifier_offre(offre_id: int, payload: OffreUpdate, db: Session = Depends(get_db)) -> OffreDetailResponse:
    offre = get_offre_or_404(offre_id, db)
    exiger_statut(offre, StatutOffre.BROUILLON, "modifiée")

    data = payload.model_dump(exclude_unset=True)
    data.pop("action", None)
    for champ, valeur in data.items():
        setattr(offre, champ, valeur)

    db.commit()
    db.refresh(offre)
    return OffreDetailResponse(offre=_serialize(offre))


@router.post("/{offre_id}/publier", response_model=OffreDetailResponse)
@router.post("/{offre_id}/publish", response_model=OffreDetailResponse, include_in_schema=False)
def publier_offre(offre_id: int, db: Session = Depends(get_db)) -> OffreDetailResponse:
    offre = get_offre_or_404(offre_id, db)
    exiger_statut(offre, StatutOffre.BROUILLON, "publiée")
    offre.statut = StatutOffre.PUBLIEE
    offre.date_publication = db.scalar(select(func.now()))
    db.commit()
    db.refresh(offre)
    return OffreDetailResponse(offre=_serialize(offre))


@router.post("/{offre_id}/cloturer", response_model=OffreDetailResponse)
@router.post("/{offre_id}/close", response_model=OffreDetailResponse, include_in_schema=False)
def cloturer_offre(offre_id: int, db: Session = Depends(get_db)) -> OffreDetailResponse:
    offre = get_offre_or_404(offre_id, db)
    exiger_statut(offre, StatutOffre.PUBLIEE, "clôturée")
    offre.statut = StatutOffre.CLOTUREE
    offre.date_cloture = db.scalar(select(func.now()))
    db.commit()
    db.refresh(offre)
    return OffreDetailResponse(offre=_serialize(offre))


@router.delete("/{offre_id}", status_code=status.HTTP_204_NO_CONTENT)
def supprimer_offre(offre_id: int, db: Session = Depends(get_db)) -> None:
    offre = get_offre_or_404(offre_id, db)
    # ✅ SUPPRESSION DE LA RESTRICTION DE STATUT
    db.delete(offre)
    db.commit()