"""Application configuration using environment variables"""

import os
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # API Keys
    anthropic_api_key: str | None = None
    openai_api_key: str | None = None
    google_api_key: str | None = None
    groq_api_key: str | None = None

    # Repository settings
    repo_path: str = "."
    examples_output_path: str | None = None  # None = use <repo_path>/examples

    # LLM Configuration
    default_model: str = "anthropic:claude-sonnet-4-5-20250929"
    temperature: float = 0.7

    # Processing settings
    max_refinement_iterations: int = 3
    discovery_paths: str = "src"  # Comma-separated list of subdirectories to search

    def get_repo_path(self) -> Path:
        """Get repository path as Path object"""
        return Path(self.repo_path).resolve()

    def get_examples_output_path(self) -> Path | None:
        """Get examples output path as Path object, or None if not set"""
        if self.examples_output_path is None:
            return None
        return Path(self.examples_output_path).resolve()

    def get_discovery_paths(self) -> list[str]:
        """Get discovery paths as list of strings"""
        return [p.strip() for p in self.discovery_paths.split(",") if p.strip()]


# Global settings instance
settings = Settings()

# Export only API keys to os.environ for pydantic-ai to discover
# This keeps os.environ clean while making API keys available to LLM providers
if settings.anthropic_api_key:
    os.environ["ANTHROPIC_API_KEY"] = settings.anthropic_api_key
if settings.openai_api_key:
    os.environ["OPENAI_API_KEY"] = settings.openai_api_key
if settings.google_api_key:
    os.environ["GOOGLE_API_KEY"] = settings.google_api_key
