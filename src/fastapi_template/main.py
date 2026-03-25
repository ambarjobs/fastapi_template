from typing import Annotated

from fastapi import Depends, FastAPI, Request, Response, status
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.orm import Session

import fastapi_template.config as cfg
from fastapi_template import HealthStatus, LoginStatus, RequesterStatus, TokenStatus, UserRole, get_logger
from fastapi_template.adapters import handle_token, oauth2form_to_credentials
from fastapi_template.core import get_login_status, get_requester_status, get_token, oauth2_scheme
from fastapi_template.database import create_all_tables, create_app_admin_user, engine, fill_roles, get_user_by_email
from fastapi_template.database import create_user as create_db_user
from fastapi_template.exceptions import DatabaseUserCreationError, InvalidTokenKeyError, UnhealthyDatabaseError
from fastapi_template.models.database import Base, Role
from fastapi_template.models.input import UserInfo
from fastapi_template.models.output import (
    HealthCheck,
    InvalidConfigurationResponse,
    InvalidRequesterResponse,
    InvalidTokenResponse,
    LoginResponse,
    UserCreationErrorResponse,
    UserCreationResponse,
    ValidationErrorModel,
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
    logger.exception(msg="Unhealthy database.", exc_info=exc)
    return JSONResponse(
        content=healthcheck_data,
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
    )


@app.exception_handler(InvalidTokenKeyError)
def invalid_token_key_error_handler(request: Request, exc: InvalidTokenKeyError):
    content = InvalidConfigurationResponse(config_item=exc.config_item, msg=exc.message).model_dump()
    logger.exception(msg="Invalid token key.", exc_info=exc)
    return JSONResponse(
        content=content,
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
    )


@app.exception_handler(DatabaseUserCreationError)
def database_user_creation_error_handler(request: Request, exc: DatabaseUserCreationError):
    content = UserCreationErrorResponse().model_dump()
    logger.exception(msg="Error creating database user.", exc_info=exc)
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
            logger.info("Health check: OK")
            return HealthCheck(**health_check_params)
        raise UnhealthyDatabaseError
    except ValidationError as err:
        logger.exception(msg="Validation error", exc_info=err)
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return ValidationErrorModel(title=err.title, error_count=err.error_count(), errors=err.errors())


@app.post(
    path="/login",
    status_code=status.HTTP_200_OK
)
def login(
    form: Annotated[OAuth2PasswordRequestForm, Depends()],
    response: Response,
) -> LoginResponse | ValidationErrorModel:
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
    response.status_code = status.HTTP_400_BAD_REQUEST
    msg = "Invalid credentials."
    logger.error(msg=msg)
    return LoginResponse(status=LoginStatus.ERROR, error=True, msg=msg)

@app.post(
    path="/create-user",
    status_code=status.HTTP_201_CREATED
)
def create_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    user_info: UserInfo,
    response: Response,
) -> UserCreationResponse | InvalidRequesterResponse | InvalidTokenResponse:
    token_info = handle_token(token=token)
    if token_info.status != TokenStatus.OK:
        response.status_code = status.HTTP_400_BAD_REQUEST
        logger.error(msg=token_info.description)
        return InvalidTokenResponse.from_token_info(token_info=token_info)
    requester_email = token_info.payload.get("sub")
    requester_status = get_requester_status(
        engine=engine,
        requester_email=requester_email,
        required_roles=[UserRole.ADMIN]
    )
    if requester_status == RequesterStatus.NOT_FOUND:
        response.status_code = status.HTTP_400_BAD_REQUEST
        logger.error(msg=f"The requester user {requester_email} does not exists on database.")
        return InvalidRequesterResponse.from_requester_status(requester_status=requester_status)
    if requester_status == RequesterStatus.UNAUTHORIZED:
        response.status_code = status.HTTP_401_UNAUTHORIZED
        logger.error(msg=f"Requester user {requester_email} does not have permission to create another user.")
        return InvalidRequesterResponse.from_requester_status(requester_status=requester_status)
    create_db_user(
        engine=engine,
        user_full_name=user_info.full_name,
        credentials=user_info.credentials,
        roles=user_info.roles
    )
    created_user = get_user_by_email(engine=engine, email=user_info.credentials.email)
    if not created_user:
        raise DatabaseUserCreationError
    logger.info(msg=f"User {created_user.email} created with success.")
    return UserCreationResponse(user_id=created_user.id, user_email=created_user.email)
