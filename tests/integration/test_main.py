from datetime import datetime, timedelta, timezone
from unittest import mock

import jwt
import pytest  # noqa: F401
from fastapi import status
from fastapi.testclient import TestClient
from freezegun import freeze_time
from pydantic import SecretStr
from pytest import MonkeyPatch
from sqlalchemy import Engine

import fastapi_template.config as cfg
import fastapi_template.main as main_module
from fastapi_template import HealthStatus, LoginStatus, RequesterStatus, TokenStatus, UserRole
from fastapi_template.database import Session, get_user_by_credentials
from fastapi_template.exceptions import UnhealthyDatabaseError
from fastapi_template.logic import create_token
from fastapi_template.main import app
from fastapi_template.models.input import UserCredentials, UserInfo
from fastapi_template.models.output import (
    InvalidRequesterResponse,
    InvalidTokenResponse,
    LoginResponse,
    UserCreationErrorResponse,
    UserCreationResponse,
    ValidationErrorModel,
)
from tests.utils import get_user_by_email_closure

client = TestClient(app=app)


class TestHealthCheck:
    def test_health_check_endpoint__general_case(
        self,
        test_engine: Engine,
        basic_tables: None,
        monkeypatch: MonkeyPatch
    ) -> None:
        expected_response = {"status": HealthStatus.OK}

        monkeypatch.setattr(main_module, "engine", test_engine)
        response = client.get(url="/health-check")

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == expected_response

    def test_health_check_endpoint__invalid_output_field(
        self,
        test_engine: Engine,
        basic_tables: None,
        monkeypatch: MonkeyPatch
    ) -> None:
        invalid_status_field = 123
        expected_response = {
            "error_count": 1,
            "errors": [
                {
                    "input": invalid_status_field,
                    "loc": ["status"],
                    "msg": "Input should be an instance of HealthStatus",
                    "type": "is_instance_of",
                    "url": "https://errors.pydantic.dev/2.12/v/is_instance_of"
                }
            ],
            "title": "HealthCheck"
        }

        monkeypatch.setattr(main_module, "engine", test_engine)
        monkeypatch.setattr(main_module, "health_check_params", {"status": invalid_status_field})
        response = client.get(url="/health-check")


        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response.json() == expected_response

    def test_health_check_endpoint__additional_output_field(
        self,
        test_engine: Engine,
        basic_tables: None,
        monkeypatch: MonkeyPatch
    ) -> None:
        additional_field = "Not existing on the output model"
        expected_response = {
            "error_count": 1,
            "errors": [
                {
                    "input": additional_field,
                    "loc": [
                        "additional_field"
                    ],
                    "msg": "Extra inputs are not permitted",
                    "type": "extra_forbidden",
                    "url": "https://errors.pydantic.dev/2.12/v/extra_forbidden"
                }
            ],
            "title": "HealthCheck"
        }

        monkeypatch.setattr(main_module, "engine", test_engine)
        monkeypatch.setattr(
            main_module,
            "health_check_params",
            {"status": HealthStatus.OK, "additional_field": additional_field}
        )
        response = client.get(url="/health-check")

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response.json() == expected_response

    def test_health_check_endpoint__unhealthy_database(
        self,
        test_engine: Engine,
        empty_tables: None,
        monkeypatch: MonkeyPatch
    ) -> None:
        unhealthy_database_error_instance = UnhealthyDatabaseError()
        expected_response = {"status": HealthStatus.ERROR, "msg": unhealthy_database_error_instance.message}

        monkeypatch.setattr(main_module, "engine", test_engine)
        response = client.get(url="/health-check")

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response.json() == expected_response


