import logging
from os import getenv

APP_DATABASE = getenv(key="APP_DATABASE", default="")
APP_ADMIN_USER = getenv(key="APP_ADMIN_USER", default="")
APP_ADMIN_PASSWORD = getenv(key="APP_ADMIN_PASSWORD", default="")

APP_ADMIN_FAKE_EMAIL = "fake.email@fastapi_template.xyz"
APP_ADMIN_FAKE_NAME = "App Admin"

# TODO: Change to logging.INFO on production.
LOGGING_LEVEL = logging.DEBUG
LOGGING_CONFIG_PARAMS = {
    "format": "%(levelname)s:\t [%(name)s] %(message)s",
    "style":"%",
    "level": LOGGING_LEVEL
}
