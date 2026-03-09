from pydantic import BaseModel, EmailStr, Field, SecretStr

import fastapi_template.config as cfg


class UserCredentials(BaseModel):
    """User credentials (used for login and user creation)."""

    email: EmailStr
    password: SecretStr = Field(min_length=cfg.PASSWORD_MIN_LENGTH, max_length=cfg.PASSWORD_MAX_LENGTH)
