"""Application settings loaded from environment variables."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

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

    app_env: str = "development"
    app_secret_key: str = "change-me"
    database_url: str
    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_key: str = ""
    football_data_api_key: str = ""
    football_data_base_url: str = "https://api.football-data.org/v4"
    mlflow_tracking_uri: str = ""
    dagshub_token: str = ""


settings = Settings()
