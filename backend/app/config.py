"""Configuration settings for Opportunity Radar."""

import os
from functools import lru_cache
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # App
    app_name: str = "Opportunity Radar"
    debug: bool = False
    api_prefix: str = "/api"

    # Database: Use SQLite by default for development, PostgreSQL for production
    database_type: Literal["sqlite", "postgresql"] = "sqlite"
    sqlite_db_path: str = "opportunity_radar.db"

    # PostgreSQL Configuration
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_user: str = "opportunity_user"
    postgres_password: str = ""
    postgres_db: str = "opportunity_radar"
    postgres_ssl_mode: str = "prefer"

    @property
    def database_url(self) -> str:
        """Construct database URL based on database_type."""
        if self.database_type == "sqlite":
            return f"sqlite+aiosqlite:///{self.sqlite_db_path}"
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}@"
            f"{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def database_sync_url(self) -> str:
        """Construct sync database URL for migrations."""
        if self.database_type == "sqlite":
            return f"sqlite:///{self.sqlite_db_path}"
        return (
            f"postgresql+psycopg2://{self.postgres_user}:{self.postgres_password}@"
            f"{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    # JWT Configuration
    jwt_secret_key: str = ""
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7

    @field_validator("jwt_secret_key", mode="before")
    @classmethod
    def validate_jwt_secret(cls, v: str, info) -> str:
        if not v:
            debug_mode = os.getenv("DEBUG", "").lower()
            if debug_mode == "true":
                return "dev-secret-key-not-for-production"
        return v

    # Stripe Configuration
    stripe_secret_key: str = ""
    stripe_publishable_key: str = ""
    stripe_webhook_secret: str = ""
    stripe_price_id_free: str = ""
    stripe_price_id_pro: str = ""
    stripe_price_id_team: str = ""

    # AI Providers
    ai_provider: Literal["openrouter", "claude", "gemini", "ollama", "local"] = (
        "openrouter"
    )

    # OpenRouter (default - free models)
    openrouter_api_key: str = ""
    openrouter_model: str = "deepseek/deepseek-r1-0528"
    openrouter_fallback_model: str = "meta-llama/llama-3.3-70b-instruct"

    # Claude
    claude_api_key: str = ""
    claude_base_url: str = ""

    # Gemini
    gemini_api_key: str = ""

    # Ollama (local)
    ollama_model: str = "deepseek-r1:14b"
    ollama_base_url: str = "http://localhost:11434"

    # ElevenLabs (for phone calls)
    elevenlabs_api_key: str = ""
    elevenlabs_voice_id: str = "21m00tcm4elvl8d8201q"  # Default voice

    # Reddit (PRAW)
    reddit_client_id: str = ""
    reddit_client_secret: str = ""
    reddit_user_agent: str = "OpportunityRadar/1.0"

    # Scraping settings
    scrape_interval_hours: int = 24
    max_posts_per_source: int = 500
    request_delay_seconds: float = 1.0

    # CORS
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:5175",
        "http://localhost:3000",
    ]

    # Authentication
    api_key: str = ""

    @field_validator("api_key", mode="before")
    @classmethod
    def validate_api_key(cls, v: str, info) -> str:
        if not v:
            debug_mode = os.getenv("DEBUG", "").lower()
            if debug_mode == "true":
                return "dev-api-key-not-for-production"
        return v

    # Redis (for background jobs)
    redis_url: str = "redis://localhost:6379/0"

    # SMTP Configuration for email alerts
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from_email: str = "alerts@opportunityradar.io"
    smtp_from_name: str = "Opportunity Radar"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
