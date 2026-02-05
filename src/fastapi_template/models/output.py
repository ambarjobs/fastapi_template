from enum import StrEnum

from pydantic import BaseModel, ConfigDict


class HealthStatus(StrEnum):
    OK = "ok"
    ERROR = "error"


class HealthCheck(BaseModel):
    "Health check endpoint output model."

    model_config = ConfigDict(strict=True, extra="forbid")

    status: HealthStatus
    msg: str | None = ""
