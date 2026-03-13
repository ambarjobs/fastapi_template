from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import Engine

from fastapi_template import LoginStatus
from fastapi_template.database import get_user_by_credentials
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
