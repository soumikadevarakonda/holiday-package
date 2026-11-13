"""
Engine Adapter: Clean architectural boundary between API/persistence layer and Person A's Package Engine.

Connects to Person A's six agreed engine operations (Project.md Section 3):
1. `build(req: TripRequest, mode="default") -> BuildResult`
2. `rebuild(req: TripRequest, city_plan: Any) -> BuildResult`
3. `validate(pkg: Any) -> list[Violation]`
4. `options(pkg: Any, kind: str, **params) -> list[Option]`
5. `apply_change(pkg: Any, change: Any) -> ChangeResult`
6. `get_store() -> CatalogStore`

When Person A delivers the engine, this adapter automatically imports and delegates to the real functions.
When the engine implementation is not yet available, calls raise `EngineUnavailableError` (HTTP 503)
describing the exact operation awaiting engine integration.
For automated testing, mock adapters can be injected via `set_engine_adapter()`.
"""

from __future__ import annotations

import logging
from typing import Any, Protocol

from backend.app.core.errors import EngineUnavailableError

logger = logging.getLogger(__name__)


class EngineProtocol(Protocol):
    """Protocol defining the 6 frozen engine interfaces."""

    def build(self, req: Any, mode: str = "default") -> Any: ...

    def rebuild(self, req: Any, city_plan: Any) -> Any: ...

    def validate(self, pkg: Any) -> list[Any]: ...

    def options(self, pkg: Any, kind: str, **params: Any) -> list[Any]: ...

    def apply_change(self, pkg: Any, change: Any) -> Any: ...

    def get_store(self) -> Any: ...


class RealEngineAdapter:
    """
    Adapter that dynamically attempts to resolve and invoke Person A's real engine modules.
    If the modules are empty or unimported, raises EngineUnavailableError.
    """

    def is_engine_available(self) -> bool:
        """Check whether the real engine implementation is available."""
        try:
            from backend.app.builder import search
            from backend.app.rules import validator

            return hasattr(search, "build") and callable(getattr(search, "build"))
        except Exception:
            return False

    def build(self, req: Any, mode: str = "default") -> Any:
        """Call Person A's builder: search.build(req, mode=mode)."""
        try:
            from backend.app.builder import search

            if hasattr(search, "build") and callable(getattr(search, "build")):
                return search.build(req, mode=mode)
        except Exception as exc:
            logger.debug("Real engine build() invocation failed: %s", exc)

        raise EngineUnavailableError(
            operation="build",
            details={"mode": mode, "destination": getattr(req, "destination_country", None)},
        )

    def rebuild(self, req: Any, city_plan: Any) -> Any:
        """Call Person A's builder: search.rebuild(req, city_plan)."""
        try:
            from backend.app.builder import search

            if hasattr(search, "rebuild") and callable(getattr(search, "rebuild")):
                return search.rebuild(req, city_plan)
        except Exception as exc:
            logger.debug("Real engine rebuild() invocation failed: %s", exc)

        raise EngineUnavailableError(operation="rebuild")

    def validate(self, pkg: Any) -> list[Any]:
        """Call Person A's rule validator: validator.validate(pkg)."""
        try:
            from backend.app.rules import validator

            if hasattr(validator, "validate") and callable(getattr(validator, "validate")):
                return validator.validate(pkg)
        except Exception as exc:
            logger.debug("Real engine validate() invocation failed: %s", exc)

        raise EngineUnavailableError(operation="validate")

    def options(self, pkg: Any, kind: str, **params: Any) -> list[Any]:
        """Call Person A's change options: options.options(pkg, kind, **params)."""
        try:
            from backend.app.changes import options

            if hasattr(options, "options") and callable(getattr(options, "options")):
                return options.options(pkg, kind, **params)
        except Exception as exc:
            logger.debug("Real engine options() invocation failed: %s", exc)

        raise EngineUnavailableError(
            operation=f"options/{kind}",
            details={"kind": kind, "params": params},
        )

    def apply_change(self, pkg: Any, change: Any) -> Any:
        """Call Person A's side-effects handler: side_effects.apply_change(pkg, change)."""
        try:
            from backend.app.changes import side_effects

            if hasattr(side_effects, "apply_change") and callable(getattr(side_effects, "apply_change")):
                return side_effects.apply_change(pkg, change)
        except Exception as exc:
            logger.debug("Real engine apply_change() invocation failed: %s", exc)

        raise EngineUnavailableError(operation="apply_change")

    def get_store(self) -> Any:
        """Call Person A's catalogue store: store.get_store()."""
        try:
            from backend.app.catalog import store

            if hasattr(store, "get_store") and callable(getattr(store, "get_store")):
                return store.get_store()
        except Exception as exc:
            logger.debug("Real engine get_store() invocation failed: %s", exc)

        raise EngineUnavailableError(operation="get_store")


# Global active adapter instance (defaults to RealEngineAdapter)
_ACTIVE_ADAPTER: Any = RealEngineAdapter()


def get_engine_adapter() -> Any:
    """Return currently active engine adapter."""
    return _ACTIVE_ADAPTER


def set_engine_adapter(adapter: Any) -> None:
    """Inject a custom adapter (used for test doubles in automated API tests)."""
    global _ACTIVE_ADAPTER
    _ACTIVE_ADAPTER = adapter


def reset_engine_adapter() -> None:
    """Reset adapter to default RealEngineAdapter."""
    global _ACTIVE_ADAPTER
    _ACTIVE_ADAPTER = RealEngineAdapter()
