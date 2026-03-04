from fastapi import FastAPI, Request, Response, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

from fastapi_template import get_logger, HealthStatus, UserRole
from fastapi_template.database import create_app_admin_user, create_all_tables, engine, fill_roles
from fastapi_template.exceptions import UnhealthyDatabaseError
from fastapi_template.models.database import Base, Role
from fastapi_template.models.output import HealthCheck, ValidationErrorModel

logger = get_logger(module_name=__name__)

app = FastAPI()

# ------------------------------------------------------------------------------
#   Database initialization.
# ------------------------------------------------------------------------------
create_all_tables(engine=engine, declarative_base=Base)
fill_roles(engine=engine)
create_app_admin_user(engine=engine)
# ------------------------------------------------------------------------------

# To facilitate mocking in tests.
health_check_params = {"status": HealthStatus.OK}


@app.exception_handler(UnhealthyDatabaseError)
def unhealthy_database_error_handler(request: Request, exc: UnhealthyDatabaseError):
    healthcheck_data = HealthCheck(status=exc.status, msg=exc.message).model_dump()
    return JSONResponse(
        content=healthcheck_data,
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
    )


@app.get(
    "/health-check",
    response_model_exclude_unset=True,
    status_code=status.HTTP_200_OK,
)
def health_check(response: Response) -> HealthCheck | ValidationErrorModel:
    "Simple health check endpoint."

    with Session(engine) as session:
        database_roles = session.scalars(select(Role.name).order_by(Role.name)).all()
        available_roles = sorted(UserRole.get_roles())
    try:
        if database_roles == available_roles:
            logger.warning("Health check: OK")
            return HealthCheck(**health_check_params)
        raise UnhealthyDatabaseError
    except ValidationError as e:
        logger.exception(msg="Validation error", exc_info=e)
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return ValidationErrorModel(title=e.title, error_count=e.error_count(), errors=e.errors())
