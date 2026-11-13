"""
Parser router: natural-language quick request parser (Feature S1).
"""

from __future__ import annotations

from fastapi import APIRouter

from backend.app.packages.schemas import QuickRequestInput, QuickRequestResponse
from backend.app.parser.quick_request import parse_quick_request

router = APIRouter(prefix="/api", tags=["Quick Request Parser"])


@router.post("/parse", response_model=QuickRequestResponse)
def parse_request(payload: QuickRequestInput):
    """
    Parse a plain-text holiday request string into structured form fields
    using deterministic rules (Feature S1).
    """
    result = parse_quick_request(payload.text)
    return result
