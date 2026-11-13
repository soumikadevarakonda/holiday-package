"""HTTP routes for the changes module. Endpoints are listed in Project.md, section 4.

Phase 0: the router exists and is mounted in main.py; add endpoints here.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/api", tags=["changes"])
