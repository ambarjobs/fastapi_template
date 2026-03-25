import pytest  # noqa: F401
from sqlalchemy import Engine

from fastapi_template import LoginStatus
from fastapi_template.core import get_login_status
from fastapi_template.models.input import UserCredentials


class TestAuthentication:
    def test_get_login_status__common_case(
        self,
        test_engine: Engine,
        database_with_user: None,
        user_credentials: UserCredentials
    ) -> None:
        login_status = get_login_status(engine=test_engine, credentials=user_credentials)

        assert login_status == LoginStatus.SUCCESS

    def test_get_login_status__non_existing_user(
        self,
        test_engine: Engine,
        database_with_user: None,
        user_credentials: UserCredentials
    ) -> None:
        non_existing_user_credentials = UserCredentials(
            email="non.existing.user@test.xyz",
            password=user_credentials.password
        )
        login_status = get_login_status(engine=test_engine, credentials=non_existing_user_credentials)

        assert login_status == LoginStatus.USER_NOT_FOUND

    def test_get_login_status__invalid_password(
        self,
        test_engine: Engine,
        database_with_user: None,
        user_credentials: UserCredentials
    ) -> None:
        invalid_password_credentials = UserCredentials(email=user_credentials.email, password="invalid_password")
        login_status = get_login_status(engine=test_engine, credentials=invalid_password_credentials)

        assert login_status == LoginStatus.WRONG_CREDENTIALS
