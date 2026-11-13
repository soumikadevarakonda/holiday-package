"""FastAPI app: CORS, error handlers, routers, /images, startup (schema + catalog seed).

Run from backend/:  uvicorn app.main:app --reload --port 8000
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from app.catalog.router import router as catalog_router
from app.catalog.seed import seed_catalog
from app.catalog.store import get_store
from app.changes.router import router as changes_router
from app.core.config import get_settings
from app.core.database import db_ping, get_engine
from app.core.errors import register_error_handlers
from app.core.migrate import apply_schema
from app.export.router import router as export_router
from app.packages.router import router as packages_router
from app.parser.router import router as parser_router
from app.reservations.router import router as reservations_router

log = logging.getLogger("app")


def init_database(app: FastAPI) -> None:
    """Create tables and seed the catalog. Never crashes startup: /api/health reports the problem."""
    app.state.db_init_error = None
    if not get_settings().DB_AUTO_INIT:
        return
    if not db_ping():
        app.state.db_init_error = "Cannot connect to MySQL. Check DB_URL in .env and that MySQL is running."
        log.warning(app.state.db_init_error)
        return
    try:
        apply_schema()
        seed_catalog()
    except Exception as exc:  # noqa: BLE001 - reported through /api/health
        app.state.db_init_error = f"{type(exc).__name__}: {exc}"
        log.exception("Database init failed")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.basicConfig(level=logging.INFO)
    init_database(app)
    # M-1 (Person A): load the catalog from MySQL into get_store() here.
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="Build My Holiday API", version="0.1.0", lifespan=lifespan)

    app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins, allow_credentials=True,
                       allow_methods=["*"], allow_headers=["*"])
    register_error_handlers(app)

    for router in (catalog_router, packages_router, changes_router, export_router,
                   reservations_router, parser_router):
        app.include_router(router)

    @app.get("/", include_in_schema=False)
    def root() -> RedirectResponse:
        return RedirectResponse(url="/docs")

    @app.get("/api/health", tags=["health"])
    def health() -> dict:
        db_ok = db_ping()
        seeded = False
        if db_ok:
            try:
                with get_engine().connect() as conn:
                    seeded = (conn.execute(text("SELECT COUNT(*) FROM flight")).scalar() or 0) > 0
            except Exception:  # noqa: BLE001 - tables not created yet
                seeded = False
        return {
            "status": "ok" if db_ok and seeded else "degraded",
            "db": db_ok,
            "catalog_seeded": seeded,
            "catalog_loaded": get_store().loaded,
            "db_init_error": getattr(app.state, "db_init_error", None),
        }

    # Photos + ATTRIBUTIONS.md: hotel / attraction `image` "images/x.jpg" -> URL "/images/x.jpg"
    if settings.images_dir.is_dir():
        app.mount("/images", StaticFiles(directory=settings.images_dir), name="images")

    return app


app = create_app()
