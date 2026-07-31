from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "SwasthiQ EOD Billing & Analytics Agent"
    app_version: str = "1.0.0"
    app_env: Literal["development", "test", "production"] = "development"
    database_url: str = "sqlite:///./swasthiq_eod.db"
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:5173"])
    max_records_per_request: int = Field(default=10_000, ge=1, le=100_000)
    max_request_body_bytes: int = Field(default=5_242_880, ge=1)
    store_rejected_raw_rows: bool = False

    llm_provider: Literal["disabled", "openai_compatible"] = "disabled"
    llm_api_key: str | None = None
    llm_base_url: str = "https://api.openai.com/v1"
    llm_model: str = "gpt-5-mini"
    llm_timeout_seconds: float = Field(default=20.0, ge=1, le=120)

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: object) -> object:
        if isinstance(value, str):
            return [part.strip() for part in value.split(",") if part.strip()]
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
