from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import ExpiredSignatureError, JWTError
from pydantic import SecretStr

import fastapi_template.config as cfg
from fastapi_template import TokenStatus
from fastapi_template.logic import get_token_payload
from fastapi_template.models.input import UserCredentials
from fastapi_template.models.internal import TokenInfo


def oauth2form_to_credentials(form_data: OAuth2PasswordRequestForm) -> UserCredentials:
    """Produce an UserCredentials object corresponding to the OAuth2 request form."""

    return UserCredentials(email=form_data.username, password=SecretStr(form_data.password))


def handle_token(token:OAuth2PasswordBearer) -> TokenInfo:
    key = cfg.TOKEN_SECRET_KEY
    try:
        payload = get_token_payload(token=token, key=key)
    except ExpiredSignatureError as err:
        return TokenInfo(payload={}, status=TokenStatus.EXPIRED, description=f"Expired token: {err}")
    except (JWTError, AttributeError) as err:
        return TokenInfo(payload={}, status=TokenStatus.INVALID, description=f"Invalid token: {err}")
    return TokenInfo(payload=payload, status=TokenStatus.OK, description="Valid token.")
