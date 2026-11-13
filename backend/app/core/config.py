"""Settings from environment variables and the repo-root `.env` file."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# backend/app/core/config.py -> parents[3] is the repo root (HolidayBooking/)
REPO_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(REPO_ROOT / ".env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    DB_URL: str = "mysql+pymysql://holiday:holiday@localhost:3306/holiday"
    DATA_DIR: Path = REPO_ROOT / "data"
    DATABASE_DIR: Path = REPO_ROOT / "database"
    API_PORT: int = 8000
    WEB_PORT: int = 5173
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"
    # Apply database/schema/*.sql and seed the catalog tables on startup.
    DB_AUTO_INIT: bool = True

    @property
    def catalog_dir(self) -> Path:
        return self.DATA_DIR / "catalog"

    @property
    def images_dir(self) -> Path:
        return self.DATA_DIR / "images"

    @property
    def schema_dir(self) -> Path:
        return self.DATABASE_DIR / "schema"

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
