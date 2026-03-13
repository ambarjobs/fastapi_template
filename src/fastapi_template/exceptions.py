from fastapi_template import HealthStatus


class UnhealthyDatabaseError(Exception):
    """Error trying to access database."""

    def __init__(self, status=HealthStatus.ERROR, message="Application cannot access database.") -> None:
        self.status = status
        self.message = message
        super().__init__(self.message)


class InvalidTokenKeyError(Exception):
    """Invalid or non-existing token key from config."""

    def __init__(
        self,
        config_item=None,
        message="Invalid or non-existing token key coming from configuration."
    ) -> None:
        self.config_item=config_item
        self.message = message
        super().__init__(self.message)


class DatabaseUserCreationError(Exception):
    """Error trying to create an user on the database."""

    def __init__(self, message="Error trying to create an user on the database.") -> None:
        self.message = message
        super().__init__(self.message)
