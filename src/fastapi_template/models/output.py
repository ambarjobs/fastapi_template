from typing import Any, NotRequired, TypedDict

from pydantic import BaseModel, ConfigDict, EmailStr

from fastapi_template import HealthStatus, LoginStatus, RequesterStatus, TokenStatus
from fastapi_template.models.internal import TokenInfo


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
    msg: str = ""


class LoginResponse(BaseModel):
    """Login response model (including OAuth2 token)."""

    status: LoginStatus
    error: bool = False
    msg: str = ""
    token: str = ""


class InvalidConfigurationResponse(BaseModel):
    """Response for invalid configurations."""

    status: str = "INVALID CONFIGURATION"
    config_item: str
    msg: str


class InvalidTokenResponse(BaseModel):
    "Response for invalid or expired token."

    status: TokenStatus
    msg: str

    @classmethod
    def from_token_info(cls, token_info: TokenInfo):
        """Return an InvalidTokenResponse based on a TokenInfo."""

        return cls(status=token_info.status, msg=token_info.description)


class UserCreationResponse(BaseModel):
    """Response for database user creation."""

    user_id: int
    user_email: EmailStr


class UserCreationErrorResponse(BaseModel):
    """Response for error on database user creation."""

    status: str = "ERROR"
    msg: str = "Error trying to create a database user."


class InvalidRequesterResponse(BaseModel):
    """Response for when the requester was not found or don't have permissions for the request."""

    status: RequesterStatus
    msg: str = "Request could not be attended."

    @classmethod
    def from_requester_status(cls, requester_status: RequesterStatus):
        """Return an InvalidRequesterResponse based on status of requester."""

        match requester_status:
            case RequesterStatus.NOT_FOUND:
                msg = "Request could not be attended because requester user was not found on database."
            case RequesterStatus.UNAUTHORIZED:
                msg = "Request could not be attended because requester user don't have permission to do the operation."
        return cls(status=requester_status, msg=msg)
