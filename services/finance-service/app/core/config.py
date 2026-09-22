from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Finance Service"
    app_version: str = "1.0.0"
    secret_key: str = "change-me-before-production"
    access_token_expire_minutes: int = 30
    database_url: str = "sqlite:///./finance.db"
    cors_origins: str = "http://127.0.0.1:5500,http://localhost:5500,https://personal-finance-pi-jet.vercel.app,https://finance-front-dl9sf7pge-crdxzs-projects.vercel.app"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()


def get_cors_origins() -> list[str]:
    configured = [origin.strip() for origin in get_settings().cors_origins.split(",") if origin.strip()]
    public_frontends = [
        "https://personal-finance-pi-jet.vercel.app",
        "https://finance-front-dl9sf7pge-crdxzs-projects.vercel.app",
    ]
    return list(dict.fromkeys(configured + public_frontends))
