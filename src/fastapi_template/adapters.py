from fastapi.security import OAuth2PasswordRequestForm
from pydantic import SecretStr

from fastapi_template.models.input import UserCredentials


def oauth2form_to_credentials(form_data: OAuth2PasswordRequestForm) -> UserCredentials:
    """Produce an UserCredentials object corresponding to the OAuth2 request form."""

    return UserCredentials(email=form_data.username, password=SecretStr(form_data.password))
