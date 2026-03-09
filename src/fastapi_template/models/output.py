from typing import Any, NotRequired, TypedDict

from pydantic import BaseModel, ConfigDict

from fastapi_template import HealthStatus, LoginStatus


class ErrorDetails(TypedDict):
    "Error details from pydantic.ValidationErrors."

    type: str
    loc: tuple[int | str, ...]
    msg: str
    input: Any
    url: NotRequired[str]


class ValidationErrorModel(BaseModel):
    "Model used to handle pydantic.ValidationErrors."

    title: str
    error_count: int
    errors: list[ErrorDetails]


class HealthCheck(BaseModel):
    "Health check endpoint output model."

    model_config = ConfigDict(strict=True, extra="forbid")

    status: HealthStatus
    msg: str | None = ""


class LoginResponse(BaseModel):
    """Login response model (include OAuth2 token)."""

    status: LoginStatus
    error: bool = False
    msg: str | None = None
    token: str | None = None


class InvalidConfigurationResponse(BaseModel):
    """Response for invalid configurations."""

    status: str = "INVALID CONFIGURATION"
    config_item: str
    msg: str


class NameParts(BaseModel):
    """Separated parts of a full name."""

    first: str
    middle: str
    last: str
