"""
Travel catalogue loader for Build My Holiday.

Loads all eight JSON files from hackathon-problem-1-holiday-package/data/catalog/
using Python's built-in json library. Maintains an in-memory, read-only catalogue
and singleton access pattern for application services.
"""

from __future__ import annotations

import copy
import json
import logging
import sys
from pathlib import Path
from typing import Any, Final

# Ensure project root is in sys.path when executed directly
_CURRENT_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _CURRENT_DIR.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from database.catalog_indexes import CatalogIndexes

logger = logging.getLogger(__name__)

# The 8 required catalogue files
CATALOG_FILENAMES: Final[tuple[str, ...]] = (
    "destinations.json",
    "airports.json",
    "flights.json",
    "hotels.json",
    "rooms.json",
    "availability.json",
    "transfers.json",
    "attractions.json",
)


class CatalogError(Exception):
    """Base exception for all catalogue loading and validation operations."""


class CatalogFileNotFoundError(CatalogError):
    """Raised when one or more required catalogue JSON files cannot be found."""

    def __init__(self, file_path: Path) -> None:
        super().__init__(f"Required catalogue file not found: {file_path}")
        self.file_path = file_path


class CatalogParseError(CatalogError):
    """Raised when a catalogue file contains malformed or unparseable JSON."""

    def __init__(self, file_path: Path, original_error: Exception) -> None:
        super().__init__(
            f"Failed to parse JSON file {file_path.name} at {file_path}: {original_error}"
        )
        self.file_path = file_path
        self.original_error = original_error


class Catalog:
    """
    Central read-only container holding travel catalogue datasets and lookup indexes.
    All attributes expose read-only copies or cached index structures.
    """

    def __init__(
        self,
        destinations: dict[str, Any],
        airports: list[dict[str, Any]],
        flights: list[dict[str, Any]],
        hotels: list[dict[str, Any]],
        rooms: list[dict[str, Any]],
        availability: list[dict[str, Any]],
        transfers: list[dict[str, Any]],
        attractions: list[dict[str, Any]],
    ) -> None:
        # Keep internal pristine copies
        self._destinations = destinations
        self._airports = airports
        self._flights = flights
        self._hotels = hotels
        self._rooms = rooms
        self._availability = availability
        self._transfers = transfers
        self._attractions = attractions

        # Precompute indexes
        self._indexes = CatalogIndexes(
            destinations=self._destinations,
            airports=self._airports,
            flights=self._flights,
            hotels=self._hotels,
            rooms=self._rooms,
            availability=self._availability,
            transfers=self._transfers,
            attractions=self._attractions,
        )

    @property
    def destinations(self) -> dict[str, Any]:
        """Read-only copy of destinations configuration."""
        return copy.deepcopy(self._destinations)

    @property
    def airports(self) -> list[dict[str, Any]]:
        """Read-only copy of airports list."""
        return [dict(a) for a in self._airports]

    @property
    def flights(self) -> list[dict[str, Any]]:
        """Read-only copy of flights list."""
        return [dict(f) for f in self._flights]

    @property
    def hotels(self) -> list[dict[str, Any]]:
        """Read-only copy of hotels list."""
        return [dict(h) for h in self._hotels]

    @property
    def rooms(self) -> list[dict[str, Any]]:
        """Read-only copy of rooms list."""
        return [dict(r) for r in self._rooms]

    @property
    def availability(self) -> list[dict[str, Any]]:
        """Read-only copy of availability list."""
        return [dict(av) for av in self._availability]

    @property
    def transfers(self) -> list[dict[str, Any]]:
        """Read-only copy of transfers list."""
        return [dict(t) for t in self._transfers]

    @property
    def attractions(self) -> list[dict[str, Any]]:
        """Read-only copy of attractions list."""
        return [dict(att) for att in self._attractions]

    @property
    def indexes(self) -> CatalogIndexes:
        """In-memory index engine for fast queries."""
        return self._indexes

    def stats(self) -> dict[str, int]:
        """Summary count of catalogue records."""
        return {
            "airports": len(self._airports),
            "flights": len(self._flights),
            "hotels": len(self._hotels),
            "rooms": len(self._rooms),
            "availability": len(self._availability),
            "transfers": len(self._transfers),
            "attractions": len(self._attractions),
            "destination_countries": len(self._destinations.get("countries", [])),
            "departure_cities": len(self._destinations.get("departure_cities", [])),
        }


class CatalogLoader:
    """
    Loader responsible for reading JSON catalogue files relative to project root.
    """

    @staticmethod
    def get_project_root() -> Path:
        """Return the root path of the project repository."""
        # This file is at <root>/database/catalog_loader.py
        current = Path(__file__).resolve().parent
        root = current.parent
        # Verify problem folder or catalog directory
        if (root / "hackathon-problem-1-holiday-package").exists():
            return root
        # Fallback to current working directory if relative structure changed
        cwd = Path.cwd()
        if (cwd / "hackathon-problem-1-holiday-package").exists():
            return cwd
        return root

    @classmethod
    def get_catalog_dir(cls, custom_dir: Path | str | None = None) -> Path:
        """Resolve the catalogue directory path."""
        if custom_dir is not None:
            return Path(custom_dir)
        root = cls.get_project_root()
        return root / "hackathon-problem-1-holiday-package" / "data" / "catalog"

    @classmethod
    def load_file(cls, file_path: Path) -> Any:
        """
        Load a single JSON file using Python's built-in json library.
        Raises CatalogFileNotFoundError if missing, or CatalogParseError if malformed.
        """
        if not file_path.is_file():
            raise CatalogFileNotFoundError(file_path)

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError as exc:
            raise CatalogParseError(file_path, exc) from exc
        except Exception as exc:
            raise CatalogError(
                f"Unexpected error reading catalogue file {file_path}: {exc}"
            ) from exc

    @classmethod
    def load_all(cls, catalog_dir: Path | str | None = None) -> Catalog:
        """
        Load all 8 JSON files and return a validated Catalog container.
        """
        dir_path = cls.get_catalog_dir(catalog_dir)
        logger.info("Loading travel catalogue from %s", dir_path)

        # Ensure directory exists
        if not dir_path.is_dir():
            raise CatalogFileNotFoundError(dir_path)

        # Load each file explicitly
        destinations = cls.load_file(dir_path / "destinations.json")
        airports = cls.load_file(dir_path / "airports.json")
        flights = cls.load_file(dir_path / "flights.json")
        hotels = cls.load_file(dir_path / "hotels.json")
        rooms = cls.load_file(dir_path / "rooms.json")
        availability = cls.load_file(dir_path / "availability.json")
        transfers = cls.load_file(dir_path / "transfers.json")
        attractions = cls.load_file(dir_path / "attractions.json")

        return Catalog(
            destinations=destinations,
            airports=airports,
            flights=flights,
            hotels=hotels,
            rooms=rooms,
            availability=availability,
            transfers=transfers,
            attractions=attractions,
        )


# Global singleton cache
_CATALOG_INSTANCE: Catalog | None = None


def get_catalog(force_reload: bool = False, catalog_dir: Path | str | None = None) -> Catalog:
    """
    Get the application-wide singleton Catalog instance.
    Loads data once during startup and caches the result.
    Pass force_reload=True if files need to be reloaded.
    """
    global _CATALOG_INSTANCE
    if _CATALOG_INSTANCE is None or force_reload:
        _CATALOG_INSTANCE = CatalogLoader.load_all(catalog_dir=catalog_dir)
    return _CATALOG_INSTANCE
