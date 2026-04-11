"""Configuration models for synth-research."""

from pathlib import Path

import yaml
from pydantic import BaseModel
from pydantic_settings import BaseSettings


class ModelConfig(BaseModel):
    """A configured LLM model."""

    model_id: str
    label: str


class WebSearchConfig(BaseModel):
    """Web search provider configuration."""

    provider: str = "tavily"


class AppConfig(BaseSettings):
    """Application configuration loaded from YAML + env vars."""

    models: list[ModelConfig] = []
    default_model_count: int = 2
    web_search: WebSearchConfig = WebSearchConfig()

    @classmethod
    def load(cls) -> "AppConfig":
        """Load config from ~/.config/synth-research/config.yaml."""
        config_path = Path.home() / ".config" / "synth-research" / "config.yaml"
        if not config_path.exists():
            return cls()
        with open(config_path) as f:
            data = yaml.safe_load(f) or {}
        return cls(**data)
