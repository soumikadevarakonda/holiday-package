"""PHASE 0 STUB DATA. Delete this file once every engine stub is replaced (milestone M-3/M-4).

The engine stubs (build, rebuild, validate, options, apply_change) return the hand-checked Menon
package in backend/tests/fixtures/menon_package.json, so the API can be built and tested before the
real engine exists.
"""

import copy
import json
from functools import lru_cache
from pathlib import Path

from app.core.package_model import Package

FIXTURE = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "menon_package.json"


@lru_cache
def _fixture_json() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def menon_package() -> Package:
    """A fresh copy every call, so callers can mutate it."""
    return Package.from_trip_format(copy.deepcopy(_fixture_json()))
