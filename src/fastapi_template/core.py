from typing import Sequence

from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import Engine
from sqlalchemy.orm import Session

from fastapi_template import LoginStatus, RequesterStatus, UserRole
from fastapi_template.database import get_user_by_credentials, get_user_by_email
from fastapi_template.logic import check_password, create_token
from fastapi_template.models.input import UserCredentials

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def get_login_status(engine: Engine, credentials: UserCredentials) -> LoginStatus:
    """Return the login status corresponding to user credentials."""

    user = get_user_by_credentials(engine=engine, credentials=credentials)
    if not user:
        return LoginStatus.USER_NOT_FOUND
    if not check_password(password=credentials.password, password_hash=user.password_hash):
        return LoginStatus.WRONG_CREDENTIALS
    return LoginStatus.SUCCESS


def get_token(credentials: UserCredentials) -> str:
    """Get a token with expiration for the user email given on credentials."""

    return create_token(credentials=credentials)


def get_requester_status(engine: Engine, requester_email: str, required_roles: Sequence[UserRole]) -> RequesterStatus:
    """Return the status of an endpoint requester."""
    with Session(engine) as session:
        requester = get_user_by_email(engine=engine, email=requester_email, session_=session)
        if not requester:
            return RequesterStatus.NOT_FOUND
        requester_roles = [role.name for role in requester.roles]
        attended_roles = [role in requester_roles for role in required_roles]
        if not all(attended_roles):
            return RequesterStatus.UNAUTHORIZED
    return RequesterStatus.VALID
