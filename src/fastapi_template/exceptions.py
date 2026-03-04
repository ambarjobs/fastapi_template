from fastapi_template import HealthStatus


class UnhealthyDatabaseError(Exception):
    """Error trying to access database."""

    def __init__(self, status=HealthStatus.ERROR, message="Application cannot access database.") -> None:
        self.status = status
        self.message = message
        super().__init__(self.message)
