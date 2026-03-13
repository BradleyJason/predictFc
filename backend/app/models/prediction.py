"""SQLAlchemy model for predictions table."""

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, JSON, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Prediction(Base):
    """Toutes les prédictions ML pour un match (1X2, score exact, over/under, BTTS...)."""

    __tablename__ = "predictions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    match_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("matches.id"))
    model_version: Mapped[str | None] = mapped_column(String(50))  # mlflow run_id

    # --- Résultat 1X2 ---
    home_win_proba: Mapped[float | None] = mapped_column(Float)
    draw_proba: Mapped[float | None] = mapped_column(Float)
    away_win_proba: Mapped[float | None] = mapped_column(Float)

    # --- Score exact ---
    predicted_home_score: Mapped[float | None] = mapped_column(Float)
    predicted_away_score: Mapped[float | None] = mapped_column(Float)
    exact_score_proba: Mapped[float | None] = mapped_column(Float)

    # --- Total buts (Over/Under) ---
    over_05_proba: Mapped[float | None] = mapped_column(Float)
    over_15_proba: Mapped[float | None] = mapped_column(Float)
    over_25_proba: Mapped[float | None] = mapped_column(Float)
    over_35_proba: Mapped[float | None] = mapped_column(Float)
    over_45_proba: Mapped[float | None] = mapped_column(Float)

    # --- BTTS (les deux équipes marquent) ---
    btts_proba: Mapped[float | None] = mapped_column(Float)

    # --- Chance double ---
    home_draw_proba: Mapped[float | None] = mapped_column(Float)  # 1X
    away_draw_proba: Mapped[float | None] = mapped_column(Float)  # X2
    home_away_proba: Mapped[float | None] = mapped_column(Float)  # 12

    # --- Qualification (phases éliminatoires) ---
    home_qualify_proba: Mapped[float | None] = mapped_column(Float)
    away_qualify_proba: Mapped[float | None] = mapped_column(Float)

    # --- Score exact détaillé ---
    top_scores: Mapped[list | None] = mapped_column(JSON, default=list)
    # --- Métadonnées ---
    confidence_score: Mapped[int | None] = mapped_column(Integer)  # 0-100
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relations
    match: Mapped["Match"] = relationship("Match", back_populates="predictions")  # noqa: F821
    smart_tickets: Mapped[list["SmartTicket"]] = relationship(  # noqa: F821
        "SmartTicket", back_populates="prediction"
    )

    def __repr__(self) -> str:
        """Représentation lisible du modèle."""
        return f"<Prediction match={self.match_id} model={self.model_version}>"
