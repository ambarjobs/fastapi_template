import logging
from logging import Logger
from enum import StrEnum

import fastapi_template.config as cfg


logging.basicConfig(**cfg.LOGGING_CONFIG_PARAMS)

def get_logger(module_name: str) -> Logger:
    """Get a logger instance for a determined module."""

    return logging.getLogger(name=module_name)


class HealthStatus(StrEnum):
    OK = "OK"
    ERROR = "ERROR"


class UserRole(StrEnum):
    """Application valid user roles."""

    GUEST = 'guest'
    USER = 'user'
    ADMIN = 'admin'

    @classmethod
    def get_roles(cls) -> list[str]:
        "Get a list of all roles available."

        return [element.value for element in cls]
