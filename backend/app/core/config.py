"""Application settings loaded from environment variables."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Le .env est à la racine du projet (2 niveaux au-dessus de backend/app/core/)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
_ENV_FILE = _PROJECT_ROOT / ".env"


class Settings(BaseSettings):
    """Central config — toutes les variables d'env du projet."""

    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # App
    app_env: str = "development"
    app_secret_key: str = "change-me"

    # Database (Supabase / PostgreSQL)
    database_url: str

    # Supabase
    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_key: str = ""

    # Football Data API
    football_data_api_key: str = ""
    football_data_base_url: str = "https://api.football-data.org/v4"

    # MLflow / DagsHub
    mlflow_tracking_uri: str = ""
    dagshub_token: str = ""


settings = Settings()
