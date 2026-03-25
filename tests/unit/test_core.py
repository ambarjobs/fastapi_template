import pytest  # noqa: F401
from sqlalchemy import Engine
from sqlalchemy.orm import Session

from fastapi_template import LoginStatus, RequesterStatus, UserRole
from fastapi_template.core import get_login_status, get_requester_status
from fastapi_template.database import create_user
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

    def test_requester_status__required_roles_is_subset(
        self,
        test_engine: Engine,
        basic_tables: None,
        admin_email: str,
    ) -> None:
        # The roles of admin user (the requester) are [UserRole.USER, UserRole.ADMIN]
        required_roles = [UserRole.ADMIN]

        requester_status = get_requester_status(
            engine=test_engine,
            requester_email=admin_email,
            required_roles=required_roles
        )

        assert requester_status == RequesterStatus.VALID

    def test_requester_status__required_roles_is_the_same(
        self,
        test_engine: Engine,
        basic_tables: None,
        admin_email: str,
    ) -> None:
        # The roles of admin user (the requester) are [UserRole.USER, UserRole.ADMIN]
        required_roles = [UserRole.ADMIN, UserRole.USER]

        requester_status = get_requester_status(
            engine=test_engine,
            requester_email=admin_email,
            required_roles=required_roles
        )

        assert requester_status == RequesterStatus.VALID

    def test_requester_status__required_roles_is_superset(
        self,
        test_engine: Engine,
        basic_tables: None,
        admin_email: str,
    ) -> None:
        # The roles of admin user (the requester) are [UserRole.USER, UserRole.ADMIN]
        required_roles = [UserRole.ADMIN, UserRole.USER, UserRole.GUEST]

        requester_status = get_requester_status(
            engine=test_engine,
            requester_email=admin_email,
            required_roles=required_roles
        )

        assert requester_status == RequesterStatus.UNAUTHORIZED

    def test_requester_status__required_roles_is_empty(
        self,
        test_engine: Engine,
        basic_tables: None,
        admin_email: str,
    ) -> None:
        # The roles of admin user (the requester) are [UserRole.USER, UserRole.ADMIN]
        required_roles = []

        requester_status = get_requester_status(
            engine=test_engine,
            requester_email=admin_email,
            required_roles=required_roles
        )

        assert requester_status == RequesterStatus.VALID

    def test_requester_status__requester_not_in_database(
        self,
        test_engine: Engine,
        basic_tables: None,
    ) -> None:
        required_roles = [UserRole.ADMIN]

        requester_status = get_requester_status(
            engine=test_engine,
            requester_email="non.existent.user@test.xyz",
            required_roles=required_roles
        )

        assert requester_status == RequesterStatus.NOT_FOUND

    def test_requester_status__requester_has_no_roles(
        self,
        test_engine: Engine,
        basic_tables: None,
        user_credentials: UserCredentials,
        user_full_name: str,
    ) -> None:
        create_user(engine=test_engine, user_full_name=user_full_name, credentials=user_credentials, roles=[])
        required_roles = [UserRole.ADMIN]

        requester_status = get_requester_status(
            engine=test_engine,
            requester_email=user_credentials.email,
            required_roles=required_roles
        )

        assert requester_status == RequesterStatus.UNAUTHORIZED
