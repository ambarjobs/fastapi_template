from fastapi import FastAPI, Response, status
from pydantic import ValidationError

from fastapi_template.models.output import HealthCheck, HealthStatus, ValidationErrorModel

app = FastAPI()

# To facilitate mocking in tests.
health_check_params = {"status": HealthStatus.OK}

@app.get(
    "/health-check",
    response_model_exclude_unset=True,
    status_code=status.HTTP_200_OK,
)
def health_check(response: Response) -> HealthCheck | ValidationErrorModel:
    "Simple health check endpoint."

    try:
        return HealthCheck(**health_check_params)
    except ValidationError as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return ValidationErrorModel(title=e.title, error_count=e.error_count(), errors=e.errors())
