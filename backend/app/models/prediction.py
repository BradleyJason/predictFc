"""ORM model for the `predictions` table."""
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.match import Match
    from app.models.smart_ticket import SmartTicket


class Prediction(Base):
    """Model-generated prediction for a single match."""

    __tablename__ = "predictions"

    id: Mapped[int] = mapped_column(primary_key=True)
    match_id: Mapped[int | None] = mapped_column(ForeignKey("matches.id"))
    model_version: Mapped[str | None] = mapped_column(String(50))

    # 1X2
    home_win_proba: Mapped[float | None] = mapped_column(Float)
    draw_proba: Mapped[float | None] = mapped_column(Float)
    away_win_proba: Mapped[float | None] = mapped_column(Float)

    # Score exact — stored as float (expected goals from Poisson model)
    predicted_home_score: Mapped[float | None] = mapped_column(Float)
    predicted_away_score: Mapped[float | None] = mapped_column(Float)
    exact_score_proba: Mapped[float | None] = mapped_column(Float)

    # Over / Under
    over_05_proba: Mapped[float | None] = mapped_column(Float)
    over_15_proba: Mapped[float | None] = mapped_column(Float)
    over_25_proba: Mapped[float | None] = mapped_column(Float)
    over_35_proba: Mapped[float | None] = mapped_column(Float)
    over_45_proba: Mapped[float | None] = mapped_column(Float)

    # BTTS
    btts_proba: Mapped[float | None] = mapped_column(Float)

    # Double chance
    home_draw_proba: Mapped[float | None] = mapped_column(Float)  # 1X
    away_draw_proba: Mapped[float | None] = mapped_column(Float)  # X2
    home_away_proba: Mapped[float | None] = mapped_column(Float)  # 12

    # Qualification (knockout stages)
    home_qualify_proba: Mapped[float | None] = mapped_column(Float)
    away_qualify_proba: Mapped[float | None] = mapped_column(Float)

    # Metadata
    confidence_score: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    # Relationships
    match: Mapped["Match | None"] = relationship("Match", back_populates="predictions")
    smart_tickets: Mapped[list["SmartTicket"]] = relationship(
        "SmartTicket", back_populates="prediction"
    )
