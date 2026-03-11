"""
Application settings loaded from the project-root .env file.

Path resolution (config.py lives at backend/app/core/config.py):
  parent  → backend/app/core/
  parent  → backend/app/
  parent  → backend/
  parent  → project root  (predictFc/)
"""
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
_ENV_FILE = _PROJECT_ROOT / ".env"


class Settings(BaseSettings):
    """All runtime configuration, sourced from environment variables / .env."""

    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # App
    app_env: str = "development"
    app_secret_key: str = "change-me"

    # Database (required)
    database_url: str

    # football-data.org
    football_data_api_key: str = ""
    football_data_base_url: str = "https://api.football-data.org/v4"

    # MLflow / DagsHub (optional)
    mlflow_tracking_uri: str = ""
    dagshub_token: str = ""


settings = Settings()
