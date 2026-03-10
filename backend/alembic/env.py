"""Alembic environment — connecte nos modèles SQLAlchemy à Alembic."""

import sys
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import engine_from_config, pool

from alembic import context

# Ajoute le dossier backend/ au sys.path pour résoudre les imports `app.*`
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.config import settings  # noqa: E402
from app.core.database import Base  # noqa: E402

# Import de tous les modèles pour que SQLAlchemy les enregistre dans Base.metadata
import app.models  # noqa: E402, F401

# Alembic Config object
config = context.config

# Injecte la DATABASE_URL depuis les settings (priorité sur alembic.ini)
config.set_main_option("sqlalchemy.url", settings.database_url)

# Configure les logs Python depuis alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Métadonnées cible pour l'autogenerate
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Exécute les migrations en mode 'offline' (sans connexion active).

    Utile en CI ou pour générer du SQL à appliquer manuellement.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Exécute les migrations en mode 'online' (connexion active).

    Mode standard pour les déploiements et le développement local.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            # Compare les types de colonnes pour détecter les changements
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
