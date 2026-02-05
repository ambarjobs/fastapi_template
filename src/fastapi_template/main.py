from fastapi import FastAPI, status
from pydantic import ValidationError

from .models.output import HealthCheck, HealthStatus

app = FastAPI()


@app.get(
    "/health-check",
    response_model_exclude_unset=True,
    status_code=status.HTTP_200_OK,
)
def health_check() -> HealthCheck:
    "Simple health check endpoint."

    try:
        return HealthCheck(status=HealthStatus.OK)
        # return HealthCheck(status=HealthStatus.OK, spurious=123)
        # return HealthCheck(status=123)
    except ValidationError as e:
        return HealthCheck(status=HealthStatus.ERROR, msg=str(e))
