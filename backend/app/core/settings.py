"""
Central application settings.

All configuration is environment-driven with safe local-development
defaults. In production, set these via environment variables:

  AFK_SECRET_KEY   - required in production; random per-boot fallback in dev
  DATABASE_URL     - defaults to local sqlite file
  AFK_CORS_ORIGINS - comma-separated allowed origins (default: localhost dev)
  AFK_ENV          - "development" (default) or "production"
  AFK_SEED_DEMO    - "true" to seed demo org on empty DB (default: false)
  AFK_DEMO_MODE    - "true" to enable one-click demo sessions (default: on in dev, off in prod)
"""
import os
import secrets
from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    env: str = os.getenv("AFK_ENV", "development")

    # Secret key: never hardcoded. In development, a random key is
    # generated per process (tokens invalidate on restart — acceptable
    # for dev). In production, AFK_SECRET_KEY must be provided.
    secret_key: str = os.getenv("AFK_SECRET_KEY") or secrets.token_urlsafe(48)

    algorithm: str = "HS256"
    access_token_expire_minutes: int = int(
        os.getenv("AFK_TOKEN_EXPIRE_MINUTES", str(60 * 24 * 7))
    )

    database_url: str = os.getenv("DATABASE_URL", "sqlite:///database.db")

    # CORS: explicit origins only. Wildcard + credentials is rejected by
    # browsers and is an unsafe default; we list dev origins explicitly.
    cors_origins: list[str] = [
        o.strip()
        for o in os.getenv(
            "AFK_CORS_ORIGINS",
            "http://127.0.0.1:8000,http://localhost:8000",
        ).split(",")
        if o.strip()
    ]

    # Minimum password length enforced at registration.
    min_password_length: int = 8

    # Demo seed: off by default so real founders start with empty evidence.
    seed_demo: bool = os.getenv("AFK_SEED_DEMO", "false").lower() in ("1", "true", "yes")

    @property
    def is_production(self) -> bool:
        return self.env.lower() == "production"

    @property
    def demo_enabled(self) -> bool:
        """One-click demo sessions: on in development unless explicitly disabled."""
        raw = os.getenv("AFK_DEMO_MODE")
        if raw is not None:
            return raw.lower() in ("1", "true", "yes")
        return not self.is_production


@lru_cache
def get_settings() -> Settings:
    s = Settings()
    if s.is_production and not os.getenv("AFK_SECRET_KEY"):
        raise RuntimeError(
            "AFK_SECRET_KEY must be set in production. "
            "Generate one with: python -c \"import secrets; print(secrets.token_urlsafe(48))\""
        )
    return s
