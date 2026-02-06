from fastapi import FastAPI, Response, status
from pydantic import ValidationError

from .models.output import HealthCheck, HealthStatus, ValidationErrorModel

app = FastAPI()


@app.get(
    "/health-check",
    response_model_exclude_unset=True,
    status_code=status.HTTP_200_OK,
)
def health_check(response: Response) -> HealthCheck | ValidationErrorModel:
    "Simple health check endpoint."

    try:
        return HealthCheck(status=HealthStatus.OK)
        # return HealthCheck(status=HealthStatus.OK, spurious=123)
        # return HealthCheck(status=123)
    except ValidationError as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return ValidationErrorModel(title=e.title, error_count=e.error_count(), errors=e.errors())
