"""ReasonFlow core configuration module."""

from __future__ import annotations

from typing import Any

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # App
    APP_ENV: str = "development"
    APP_DEBUG: bool = True

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/reasonflow"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Google Gemini API (used by LangChain)
    GEMINI_API_KEY: str = ""

    # Gmail OAuth
    GMAIL_CLIENT_ID: str = ""
    GMAIL_CLIENT_SECRET: str = ""
    GMAIL_REDIRECT_URI: str = "http://localhost:3000/auth/gmail/callback"

    # JWT Authentication
    JWT_SECRET_KEY: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 30

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v: Any) -> list[str]:
        if isinstance(v, str):
            import json
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return [origin.strip() for origin in v.split(",")]
        return v

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"

    def validate_production(self) -> None:
        """Validate required configuration for production environment.

        Raises:
            ValueError: If any required production configuration is missing or invalid.
        """
        errors = []

        # Check JWT_SECRET_KEY
        if not self.JWT_SECRET_KEY or self.JWT_SECRET_KEY == "change-me-in-production":
            errors.append(
                "JWT_SECRET_KEY must be set to a secure value in production "
                "(not the default 'change-me-in-production')"
            )

        # Check GEMINI_API_KEY
        if not self.GEMINI_API_KEY or not self.GEMINI_API_KEY.strip():
            errors.append("GEMINI_API_KEY must be configured in production")

        # Check DATABASE_URL
        if not self.DATABASE_URL or not self.DATABASE_URL.strip():
            errors.append("DATABASE_URL must be configured in production")

        if errors:
            msg = "Production configuration errors:\n"
            msg += "\n".join(f"  - {e}" for e in errors)
            raise ValueError(msg)


settings = Settings()
