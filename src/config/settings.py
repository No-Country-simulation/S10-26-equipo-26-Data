from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = "development"
    log_level: str = "INFO"

    ingest_mode: str = "api"  # api | postgres (decisión #1, pendiente)
    database_url: str | None = None
    api_url: str | None = None
    api_key: str | None = None

    exchange_rate_api_url: str = ""
    exchange_rate_api_key: str | None = None
    fx_rate_type: str = "oficial"  # oficial | paralelo

    download_delay: float = 1.5
    collection_max_retries: int = 2


@lru_cache
def get_settings() -> Settings:
    return Settings()
