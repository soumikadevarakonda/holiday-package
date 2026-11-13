"""
Application configuration for Build My Holiday backend.
"""

from __future__ import annotations

import os
from pathlib import Path
from pydantic import BaseModel, Field

# Locate repository root
PROJECT_ROOT = Path(__file__).resolve().parents[3]


def get_data_dir() -> Path:
    """Resolve data directory path (checks data/ then datasets/)."""
    for candidate in [
        PROJECT_ROOT / "data",
        PROJECT_ROOT / "datasets",
    ]:
        if candidate.is_dir() and ((candidate / "catalog").exists() or (candidate / "data" / "catalog").exists()):
            return candidate
    return PROJECT_ROOT / "data"


class Settings(BaseModel):
    """Global application settings."""

    app_name: str = "Build My Holiday API"
    app_version: str = "1.0.0"
    debug: bool = Field(default_factory=lambda: os.getenv("DEBUG", "false").lower() in ("true", "1"))
    data_dir: Path = Field(default_factory=get_data_dir)
    cors_origins: list[str] = Field(
        default_factory=lambda: [
            origin.strip()
            for origin in os.getenv("CORS_ORIGINS", "*").split(",")
            if origin.strip()
        ]
    )
    api_prefix: str = "/api"


settings = Settings()
