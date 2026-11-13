"""POST /api/parse (S1): fill the request form from a sentence. Rules only, no AI."""

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.parser.quick_request import parse_quick_request

router = APIRouter(prefix="/api", tags=["parse"])


class ParseIn(BaseModel):
    text: str = Field(..., min_length=1, max_length=500,
                      examples=["2 adults 1 kid age 6 Bengaluru to Japan 10 Apr 6 nights 3.5 lakh"])


class ParseOut(BaseModel):
    request: dict = Field(description="Partly filled request: only the fields that were found")
    unparsed: list[str] = Field(description="Words that were not understood")
    warnings: list[str]


@router.post("/parse", response_model=ParseOut)
def parse(body: ParseIn) -> ParseOut:
    res = parse_quick_request(body.text)
    return ParseOut(request=res.request, unparsed=res.unparsed, warnings=res.warnings)
