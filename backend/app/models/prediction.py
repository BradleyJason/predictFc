"""SQLAlchemy model for predictions table."""

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Prediction(Base):
    """Toutes les prédictions ML pour un match."""

    __tablename__ = "predictions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    match_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("matches.id"))
    model_version: Mapped[str | None] = mapped_column(String(50))

    # 1X2
    home_win_proba: Mapped[float | None] = mapped_column(Float)
    draw_proba: Mapped[float | None] = mapped_column(Float)
    away_win_proba: Mapped[float | None] = mapped_column(Float)

    # Score exact
    predicted_home_score: Mapped[int | None] = mapped_column(Integer)
    predicted_away_score: Mapped[int | None] = mapped_column(Integer)
    exact_score_proba: Mapped[float | None] = mapped_column(Float)

    # Over/Under
    over_05_proba: Mapped[float | None] = mapped_column(Float)
    over_15_proba: Mapped[float | None] = mapped_column(Float)
    over_25_proba: Mapped[float | None] = mapped_column(Float)
    over_35_proba: Mapped[float | None] = mapped_column(Float)
    over_45_proba: Mapped[float | None] = mapped_column(Float)

    # BTTS
    btts_proba: Mapped[float | None] = mapped_column(Float)

    # Chance double
    home_draw_proba: Mapped[float | None] = mapped_column(Float)
    away_draw_proba: Mapped[float | None] = mapped_column(Float)
    home_away_proba: Mapped[float | None] = mapped_column(Float)

    # Qualification
    home_qualify_proba: Mapped[float | None] = mapped_column(Float)
    away_qualify_proba: Mapped[float | None] = mapped_column(Float)

    # Métadonnées
    confidence_score: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    match: Mapped["Match"] = relationship("Match", back_populates="predictions")  # noqa: F821
    smart_tickets: Mapped[list["SmartTicket"]] = relationship("SmartTicket", back_populates="prediction")  # noqa: F821

    def __repr__(self) -> str:
        """Représentation lisible."""
        return f"<Prediction match={self.match_id} model={self.model_version}>"
