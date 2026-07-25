# Project Configuration

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    app_name: str = "LoRa PLB Gateway"
    app_version: str = "1.0.0"
    debug: bool = False
    log_level: str = "INFO"

    host: str = "0.0.0.0"
    port: int = 8000

    database_url: str = (
        "postgresql+psycopg://postgres:abhay2121N@localhost:5432/plb_gateway"
    )

    gateway_id: str = "GATEWAY_01"

    # 15 minutes timeout for marking nodes OFFLINE
    node_offline_timeout_seconds: int = 900

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()