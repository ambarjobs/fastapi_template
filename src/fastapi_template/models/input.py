from pydantic import BaseModel, EmailStr, Field, SecretStr

import fastapi_template.config as cfg
from fastapi_template import UserRole


class UserCredentials(BaseModel):
    """User credentials (used for login and user creation)."""

    email: EmailStr
    password: SecretStr = Field(min_length=cfg.PASSWORD_MIN_LENGTH, max_length=cfg.PASSWORD_MAX_LENGTH)


class Address(BaseModel):
    """General address."""

    street: str = Field(max_length=255)
    district: str | None = Field(max_length=255, default=None)
    city: str = Field(max_length=255)
    state: str = Field(max_length=2)
    country: str = Field(max_length=2)
    zip_code: str = Field(max_length=9)


class UserInfo(BaseModel):
    """Information about the user."""

    credentials: UserCredentials
    full_name: str = Field(max_length=255)
    address: Address | None = None
    roles: list[UserRole] = Field(default_factory=list)
