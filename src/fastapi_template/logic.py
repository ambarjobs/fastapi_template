from datetime import datetime, timedelta, UTC
from hashlib import scrypt
from os import urandom

from jose import jwt
from pydantic import SecretStr

import fastapi_template.config as cfg
from fastapi_template.exceptions import InvalidTokenKeyError
from fastapi_template.models.input import UserCredentials


HASH_CPU_MEMORY_COST = 2 ** 14
HASH_BLOCK_SIZE = 8
HASH_PARALLELIZATION = 1


def calc_password_hash(password: SecretStr) -> str:
    """Calculate a salted hash for a password."""

    salt = urandom(cfg.HASH_SALT_LENGTH)
    encoded_password = password.get_secret_value().encode(encoding=cfg.APP_ENCODING)
    key = scrypt(
        password=encoded_password,
        salt=salt,
        n=HASH_CPU_MEMORY_COST,
        r=HASH_BLOCK_SIZE,
        p=HASH_PARALLELIZATION
    )
    return (salt + key).hex()


def check_password(password: SecretStr, password_hash: str) -> bool:
    """Check if a password correspond to stored password hash."""

    encoded_password = password.get_secret_value().encode(encoding=cfg.APP_ENCODING)
    bytes_hash = bytearray.fromhex(password_hash)
    salt = bytes_hash[:cfg.HASH_SALT_LENGTH]
    stored_key = bytes_hash[cfg.HASH_SALT_LENGTH:]

    password_key = scrypt(
        password=encoded_password,
        salt=salt,
        n=HASH_CPU_MEMORY_COST,
        r=HASH_BLOCK_SIZE,
        p=HASH_PARALLELIZATION
    )

    return password_key == stored_key


def create_token(
    credentials: UserCredentials,
    key: str = cfg.TOKEN_SECRET_KEY,
    expiration_in_hours: float = float(cfg.TOKEN_EXPIRATION_IN_HOURS)
    ) -> str:
    """Return an OAuth2 token with determined expiration."""

    this_moment = datetime.now(tz=UTC)
    token_expiration = this_moment + timedelta(hours=expiration_in_hours)
    if not key:
        raise InvalidTokenKeyError(config_item="TOKEN_SECRET_KEY")
    return jwt.encode(
        claims={"sub": credentials.email, 'exp': token_expiration},
        key=key,
        algorithm=cfg.TOKEN_ALGORITHM
    )
