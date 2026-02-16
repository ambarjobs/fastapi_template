from enum import StrEnum
from os import getenv

APP_DATABASE = getenv(key="APP_DATABASE", default="")
APP_ADMIN_USER = getenv(key="APP_ADMIN_USER", default="")
APP_ADMIN_PASSWORD = getenv(key="APP_ADMIN_PASSWORD", default="")


class AppRole(StrEnum):
    GUEST = 'guest'
    USER = 'user'
    ADMIN = 'admin'

    @classmethod
    def get_roles(cls) -> list[str]:
        "Get a list of all roles available."

        return [element.value for element in cls]
