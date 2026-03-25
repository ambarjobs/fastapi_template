from typing import Any

from pydantic import BaseModel

from fastapi_template import TokenStatus


class NameParts(BaseModel):
    """Separated parts of a full name."""

    first: str
    middle: str
    last: str


class TokenInfo(BaseModel):
    """Token information after handling it."""

    payload: dict[str, Any]
    status: TokenStatus
    description: str = ""
