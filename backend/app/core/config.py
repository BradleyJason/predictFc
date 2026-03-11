"""
Application settings loaded from the project-root .env file.
...
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
        case_sensitive=False,   # ← ajout de theirs
        extra="ignore",
    )

    app_env: str = "development"
    app_secret_key: str = "change-me"
    database_url: str

    # Supabase                  ← ajout de theirs
    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_key: str = ""

    # football-data.org
    football_data_api_key: str = ""
    football_data_base_url: str = "https://api.football-data.org/v4"

    # MLflow / DagsHub
    mlflow_tracking_uri: str = ""
    dagshub_token: str = ""

settings = Settings()
