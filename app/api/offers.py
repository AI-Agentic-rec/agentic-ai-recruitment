from collections.abc import Generator

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.sql import func
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models import Offer, OfferStatus, User
from app.schemas.offer import OfferCreate, OfferRead, OfferUpdate

router = APIRouter(prefix="/offers", tags=["offers"])


def get_db() -> Generator[Session, None, None]:
    with SessionLocal() as db:
        yield db


def get_offer_or_404(offer_id: int, db: Session) -> Offer:
    offer = db.get(Offer, offer_id)
    if offer is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Offer not found")
    return offer


@router.post("", response_model=OfferRead, status_code=status.HTTP_201_CREATED)
def create_offer(payload: OfferCreate, db: Session = Depends(get_db)) -> Offer:
    creator = db.get(User, payload.creator_id)
    if creator is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Creator not found")

    offer = Offer(**payload.model_dump())
    db.add(offer)
    db.commit()
    db.refresh(offer)
    return offer


@router.get("", response_model=list[OfferRead])
def list_offers(
    status_filter: OfferStatus | None = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
) -> list[Offer]:
    query = select(Offer).order_by(Offer.created_at.desc())
    if status_filter is not None:
        query = query.where(Offer.status == status_filter)
    return list(db.scalars(query).all())


@router.get("/{offer_id}", response_model=OfferRead)
def read_offer(offer_id: int, db: Session = Depends(get_db)) -> Offer:
    return get_offer_or_404(offer_id, db)


@router.patch("/{offer_id}", response_model=OfferRead)
def update_offer(offer_id: int, payload: OfferUpdate, db: Session = Depends(get_db)) -> Offer:
    offer = get_offer_or_404(offer_id, db)
    if offer.status is not OfferStatus.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only draft offers can be edited",
        )

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(offer, field, value)
    db.commit()
    db.refresh(offer)
    return offer


@router.post("/{offer_id}/publish", response_model=OfferRead)
def publish_offer(offer_id: int, db: Session = Depends(get_db)) -> Offer:
    offer = get_offer_or_404(offer_id, db)
    if offer.status is not OfferStatus.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only draft offers can be published",
        )
    offer.status = OfferStatus.PUBLISHED
    offer.published_at = db.scalar(select(func.now()))
    db.commit()
    db.refresh(offer)
    return offer


@router.post("/{offer_id}/close", response_model=OfferRead)
def close_offer(offer_id: int, db: Session = Depends(get_db)) -> Offer:
    offer = get_offer_or_404(offer_id, db)
    if offer.status is not OfferStatus.PUBLISHED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only published offers can be closed",
        )
    offer.status = OfferStatus.CLOSED
    offer.closed_at = db.scalar(select(func.now()))
    db.commit()
    db.refresh(offer)
    return offer


@router.delete("/{offer_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_offer(offer_id: int, db: Session = Depends(get_db)) -> None:
    offer = get_offer_or_404(offer_id, db)
    if offer.status is not OfferStatus.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only draft offers can be deleted",
        )
    db.delete(offer)
    db.commit()
