"""phase4b_fix_injury_remove_player_fk
Revision ID: 8653d6cbfdc0
Revises: 01f2ec402355
Create Date: 2026-03-12 17:10:50.800818
"""
from typing import Sequence, Union
import sqlalchemy as sa
from alembic import op

revision: str = '8653d6cbfdc0'
down_revision: Union[str, Sequence[str], None] = '01f2ec402355'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Supprimer FK player_id si elle existe
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name='injuries' AND column_name='player_id'
            ) THEN
                ALTER TABLE injuries DROP COLUMN IF EXISTS player_id;
            END IF;
        END$$;
    """)

    # Ajouter colonne fixture_id pour lier a un match specifique via api_football_id
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns
                WHERE table_name='injuries' AND column_name='fixture_id'
            ) THEN
                ALTER TABLE injuries ADD COLUMN fixture_id INTEGER;
            END IF;
        END$$;
    """)


def downgrade() -> None:
    op.execute("ALTER TABLE injuries ADD COLUMN IF NOT EXISTS player_id INTEGER;")
    op.execute("ALTER TABLE injuries DROP COLUMN IF EXISTS fixture_id;")
