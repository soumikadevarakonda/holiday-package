"""
Database configuration for Build My Holiday.

Reads MySQL credentials and pool parameters from environment variables
or an optional .env file at the project root. Never hardcodes credentials.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote_plus


def find_project_root() -> Path:
    """Locate the project root directory containing .env or the catalog folder."""
    current = Path(__file__).resolve().parent
    for parent in [current, current.parent, current.parent.parent]:
        if (
            (parent / ".env").exists()
            or (parent / "datasets").exists()
            or (parent / "hackathon-problem-1-holiday-package").exists()
        ):
            return parent
    return current.parent


def load_env_file(env_path: Path | None = None) -> None:
    """
    Lightweight .env file loader that does not require third-party dependencies.
    Only populates os.environ if the key is not already present.
    """
    if env_path is None:
        env_path = find_project_root() / ".env"

    if not env_path.is_file():
        return

    try:
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" in line:
                    key, val = line.split("=", 1)
                    key = key.strip()
                    val = val.strip().strip("'\"")
                    if key and key not in os.environ:
                        os.environ[key] = val
    except Exception:
        # Ignore read errors on optional .env
        pass


# Automatically attempt to load .env on module import
load_env_file()


@dataclass(frozen=True)
class DatabaseConfig:
    """Immutable database configuration read from environment."""

    host: str = "localhost"
    port: int = 3306
    user: str = "root"
    password: str = ""
    name: str = "build_my_holiday"
    pool_size: int = 5
    max_overflow: int = 10
    pool_recycle: int = 3600
    pool_timeout: int = 30
    database_url: str | None = None

    @classmethod
    def from_env(cls) -> "DatabaseConfig":
        """Construct database configuration from current environment variables."""
        # Refresh env file in case it was created after startup
        load_env_file()

        raw_port = os.getenv("DB_PORT", "3306")
        try:
            port = int(raw_port)
        except ValueError:
            port = 3306

        raw_pool_size = os.getenv("DB_POOL_SIZE", "5")
        try:
            pool_size = int(raw_pool_size)
        except ValueError:
            pool_size = 5

        raw_max_overflow = os.getenv("DB_MAX_OVERFLOW", "10")
        try:
            max_overflow = int(raw_max_overflow)
        except ValueError:
            max_overflow = 10

        raw_pool_recycle = os.getenv("DB_POOL_RECYCLE", "3600")
        try:
            pool_recycle = int(raw_pool_recycle)
        except ValueError:
            pool_recycle = 3600

        raw_pool_timeout = os.getenv("DB_POOL_TIMEOUT", "30")
        try:
            pool_timeout = int(raw_pool_timeout)
        except ValueError:
            pool_timeout = 30

        return cls(
            host=os.getenv("DB_HOST", "localhost"),
            port=port,
            user=os.getenv("DB_USER", "root"),
            password=os.getenv("DB_PASSWORD", ""),
            name=os.getenv("DB_NAME", "build_my_holiday"),
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_recycle=pool_recycle,
            pool_timeout=pool_timeout,
            database_url=os.getenv("DATABASE_URL"),
        )

    def get_url(self) -> str:
        """
        Return the SQLAlchemy connection URL.
        If DATABASE_URL is explicitly provided, use that;
        otherwise assemble a MySQL connection URL using PyMySQL driver.
        """
        if self.database_url:
            return self.database_url

        encoded_user = quote_plus(self.user)
        encoded_password = quote_plus(self.password)
        auth = f"{encoded_user}:{encoded_password}" if self.password else encoded_user
        return (
            f"mysql+pymysql://{auth}@{self.host}:{self.port}/{self.name}"
            "?charset=utf8mb4"
        )

    def get_pool_kwargs(self) -> dict:
        """Return engine keyword arguments for connection pooling."""
        url = self.get_url()
        # SQLite does not support standard queue pool kwargs
        if url.startswith("sqlite"):
            return {}

        return {
            "pool_size": self.pool_size,
            "max_overflow": self.max_overflow,
            "pool_recycle": self.pool_recycle,
            "pool_timeout": self.pool_timeout,
            "pool_pre_ping": True,
        }


def get_db_config() -> DatabaseConfig:
    """Return current DatabaseConfig instance."""
    return DatabaseConfig.from_env()
