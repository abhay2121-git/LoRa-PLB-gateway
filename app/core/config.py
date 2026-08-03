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

    # LoRa Radio Parameters
    lora_frequency: float = 433.0
    lora_bandwidth: int = 125000
    lora_coding_rate: int = 5
    lora_spreading_factor: int = 7
    lora_tx_power: int = 17
    lora_rx_timeout: int = 10
    lora_ack_timeout: int = 5
    lora_retry_count: int = 3

    # Hardware SPI / GPIO Settings
    spi_bus: int = 0
    spi_device: int = 0
    gpio_reset_pin: int = 25
    gpio_dio0_pin: int = 24

    # Timeout & Cache Settings
    heartbeat_timeout_seconds: int = 900
    duplicate_cache_ttl_seconds: int = 3600

    # Queue Worker Settings
    ack_queue_workers: int = 1
    outbound_queue_workers: int = 1

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