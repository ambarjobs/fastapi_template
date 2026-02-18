from hashlib import scrypt
from os import urandom

from pydantic import SecretStr

import fastapi_template.config as cfg


HASH_CPU_MEMORY_COST = 2 ** 14
HASH_BLOCK_SIZE = 8
HASH_PARALLELIZATION = 1


def calc_password_hash(password: SecretStr) -> str:
    """Calculate a salted hash for a password."""

    salt = urandom(cfg.PASSWORD_SALT_LENGTH)
    encoded_password = password.get_secret_value().encode(encoding=cfg.APP_ENCODING)
    key = scrypt(
        password=encoded_password,
        salt=salt,
        n=HASH_CPU_MEMORY_COST,
        r=HASH_BLOCK_SIZE,
        p=HASH_PARALLELIZATION
    )
    return (salt + key).hex()


def check_password(password: SecretStr, stored_hash: str) -> bool:
    """Check if a password correspond to stored hash."""

    encoded_password = password.get_secret_value().encode(encoding=cfg.APP_ENCODING)
    bytes_hash = bytearray.fromhex(stored_hash)
    salt = bytes_hash[:cfg.PASSWORD_SALT_LENGTH]
    stored_key = bytes_hash[cfg.PASSWORD_SALT_LENGTH:]

    password_key = scrypt(
        password=encoded_password,
        salt=salt,
        n=HASH_CPU_MEMORY_COST,
        r=HASH_BLOCK_SIZE,
        p=HASH_PARALLELIZATION
    )

    return password_key == stored_key
