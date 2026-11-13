"""
Build My Holiday — Main FastAPI Application.
Integrates all 15 API endpoints, database persistence, and catalogue layer.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from backend.app.catalog.router import router as catalog_router
from backend.app.changes.router import router as changes_router
from backend.app.core.config import settings
from backend.app.core.database import init_db, is_database_connected
from backend.app.core.engine_adapter import get_engine_adapter
from backend.app.core.errors import AppError
from backend.app.export.router import router as export_router
from backend.app.packages.router import router as packages_router
from backend.app.parser.router import router as parser_router
from backend.app.reservations.router import router as reservations_router
from database.catalog_loader import get_catalog

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle."""
    logger.info("Initializing Build My Holiday API...")
    # Initialize database tables
    init_db()
    # Preload catalogue
    try:
        catalog = get_catalog()
        logger.info("Catalogue preloaded successfully (%s)", catalog.stats())
    except Exception as exc:
        logger.warning("Catalogue preload failed: %s", exc)
    yield
    logger.info("Shutting down Build My Holiday API...")


app = FastAPI(
    title=settings.app_name,
    description="Build My Holiday Package Builder & Reservation API",
    version=settings.app_version,
    lifespan=lifespan,
)

# ------------------------------------------------------------------------------
# CORS Middleware
# ------------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ------------------------------------------------------------------------------
# Uniform Exception Handlers
# ------------------------------------------------------------------------------
@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    """Handle domain application exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_dict(),
    )


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    """Format Pydantic schema validation failures into uniform error shape."""
    details = exc.errors()
    first_msg = details[0].get("msg") if details else "Validation error"
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=jsonable_encoder({
            "code": "VALIDATION_ERROR",
            "message": first_msg,
            "details": details,
        }),
    )


# ------------------------------------------------------------------------------
# Health & Metadata Endpoints (Endpoints 1 and 2)
# ------------------------------------------------------------------------------
@app.get("/api/health")
@app.get("/health")
def get_health():
    """
    Health check (Endpoint 1).
    Reports application status, database connectivity, catalogue status, and engine readiness.
    """
    db_ok = is_database_connected()

    cat_stats = None
    cat_ok = False
    try:
        catalog = get_catalog()
        cat_stats = catalog.stats()
        cat_ok = True
    except Exception:
        pass

    engine_adapter = get_engine_adapter()
    engine_available = engine_adapter.is_engine_available()

    overall_status = "healthy" if (db_ok and cat_ok) else "degraded"

    return {
        "status": overall_status,
        "service": "build-my-holiday-api",
        "version": settings.app_version,
        "dependencies": {
            "database": {
                "status": "connected" if db_ok else "disconnected",
            },
            "catalogue": {
                "status": "available" if cat_ok else "unavailable",
                "record_counts": cat_stats,
            },
            "engine": {
                "status": "connected" if engine_available else "awaiting_integration",
                "provider": "Person A (Khushi)",
            },
        },
    }


@app.get("/api/meta")
def get_metadata():
    """
    Metadata retrieval (Endpoint 2).
    Returns real travel catalogue metadata (departure cities, destination countries, date windows, rules).
    """
    catalog = get_catalog()
    dest = catalog.destinations

    return {
        "departure_cities": dest.get("departure_cities", []),
        "destination_countries": dest.get("countries", []),
        "rules": dest.get("rules", {}),
        "summary": catalog.stats(),
    }


@app.get("/")
def root():
    """Root info endpoint."""
    return {
        "service": "Build My Holiday API",
        "version": settings.app_version,
        "docs_url": "/docs",
    }


# ------------------------------------------------------------------------------
# Mount Routers
# ------------------------------------------------------------------------------
app.include_router(catalog_router)
app.include_router(packages_router)
app.include_router(changes_router)
app.include_router(reservations_router)
app.include_router(export_router)
app.include_router(parser_router)

# ------------------------------------------------------------------------------
# Mount Static Images
# ------------------------------------------------------------------------------
images_dir = settings.data_dir / "images"
if not images_dir.is_dir():
    images_dir = settings.data_dir / "data" / "images"

if images_dir.is_dir():
    app.mount("/images", StaticFiles(directory=str(images_dir)), name="images")
