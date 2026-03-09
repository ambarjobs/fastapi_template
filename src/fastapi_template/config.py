import logging
from os import getenv

from pydantic import SecretStr

# ------------------------------------------------------------------------------
#   Environment variables.
# ------------------------------------------------------------------------------
APP_DATABASE = getenv(key="APP_DATABASE", default="")
APP_ADMIN_USER = getenv(key="APP_ADMIN_USER", default="")
APP_ADMIN_PASSWORD = SecretStr(getenv(key="APP_ADMIN_PASSWORD", default=""))

TEST_DATABASE = getenv(key="TEST_POSTGRES_DB", default="")
TEST_DATABASE_PORT = getenv(key="TEST_PGPORT", default=5433)

# ------------------------------------------------------------------------------
#   Application admin user.
# ------------------------------------------------------------------------------
APP_ADMIN_FAKE_EMAIL = "fake.email@fastapi-template.xyz"
APP_ADMIN_FAKE_NAME = "App Admin"

# ------------------------------------------------------------------------------
#   General application values.
# ------------------------------------------------------------------------------
APP_ENCODING = "utf-8"

# TODO: Change to logging.INFO on production.
LOGGING_LEVEL = logging.DEBUG
LOGGING_CONFIG_PARAMS = {
    "format": "%(levelname)s:\t [%(name)s] %(message)s",
    "style":"%",
    "level": LOGGING_LEVEL
}

# ------------------------------------------------------------------------------
#   Authentication.
# ------------------------------------------------------------------------------
HASH_SALT_LENGTH = 32

PASSWORD_MIN_LENGTH = 8
PASSWORD_MAX_LENGTH = 64

TOKEN_EXPIRATION_IN_HOURS = 2.0
TOKEN_SECRET_KEY = getenv(key="TOKEN_SECRET_KEY")
TOKEN_ALGORITHM = "HS256"
