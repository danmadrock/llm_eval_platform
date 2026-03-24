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


@lru_cache
def get_settings() -> Settings:
    return Settings()