class TestLogin:
    def test_login__common_case(
        self,
        test_engine: Engine,
        user_credentials: UserCredentials,
        database_with_user: None,
        frozen_time: datetime,
        monkeypatch: MonkeyPatch,
    ) -> None:
        form = {"username": user_credentials.email, "password": user_credentials.password.get_secret_value()}

        monkeypatch.setattr(main_module, "engine", test_engine)
        with freeze_time(time_to_freeze=frozen_time):
            response = client.post(url="/login", data=form)
            login_response = LoginResponse(**response.json())
            token = login_response.token
            payload = jwt.decode(jwt=token, key=cfg.TOKEN_SECRET_KEY, algorithms=cfg.TOKEN_ALGORITHM)

        assert response.status_code == status.HTTP_200_OK

        assert login_response.status == LoginStatus.SUCCESS.value
        assert not login_response.error
        assert login_response.msg == f"Token expires in {cfg.TOKEN_EXPIRATION_IN_HOURS} hours."

        assert isinstance(token, str)
        assert len(token) == 151

        assert payload.get("sub") == user_credentials.email
        assert isinstance(payload.get("exp"), int)

    def test_login__invalid_email(
        self,
        test_engine: Engine,
        user_credentials: UserCredentials,
        database_with_user: None,
        frozen_time: datetime,
        monkeypatch: MonkeyPatch,
    ) -> None:
        form = {"username": "invalid_email", "password": user_credentials.password.get_secret_value()}

        monkeypatch.setattr(main_module, "engine", test_engine)
        with freeze_time(time_to_freeze=frozen_time):
            response = client.post(url="/login", data=form)
        login_response = ValidationErrorModel(**response.json())

        assert response.status_code == status.HTTP_400_BAD_REQUEST

        assert login_response.title == "UserCredentials"
        assert login_response.error_count == 1

        error = login_response.errors[0]
        assert error.get("type") == "value_error"
        assert error.get("loc") == ("email",)
        assert error.get("msg") == "value is not a valid email address: An email address must have an @-sign."
        assert error.get("input") == "invalid_email"

    def test_login__non_existent_user(
        self,
        test_engine: Engine,
        user_credentials: UserCredentials,
        database_with_user: None,
        frozen_time: datetime,
        monkeypatch: MonkeyPatch,
    ) -> None:
        form = {"username": "non.existent.user@domain.xyz", "password": user_credentials.password.get_secret_value()}

        monkeypatch.setattr(main_module, "engine", test_engine)
        with freeze_time(time_to_freeze=frozen_time):
            response = client.post(url="/login", data=form)
        login_response = LoginResponse(**response.json())

        assert response.status_code == status.HTTP_400_BAD_REQUEST

        assert login_response.status == LoginStatus.ERROR.value
        assert login_response.error
        assert login_response.msg == "Invalid credentials."
        assert not login_response.token

    def test_login__wrong_password(
        self,
        test_engine: Engine,
        user_credentials: UserCredentials,
        database_with_user: None,
        frozen_time: datetime,
        monkeypatch: MonkeyPatch,
    ) -> None:
        form = {"username": user_credentials.email, "password": "wrong_password"}

        monkeypatch.setattr(main_module, "engine", test_engine)
        with freeze_time(time_to_freeze=frozen_time):
            response = client.post(url="/login", data=form)
        login_response = LoginResponse(**response.json())

        assert response.status_code == status.HTTP_400_BAD_REQUEST

        assert login_response.status == LoginStatus.ERROR.value
        assert login_response.error
        assert login_response.msg == "Invalid credentials."
        assert not login_response.token


