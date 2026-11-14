from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.recruitment import OfferStatus


class OfferFields(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    description: str = Field(min_length=1)
    diploma_required: str | None = Field(default=None, max_length=255)
    experience_years: int | None = Field(default=None, ge=0)
    required_skills: list[str] = Field(default_factory=list)
    desired_skills: list[str] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)
    location: str | None = Field(default=None, max_length=255)


class OfferCreate(OfferFields):
    creator_id: int = Field(gt=0)


class OfferUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, min_length=1)
    diploma_required: str | None = Field(default=None, max_length=255)
    experience_years: int | None = Field(default=None, ge=0)
    required_skills: list[str] | None = None
    desired_skills: list[str] | None = None
    languages: list[str] | None = None
    location: str | None = Field(default=None, max_length=255)


class OfferRead(OfferFields):
    model_config = ConfigDict(from_attributes=True)

    id: int
    creator_id: int
    status: OfferStatus
    created_at: datetime
    published_at: datetime | None
    closed_at: datetime | None
