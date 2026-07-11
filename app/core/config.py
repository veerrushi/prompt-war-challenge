"""
Application settings loaded from environment variables / .env file.

Uses pydantic-settings for type-safe, validated configuration with a
module-level cached accessor so the Settings object is only constructed once.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for RainReady AI.

    All fields can be overridden via environment variables or a .env file
    placed in the project root.
    """

    groq_api_key: str = ""
    port: int = 8080

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance (constructed at most once per process)."""
    return Settings()
