"""
Configuration management for PrivacyLens.
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Model settings
    spacy_model: str = "en_core_web_sm"
    confidence_threshold: float = 0.5
    use_spacy: bool = True

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_title: str = "PrivacyLens API"
    api_version: str = "1.0.0"

    # Logging
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        env_prefix = "PRIVACYLENS_"


settings = Settings()
