"""initial schema

Revision ID: f6fc3a7b81f6
Revises:
Create Date: 2026-03-10

"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "f6fc3a7b81f6"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Crée toutes les tables du schéma initial PredictFC."""

    # --- competitions ---
    op.create_table(
        "competitions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(10), nullable=False, unique=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("country", sa.String(50), nullable=True),
        sa.Column("season", sa.String(10), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    # --- teams ---
    op.create_table(
        "teams",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("external_id", sa.Integer(), nullable=True, unique=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("short_name", sa.String(50), nullable=True),
        sa.Column(
            "competition_id",
            sa.Integer(),
            sa.ForeignKey("competitions.id"),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    # --- players ---
    op.create_table(
        "players",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("external_id", sa.Integer(), nullable=True, unique=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("position", sa.String(50), nullable=True),
        sa.Column(
            "team_id",
            sa.Integer(),
            sa.ForeignKey("teams.id"),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    # --- matches ---
    op.create_table(
        "matches",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("external_id", sa.Integer(), nullable=True, unique=True),
        sa.Column(
            "competition_id",
            sa.Integer(),
            sa.ForeignKey("competitions.id"),
            nullable=True,
        ),
        sa.Column(
            "home_team_id",
            sa.Integer(),
            sa.ForeignKey("teams.id"),
            nullable=True,
        ),
        sa.Column(
            "away_team_id",
            sa.Integer(),
            sa.ForeignKey("teams.id"),
            nullable=True,
        ),
        sa.Column("match_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("status", sa.String(20), nullable=True),
        sa.Column("home_score", sa.Integer(), nullable=True),
        sa.Column("away_score", sa.Integer(), nullable=True),
        sa.Column("matchday", sa.Integer(), nullable=True),
        sa.Column("stage", sa.String(50), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    # --- player_stats ---
    op.create_table(
        "player_stats",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "player_id",
            sa.Integer(),
            sa.ForeignKey("players.id"),
            nullable=True,
        ),
        sa.Column(
            "match_id",
            sa.Integer(),
            sa.ForeignKey("matches.id"),
            nullable=True,
        ),
        sa.Column("goals", sa.Integer(), server_default="0", nullable=False),
        sa.Column("assists", sa.Integer(), server_default="0", nullable=False),
        sa.Column("minutes", sa.Integer(), server_default="0", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("player_id", "match_id", name="uq_player_match"),
    )

    # --- predictions ---
    op.create_table(
        "predictions",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "match_id",
            sa.Integer(),
            sa.ForeignKey("matches.id"),
            nullable=True,
        ),
        sa.Column("model_version", sa.String(50), nullable=True),
        # 1X2
        sa.Column("home_win_proba", sa.Float(), nullable=True),
        sa.Column("draw_proba", sa.Float(), nullable=True),
        sa.Column("away_win_proba", sa.Float(), nullable=True),
        # Score exact
        sa.Column("predicted_home_score", sa.Integer(), nullable=True),
        sa.Column("predicted_away_score", sa.Integer(), nullable=True),
        sa.Column("exact_score_proba", sa.Float(), nullable=True),
        # Over/Under
        sa.Column("over_05_proba", sa.Float(), nullable=True),
        sa.Column("over_15_proba", sa.Float(), nullable=True),
        sa.Column("over_25_proba", sa.Float(), nullable=True),
        sa.Column("over_35_proba", sa.Float(), nullable=True),
        sa.Column("over_45_proba", sa.Float(), nullable=True),
        # BTTS
        sa.Column("btts_proba", sa.Float(), nullable=True),
        # Chance double
        sa.Column("home_draw_proba", sa.Float(), nullable=True),
        sa.Column("away_draw_proba", sa.Float(), nullable=True),
        sa.Column("home_away_proba", sa.Float(), nullable=True),
        # Qualification
        sa.Column("home_qualify_proba", sa.Float(), nullable=True),
        sa.Column("away_qualify_proba", sa.Float(), nullable=True),
        # Métadonnées
        sa.Column("confidence_score", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    # --- smart_tickets ---
    op.create_table(
        "smart_tickets",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "match_id",
            sa.Integer(),
            sa.ForeignKey("matches.id"),
            nullable=True,
        ),
        sa.Column(
            "prediction_id",
            sa.Integer(),
            sa.ForeignKey("predictions.id"),
            nullable=True,
        ),
        sa.Column(
            "selections",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=False,
        ),
        sa.Column("combined_proba", sa.Float(), nullable=True),
        sa.Column("confidence_score", sa.Integer(), nullable=True),
        sa.Column("mode", sa.String(20), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )

    # --- Index recommandés ---
    op.create_index("idx_matches_date", "matches", ["match_date"])
    op.create_index("idx_matches_competition", "matches", ["competition_id"])
    op.create_index("idx_predictions_match", "predictions", ["match_id"])
    op.create_index("idx_player_stats_player", "player_stats", ["player_id"])
    op.create_index("idx_player_stats_match", "player_stats", ["match_id"])


def downgrade() -> None:
    """Supprime toutes les tables dans l'ordre inverse des dépendances."""
    op.drop_index("idx_player_stats_match", table_name="player_stats")
    op.drop_index("idx_player_stats_player", table_name="player_stats")
    op.drop_index("idx_predictions_match", table_name="predictions")
    op.drop_index("idx_matches_competition", table_name="matches")
    op.drop_index("idx_matches_date", table_name="matches")

    op.drop_table("smart_tickets")
    op.drop_table("predictions")
    op.drop_table("player_stats")
    op.drop_table("matches")
    op.drop_table("players")
    op.drop_table("teams")
    op.drop_table("competitions")
