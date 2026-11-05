from datetime import datetime

from sqlalchemy import DateTime, Integer, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class JobOffer(Base):
    __tablename__ = "job_offers"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    diploma_required: Mapped[str] = mapped_column(String(200), nullable=False)
    experience_years: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    mandatory_skills: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    desired_skills: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    languages: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    location: Mapped[str] = mapped_column(String(150), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
