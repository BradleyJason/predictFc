"""SQLAlchemy model for competitions table."""
from datetime import datetime
from sqlalchemy import DateTime, Integer, String, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

class Competition(Base):
    """Représente une compétition (PL, FL1, CL...)."""
    __tablename__ = "competitions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    api_football_id: Mapped[int | None] = mapped_column(Integer, unique=True, index=True)
    code: Mapped[str] = mapped_column(String(10), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    country: Mapped[str | None] = mapped_column(String(50))
    type: Mapped[str | None] = mapped_column(String(20))  # LEAGUE, CUP, SUPERCOUPE, INTERNATIONAL
    logo_url: Mapped[str | None] = mapped_column(String(500))
    crest_url: Mapped[str | None] = mapped_column(String(500))  # football-data (legacy)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relations
    teams: Mapped[list["Team"]] = relationship("Team", back_populates="competition")  # noqa: F821
    matches: Mapped[list["Match"]] = relationship("Match", back_populates="competition")  # noqa: F821
    seasons: Mapped[list["Season"]] = relationship("Season", back_populates="competition")  # noqa: F821

    def __repr__(self) -> str:
        return f"<Competition {self.code} api_id={self.api_football_id}>"