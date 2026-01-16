from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="LOGLENS_",
        extra="ignore",
    )

    app_name: str = "LogLens"
    environment: str = "development"
    database_url: str = "sqlite:///./data/runtime/loglens.sqlite3"
    result_ttl_hours: int = 24
    max_upload_bytes: int = 5 * 1024 * 1024
    max_log_lines: int = 50_000
    queue_capacity: int = 8
    openai_model: str = "gpt-5-mini"
    model_dir: Path = Path("artifacts/models")
    static_dir: Path = Path("frontend/dist")


@lru_cache
def get_settings() -> Settings:
    return Settings()