class TestCreateUser:
    def test_create_user__common_case(
        self,
        test_engine: Engine,
        basic_tables: None,
        admin_token: str,
        frozen_time: datetime,
        user_credentials: UserCredentials,
        user_full_name: str,
        monkeypatch: MonkeyPatch,
    ) -> None:
        user_info = UserInfo(credentials=user_credentials, full_name=user_full_name, roles=[UserRole.USER])
        payload = user_info.model_dump()
        if payload and payload.get("credentials", {}).get("password"):
            payload["credentials"] |= {"password": user_info.credentials.password.get_secret_value()}
        monkeypatch.setattr(main_module, "engine", test_engine)

        with freeze_time(time_to_freeze=frozen_time):
            response = client.post(
                url="/create-user",
                json=payload,
                headers={'Authorization': f'Bearer {admin_token}'}
            )

        assert response.status_code == status.HTTP_201_CREATED
        user_creation_response = UserCreationResponse(**response.json())
        assert user_creation_response.user_email == user_info.credentials.email

    def test_create_user__expired_token(
        self,
        test_engine: Engine,
        basic_tables: None,
        admin_credentials: UserCredentials,
        user_credentials: UserCredentials,
        user_full_name: str,
        monkeypatch: MonkeyPatch,
    ) -> None:
        user_info = UserInfo(credentials=user_credentials, full_name=user_full_name, roles=[UserRole.USER])
        payload = user_info.model_dump()
        if payload and payload.get("credentials", {}).get("password"):
            payload["credentials"] |= {"password": user_info.credentials.password.get_secret_value()}
        monkeypatch.setattr(main_module, "engine", test_engine)

        yesterday = datetime.now(tz=timezone.utc) - timedelta(days=1.0)
        with freeze_time(time_to_freeze=yesterday):
            admin_expired_token = create_token(credentials=admin_credentials)

        response = client.post(
            url="/create-user",
            json=payload,
            headers={'Authorization': f'Bearer {admin_expired_token}'}
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        invalid_token_response = InvalidTokenResponse(**response.json())
        assert invalid_token_response.status == TokenStatus.EXPIRED
        assert invalid_token_response.msg == "Expired token: Signature has expired"

    def test_create_user__invalid_token(
        self,
        test_engine: Engine,
        basic_tables: None,
        admin_credentials: UserCredentials,
        user_credentials: UserCredentials,
        user_full_name: str,
        frozen_time: datetime,
        monkeypatch: MonkeyPatch,
    ) -> None:
        invalid_key = "invalid_key__invalid_key__invalid_key__invalid_key"
        user_info = UserInfo(credentials=user_credentials, full_name=user_full_name, roles=[UserRole.USER])
        payload = user_info.model_dump()
        if payload and payload.get("credentials", {}).get("password"):
            payload["credentials"] |= {"password": user_info.credentials.password.get_secret_value()}
        monkeypatch.setattr(main_module, "engine", test_engine)

        with freeze_time(time_to_freeze=frozen_time):
            admin_invalid_token = create_token(credentials=admin_credentials, key=invalid_key)
            response = client.post(
                url="/create-user",
                json=payload,
                headers={'Authorization': f'Bearer {admin_invalid_token}'}
            )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        invalid_token_response = InvalidTokenResponse(**response.json())
        assert invalid_token_response.status == TokenStatus.INVALID
        assert invalid_token_response.msg == "Invalid token: Signature verification failed"

    def test_create_user__requester_not_found(
        self,
        test_engine: Engine,
        basic_tables: None,
        user_credentials: UserCredentials,
        user_full_name: str,
        frozen_time: datetime,
        monkeypatch: MonkeyPatch,
    ) -> None:
        user_info = UserInfo(credentials=user_credentials, full_name=user_full_name, roles=[UserRole.USER])
        payload = user_info.model_dump()
        if payload and payload.get("credentials", {}).get("password"):
            payload["credentials"] |= {"password": user_info.credentials.password.get_secret_value()}
        monkeypatch.setattr(main_module, "engine", test_engine)

        with freeze_time(time_to_freeze=frozen_time):
            unknown_requester_credentials = UserCredentials(
                email="unknown_user@domain.xyz",
                password=SecretStr("something_that_even_wont_be_used")
            )
            unknown_requester_token = create_token(credentials=unknown_requester_credentials)
            response = client.post(
                url="/create-user",
                json=payload,
                headers={'Authorization': f'Bearer {unknown_requester_token}'}
            )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        invalid_requester_response  = InvalidRequesterResponse(**response.json())
        assert invalid_requester_response.status == RequesterStatus.NOT_FOUND
        assert invalid_requester_response.msg == (
            "Request could not be attended because requester user was not found on database."
        )

    def test_create_user__requester_unauthorized(
        self,
        test_engine: Engine,
        basic_tables: None,
        admin_token: str,
        admin_credentials: UserCredentials,
        user_credentials: UserCredentials,
        user_full_name: str,
        frozen_time: datetime,
        monkeypatch: MonkeyPatch,
    ) -> None:
        user_info = UserInfo(credentials=user_credentials, full_name=user_full_name, roles=[UserRole.USER])
        payload = user_info.model_dump()
        if payload and payload.get("credentials", {}).get("password"):
            payload["credentials"] |= {"password": user_info.credentials.password.get_secret_value()}
        with Session(test_engine) as session:
            admin_user = get_user_by_credentials(engine=test_engine, credentials=admin_credentials, session_=session)
            admin_roles = [role for role in admin_user.roles if role.name == UserRole.ADMIN.value]
            if admin_roles:
                admin_user.roles.remove(admin_roles[0])
                session.commit()
        monkeypatch.setattr(main_module, "engine", test_engine)

        with freeze_time(time_to_freeze=frozen_time):
            response = client.post(
                url="/create-user",
                json=payload,
                headers={'Authorization': f'Bearer {admin_token}'}
            )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        invalid_requester_response  = InvalidRequesterResponse(**response.json())
        assert invalid_requester_response.status == RequesterStatus.UNAUTHORIZED
        assert invalid_requester_response.msg == (
            "Request could not be attended because requester user don't have permission to do the operation."
        )


    def test_create_user__user_not_created(
        self,
        test_engine: Engine,
        basic_tables: None,
        admin_token: str,
        frozen_time: datetime,
        user_credentials: UserCredentials,
        user_full_name: str,
        monkeypatch: MonkeyPatch,
    ) -> None:
        user_info = UserInfo(credentials=user_credentials, full_name=user_full_name, roles=[UserRole.USER])
        payload = user_info.model_dump()
        if payload and payload.get("credentials", {}).get("password"):
            payload["credentials"] |= {"password": user_info.credentials.password.get_secret_value()}
        monkeypatch.setattr(main_module, "engine", test_engine)

        with mock.patch("fastapi_template.main.get_user_by_email") as mocked_get_user_by_email:
            mocked_get_user_by_email.side_effect = get_user_by_email_closure(missed_user_email=user_credentials.email)
            with freeze_time(time_to_freeze=frozen_time):
                response = client.post(
                    url="/create-user",
                    json=payload,
                    headers={'Authorization': f'Bearer {admin_token}'}
                )

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        user_creation_response = UserCreationErrorResponse(**response.json())
        assert user_creation_response.status == "ERROR"
        assert user_creation_response.msg == "Error trying to create a database user."

    # admin_user roles: [UserRole.USER, UserRole.ADMIN]
    @pytest.mark.parametrize(
        argnames="required_roles",
        argvalues=[
            [],
            [UserRole.USER],
            [UserRole.ADMIN],
            [UserRole.USER, UserRole.ADMIN]
        ]
    )
    def test_create_user__different_have_required_roles(
        self,
        test_engine: Engine,
        basic_tables: None,
        admin_token: str,
        frozen_time: datetime,
        user_credentials: UserCredentials,
        user_full_name: str,
        required_roles: list[UserRole],
        monkeypatch: MonkeyPatch,
    ) -> None:
        app.dependency_overrides[main_module.get_create_user_required_roles] = (lambda: required_roles)
        user_info = UserInfo(credentials=user_credentials, full_name=user_full_name, roles=[UserRole.USER])
        payload = user_info.model_dump()
        if payload and payload.get("credentials", {}).get("password"):
            payload["credentials"] |= {"password": user_info.credentials.password.get_secret_value()}
        monkeypatch.setattr(main_module, "engine", test_engine)

        with freeze_time(time_to_freeze=frozen_time):
            response = client.post(
                url="/create-user",
                json=payload,
                headers={'Authorization': f'Bearer {admin_token}'}
            )

        assert response.status_code == status.HTTP_201_CREATED
        user_creation_response = UserCreationResponse(**response.json())
        assert user_creation_response.user_email == user_info.credentials.email

    # admin_user roles: [UserRole.USER, UserRole.ADMIN]
    @pytest.mark.parametrize(
        argnames="required_roles",
        argvalues=[
            [UserRole.GUEST],
            [UserRole.GUEST, UserRole.USER],
            [UserRole.GUEST, UserRole.ADMIN],
            [UserRole.GUEST, UserRole.USER, UserRole.ADMIN]
        ]
    )
    def test_create_user__different_dont_have_required_roles(
        self,
        test_engine: Engine,
        basic_tables: None,
        admin_token: str,
        frozen_time: datetime,
        user_credentials: UserCredentials,
        user_full_name: str,
        required_roles: list[UserRole],
        monkeypatch: MonkeyPatch,
    ) -> None:
        app.dependency_overrides[main_module.get_create_user_required_roles] = (lambda: required_roles)
        user_info = UserInfo(credentials=user_credentials, full_name=user_full_name, roles=[UserRole.USER])
        payload = user_info.model_dump()
        if payload and payload.get("credentials", {}).get("password"):
            payload["credentials"] |= {"password": user_info.credentials.password.get_secret_value()}
        monkeypatch.setattr(main_module, "engine", test_engine)

        with freeze_time(time_to_freeze=frozen_time):
            response = client.post(
                url="/create-user",
                json=payload,
                headers={'Authorization': f'Bearer {admin_token}'}
            )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        invalid_requester_response  = InvalidRequesterResponse(**response.json())
        assert invalid_requester_response.status == RequesterStatus.UNAUTHORIZED
        assert invalid_requester_response.msg == (
            "Request could not be attended because requester user don't have permission to do the operation."
        )
