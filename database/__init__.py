"""
Build My Holiday - Database and Catalogue Management Layer.

Provides:
- In-memory read-only catalogue loader and fast indexing.
- Catalogue validation for referential integrity and constraints.
- MySQL application database connection management and pooling.
- SQLAlchemy 2.0 ORM models for trips and reservations.
- Repositories for data access and persistence.
"""

from database.config import DatabaseConfig, get_db_config
from database.connection import (
    DatabaseConnectionError,
    check_connection,
    dispose_engine,
    get_db_session,
    get_engine,
    get_session_factory,
)
from database.catalog_loader import (
    Catalog,
    CatalogError,
    CatalogFileNotFoundError,
    CatalogLoader,
    CatalogParseError,
    get_catalog,
)
from database.catalog_indexes import CatalogIndexes
from database.catalog_validator import (
    CatalogValidator,
    ValidationReport,
    validate_catalog,
)
from database.models import (
    Base,
    Reservation,
    ReservationItem,
    Trip,
    TripCity,
    TripItem,
)
from database.repositories import (
    ReservationRepository,
    TripRepository,
)

__all__ = [
    # Config & Connection
    "DatabaseConfig",
    "get_db_config",
    "get_engine",
    "get_session_factory",
    "get_db_session",
    "check_connection",
    "dispose_engine",
    "DatabaseConnectionError",
    # Catalogue Loader & Indexes
    "Catalog",
    "CatalogLoader",
    "CatalogIndexes",
    "CatalogError",
    "CatalogFileNotFoundError",
    "CatalogParseError",
    "get_catalog",
    # Catalogue Validator
    "CatalogValidator",
    "ValidationReport",
    "validate_catalog",
    # Models
    "Base",
    "Trip",
    "TripCity",
    "TripItem",
    "Reservation",
    "ReservationItem",
    # Repositories
    "TripRepository",
    "ReservationRepository",
]
