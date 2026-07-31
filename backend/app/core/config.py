from functools import lru_cache
from typing import Literal

from pydantic import AliasChoices, Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.limits import (
    DEFAULT_MAX_ISSUES_PER_REQUEST,
    DEFAULT_MAX_ISSUES_PER_ROW,
    DEFAULT_MAX_JSON_DEPTH,
    DEFAULT_MAX_JSON_NODES,
    DEFAULT_MAX_LINE_ITEMS_PER_RECORD,
    DEFAULT_MAX_MEDICINE_COMPARISONS_PER_REPORT,
    DEFAULT_MAX_MEDICINE_WARNINGS_PER_REPORT,
    DEFAULT_MAX_PERSISTED_ISSUES_PER_REPORT,
    DEFAULT_MAX_RECORDS_PER_IMPORT,
    MAX_SAFE_JSON_INTEGER,
)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore", populate_by_name=True)

    app_name: str = "SwasthiQ EOD Billing & Analytics Agent"
    app_version: str = "1.0.0"
    app_env: Literal["development", "test", "production"] = "development"
    database_url: str = "sqlite:///./swasthiq_eod.db"
    cors_allowed_origins: str | list[str] = Field(
        default="http://localhost:5173,http://127.0.0.1:5173",
        validation_alias=AliasChoices("cors_origins", "CORS_ALLOWED_ORIGINS", "CORS_ORIGINS"),
    )
    cors_allow_credentials: bool = False
    log_level: str = "INFO"
    log_format: Literal["text", "json"] = "text"
    log_include_request_id: bool = True
    max_records_per_request: int = Field(default=DEFAULT_MAX_RECORDS_PER_IMPORT, ge=1, le=100_000, validation_alias=AliasChoices("MAX_RECORDS_PER_IMPORT", "MAX_RECORDS_PER_REQUEST"))
    max_request_body_bytes: int = Field(default=5_242_880, ge=1)
    store_rejected_raw_rows: bool = False
    narrative_rate_limit_per_minute: int = Field(default=12, ge=0, le=600)
    max_json_depth: int = Field(default=DEFAULT_MAX_JSON_DEPTH, ge=1, le=512)
    max_json_nodes: int = Field(default=DEFAULT_MAX_JSON_NODES, ge=1, le=2_000_000)
    max_line_items_per_record: int = Field(default=DEFAULT_MAX_LINE_ITEMS_PER_RECORD, ge=1, le=10_000)
    max_issues_per_row: int = Field(default=DEFAULT_MAX_ISSUES_PER_ROW, ge=1, le=1_000)
    max_issues_per_request: int = Field(default=DEFAULT_MAX_ISSUES_PER_REQUEST, ge=1, le=10_000)
    max_persisted_issues_per_report: int = Field(default=DEFAULT_MAX_PERSISTED_ISSUES_PER_REPORT, ge=1, le=10_000)
    max_medicine_warnings_per_report: int = Field(default=DEFAULT_MAX_MEDICINE_WARNINGS_PER_REPORT, ge=0, le=5_000)
    max_medicine_comparisons_per_report: int = Field(default=DEFAULT_MAX_MEDICINE_COMPARISONS_PER_REPORT, ge=0, le=5_000_000)
    max_safe_paise: int = Field(default=MAX_SAFE_JSON_INTEGER, ge=1, le=MAX_SAFE_JSON_INTEGER)

    llm_enabled: bool = True
    llm_provider: Literal["disabled", "nvidia"] = "nvidia"
    nvidia_api_key: SecretStr | None = None
    nvidia_api_keys: SecretStr | None = None
    nvidia_model: str = "nvidia/nemotron-3-nano-30b-a3b"
    nvidia_base_url: str | None = None
    llm_timeout_seconds: float = Field(default=25.0, gt=0, le=120)
    llm_max_tokens: int = Field(default=700, ge=1, le=4_000)
    llm_temperature: float = Field(default=0.0, ge=0.0, le=1.0)
    llm_transport_retries: int = Field(default=1, ge=0, le=3)

    @field_validator("cors_allowed_origins", mode="before")
    @classmethod
    def parse_cors_allowed_origins(cls, value: object) -> object:
        return value

    @property
    def cors_origins(self) -> list[str]:
        value = self.cors_allowed_origins
        if isinstance(value, str):
            return [part.strip() for part in value.split(",") if part.strip()]
        return value

    @property
    def nvidia_api_key_pool(self) -> list[SecretStr]:
        values: list[SecretStr] = []
        if self.nvidia_api_keys is not None:
            raw_pool = self.nvidia_api_keys.get_secret_value()
            values.extend(SecretStr(part.strip()) for part in raw_pool.split(",") if part.strip())
        if not values and self.nvidia_api_key is not None and self.nvidia_api_key.get_secret_value():
            values.append(self.nvidia_api_key)
        return values

    @model_validator(mode="after")
    def validate_limit_relationships(self) -> "Settings":
        if self.max_issues_per_row > self.max_issues_per_request:
            raise ValueError("MAX_ISSUES_PER_ROW cannot exceed MAX_ISSUES_PER_REQUEST")
        if self.max_persisted_issues_per_report > self.max_issues_per_request:
            raise ValueError("MAX_PERSISTED_ISSUES_PER_REPORT cannot exceed MAX_ISSUES_PER_REQUEST")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
