import logging
from os import getenv

from pydantic import SecretStr

# ------------------------------------------------------------------------------
#   Environment variables.
# ------------------------------------------------------------------------------
APP_DATABASE = getenv(key="APP_DATABASE", default="")
APP_ADMIN_USER = getenv(key="APP_ADMIN_USER", default="")
APP_ADMIN_PASSWORD = SecretStr(getenv(key="APP_ADMIN_PASSWORD", default=""))

# ------------------------------------------------------------------------------
#   Application admin user.
# ------------------------------------------------------------------------------
APP_ADMIN_FAKE_EMAIL = "fake.email@fastapi_template.xyz"
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

PASSWORD_SALT_LENGTH = 32
