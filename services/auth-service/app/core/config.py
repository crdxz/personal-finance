from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Personal Finance Auth Service"
    app_version: str = "1.0.0"
    environment: str = "development"
    secret_key: str = "change-me-in-development"
    access_token_expire_minutes: int = 30
    database_url: str = "sqlite:///./auth.db"
    cors_origins: str = "http://127.0.0.1:5500,http://localhost:5500"
    supabase_url: str | None = None
    supabase_key: str | None = None

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()


def get_cors_origins() -> list[str]:
    return [origin.strip() for origin in get_settings().cors_origins.split(",") if origin.strip()]
