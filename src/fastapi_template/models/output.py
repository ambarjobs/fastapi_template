from typing import Any

from pydantic import BaseModel, ConfigDict

from fastapi_template import HealthStatus


class ErrorDetails(BaseModel):
    "Error details from pydantic.ValidationErrors."

    type: str
    loc: tuple[int | str, ...]
    msg: str
    input: Any
    url: str


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
