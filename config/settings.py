# config/settings.py

"""
Central configuration — loads from .env and environment variables.
"""

import os
from functools import lru_cache
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment."""

    # GCP Project
    PROJECT_ID: str = Field(default="mapa-assistant")
    REGION: str = Field(default="us-central1")
    ENVIRONMENT: str = Field(default="production")

    # Vertex AI / Gemini
    MODEL_NAME: str = Field(default="gemini-2.5-pro")
    VERTEX_AI_LOCATION: str = Field(default="us-central1")

    # API
    API_HOST: str = Field(default="0.0.0.0")
    API_PORT: int = Field(default=8080)
    API_KEY: str = Field(default="")

    # Firestore
    FIRESTORE_PROJECT_ID: str = Field(default="mapa-assistant")
    FIRESTORE_DATABASE: str = Field(default="(default)")

    # Logging
    LOG_LEVEL: str = Field(default="INFO")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()