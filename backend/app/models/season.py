"""SQLAlchemy model for seasons table."""
from datetime import datetime, date
from sqlalchemy import DateTime, Date, ForeignKey, Integer, String, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

class Season(Base):
    """Représente une saison pour une compétition donnée."""
    __tablename__ = "seasons"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    competition_id: Mapped[int] = mapped_column(Integer, ForeignKey("competitions.id"), nullable=False, index=True)
    year: Mapped[int] = mapped_column(Integer, nullable=False)  # ex: 2024 pour 2024/25
    start_date: Mapped[date | None] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date)
    is_current: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Relations
    competition: Mapped["Competition"] = relationship("Competition", back_populates="seasons")  # noqa: F821
    matches: Mapped[list["Match"]] = relationship("Match", back_populates="season")  # noqa: F821

    def __repr__(self) -> str:
        return f"<Season {self.year}/{self.year+1} comp={self.competition_id}>"