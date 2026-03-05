from typing import Annotated

from fastapi import Depends, FastAPI, Request, Response, status
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

import fastapi_template.config as cfg
from fastapi_template import get_logger, HealthStatus, LoginStatus, UserRole
from fastapi_template.adapters import oauth2form_to_credentials
from fastapi_template.core import get_login_status, get_token
from fastapi_template.database import create_app_admin_user, create_all_tables, engine, fill_roles
from fastapi_template.exceptions import InvalidTokenKeyError, UnhealthyDatabaseError
from fastapi_template.models.database import Base, Role
from fastapi_template.models.output import (
    HealthCheck,
    InvalidConfigurationResponse,
    LoginResponse,
    ValidationErrorModel
)

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

@app.exception_handler(InvalidTokenKeyError)
def invalid_token_key_error_handler(request: Request, exc: InvalidTokenKeyError):
    content = InvalidConfigurationResponse(config_item=exc.config_item, msg=exc.message).model_dump()
    return JSONResponse(
        content=content,
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
    )


@app.get(
    path="/health-check",
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
    except ValidationError as err:
        logger.exception(msg="Validation error", exc_info=err)
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return ValidationErrorModel(title=err.title, error_count=err.error_count(), errors=err.errors())


@app.post(path="/login", status_code=status.HTTP_200_OK)
def login(form: Annotated[OAuth2PasswordRequestForm, Depends()], response: Response) -> LoginResponse:
    """Login endpoint that returns an OAuth2 token."""

    try:
        credentials = oauth2form_to_credentials(form_data=form)
    except ValidationError as err:
        logger.exception(msg="Validation error", exc_info=err)
        response.status_code = status.HTTP_400_BAD_REQUEST
        return ValidationErrorModel(title=err.title, error_count=err.error_count(), errors=err.errors())

    login_status = get_login_status(engine=engine, credentials=credentials)
    if login_status == LoginStatus.SUCCESS:
        token = get_token(credentials=credentials)
        logger.info(
            msg=(
                f"Login for user: {credentials.email} ."
                f" Token generated with {cfg.TOKEN_EXPIRATION_IN_HOURS} hours expiration."
            )
        )
        return LoginResponse(
            status=login_status,
            msg=f"Token expires in {cfg.TOKEN_EXPIRATION_IN_HOURS} hours.",
            token=token
        )
    return LoginResponse(status=LoginStatus.ERROR, error=True, msg="Invalid credentials.")
