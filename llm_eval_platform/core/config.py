from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "llm-eval-platform"
    environment: str = "local"
    debug: bool = False
    log_level: str = "INFO"

    api_host: str = "0.0.0.0"
    api_port: int = 8000

    database_url: str = Field(
        default="postgresql+psycopg2://postgres:postgres@postgres:5432/llm_eval_platform"
    )
    redis_url: str = "redis://redis:6379/0"

    auto_create_tables: bool = False

    api_key_records: list[str] = Field(default_factory=lambda: ["dev-admin:tenant-dev:admin:dev-secret"])
    requests_per_minute: int = 120
    artifact_bucket: str = "llm-eval-artifacts"
    artifact_prefix: str = "tenant-artifacts"
    regression_score_drop_threshold: float = 0.03
    regression_failure_rate_increase_threshold: float = 0.05
    tenant_daily_run_quota: int = 200

@lru_cache
def get_settings() -> Settings:
    return Settings()
