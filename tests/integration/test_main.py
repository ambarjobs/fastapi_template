from datetime import datetime

import pytest  # noqa: F401
from fastapi import status
from fastapi.testclient import TestClient
from freezegun import freeze_time
from pytest import MonkeyPatch
from sqlalchemy import Engine

import fastapi_template.config as cfg
import fastapi_template.main as main_module
from fastapi_template import HealthStatus, LoginStatus
from fastapi_template.exceptions import UnhealthyDatabaseError
from fastapi_template.main import app
from fastapi_template.models.database import User
from fastapi_template.models.input import UserCredentials
from fastapi_template.models.output import LoginResponse, ValidationErrorModel

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
        database_user: None,
        frozen_time: datetime,
        monkeypatch: MonkeyPatch,
    ) -> None:
        form = {"username": user_credentials.email, "password": user_credentials.password.get_secret_value()}

        monkeypatch.setattr(main_module, "engine", test_engine)
        with freeze_time(time_to_freeze=frozen_time):
            response = client.post(url="/login", data=form)
        login_response = LoginResponse(**response.json())

        assert response.status_code == status.HTTP_200_OK

        assert login_response.status == LoginStatus.SUCCESS.value
        assert not login_response.error
        assert login_response.msg == f"Token expires in {cfg.TOKEN_EXPIRATION_IN_HOURS} hours."
        # spell-checker: disable
        assert login_response.token == (
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0X3VzZXJAZmFrZS5kb21haW4"
            "ueHl6IiwiZXhwIjoxNzczMDAzNTA2fQ.NZ_u_fKJYEyRsBeF-1i8jqlZYJy3Vuzp5gmteFNbnTo"
        )
        # spell-checker: enable

    def test_login__invalid_email(
        self,
        test_engine: Engine,
        user_credentials: UserCredentials,
        database_user: User,
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
        database_user: User,
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
        assert login_response.token is None

    def test_login__wrong_password(
        self,
        test_engine: Engine,
        user_credentials: UserCredentials,
        database_user: User,
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
        assert login_response.token is None
