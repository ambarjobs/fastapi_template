from functools import reduce
from itertools import combinations
from operator import add
from typing import NamedTuple

import pytest  # noqa: F401
from sqlalchemy import Engine, inspect, select
from sqlalchemy.orm import Session

from fastapi_template import UserRole
from fastapi_template.database import Base, create_all_tables, create_app_admin_user, create_user, fill_roles, get_roles
from fastapi_template.logic import check_password, extract_names
from fastapi_template.models.database import Role, User
from fastapi_template.models.input import Address, UserCredentials
from tests.utils import check_sequences_contents

EXPECTED_TABLE_NAMES = ["user", "address", "role", "user_role"]


def get_user_roles_combinations():
    user_roles = list(UserRole)
    return reduce(add, [list(combinations(user_roles, n)) for n in range(1, len(user_roles) + 1)])


class GetRolesParams(NamedTuple):
    """Parameters for get_roles testing."""

    roles: list[UserRole]
    result: list[UserRole]

    @classmethod
    def get_params_names(cls):
        return ','.join(cls._fields)


class TestDatabaseStructuralFunctions:
    def test_initial_database_empty(self, test_engine: Engine) -> None:
        assert inspect(test_engine).get_table_names() == []

    def test_creation_of_all_tables__nonexisting_tables(self, test_engine: Engine) -> None:
        assert inspect(test_engine).get_table_names() == []

        create_all_tables(engine=test_engine, declarative_base=Base)
        database_table_names = inspect(test_engine).get_table_names()
        check_sequences_contents(database_table_names, EXPECTED_TABLE_NAMES)

    def test_creation_of_all_tables__already_existing_tables(self, test_engine: Engine, empty_tables: None) -> None:
        initial_database_table_names = inspect(test_engine).get_table_names()
        check_sequences_contents(initial_database_table_names, EXPECTED_TABLE_NAMES)

        create_all_tables(engine=test_engine, declarative_base=Base)
        database_table_names = inspect(test_engine).get_table_names()
        check_sequences_contents(database_table_names, EXPECTED_TABLE_NAMES)

    def test_roles_filling__empty_roles(self, test_engine: Engine, empty_tables: None) -> None:
        with Session(test_engine) as session:
            initial_roles = session.scalars(select(Role.name)).all()
        assert initial_roles == []

        fill_roles(engine=test_engine)
        with Session(test_engine) as session:
            current_roles = session.scalars(select(Role.name)).all()
        check_sequences_contents(current_roles, UserRole.get_roles())

    def test_roles_filling__already_existing_roles(self, test_engine: Engine, tables_with_roles: None) -> None:
        with Session(test_engine) as session:
            initial_roles = session.scalars(select(Role.name)).all()
        check_sequences_contents(initial_roles, UserRole.get_roles())

        fill_roles(engine=test_engine)
        with Session(test_engine) as session:
            current_roles = session.scalars(select(Role.name)).all()
        check_sequences_contents(current_roles, UserRole.get_roles())

    def test_create_app_admin_user__no_previous_admin_user(
        self,
        test_engine: Engine,
        admin_credentials: UserCredentials,
        admin_full_name: str,
        tables_with_roles: None
    ) -> None:
        # Check app_admin_user do not exists on User table.
        with Session(test_engine) as session:
            admin_user = session.scalar(select(User).where(User.email == admin_credentials.email))
            assert admin_user is None

        with Session(test_engine) as session:
            expected_admin_roles = session.execute(
                select(Role.id, Role.name)
                .where(
                    (Role.name == UserRole.USER.value) |
                    (Role.name == UserRole.ADMIN.value)
                )
            ).all()

        create_app_admin_user(engine=test_engine, admin_credentials=admin_credentials, user_full_name=admin_full_name)
        with Session(test_engine) as session:
            admin_user = session.scalar(select(User).where(User.email == admin_credentials.email))
            assert admin_user.email == admin_credentials.email
            assert admin_user.first_name == extract_names(full_name=admin_full_name).first
            assert check_password(password=admin_credentials.password, password_hash=admin_user.password_hash)

            check_sequences_contents(
                checked_sequence=[(role.id, role.name) for role in admin_user.roles],
                expected_sequence=expected_admin_roles,
            )

    def test_create_app_admin_user__pre_existent_admin_user(
        self,
        test_engine: Engine,
        basic_tables: None,
        admin_credentials: UserCredentials,
        admin_full_name: str,
    ) -> None:
        with Session(test_engine) as session:
            expected_admin_roles = session.execute(
                select(Role.id, Role.name)
                .where(
                    (Role.name == UserRole.USER.value) |
                    (Role.name == UserRole.ADMIN.value)
                )
            ).all()

        # Check admin_user already exists.
        with Session(test_engine) as session:
            admin_user = session.scalar(select(User).where(User.email == admin_credentials.email))
            assert admin_user.email == admin_credentials.email
            assert admin_user.first_name == extract_names(full_name=admin_full_name).first
            assert check_password(password=admin_credentials.password, password_hash=admin_user.password_hash)
            check_sequences_contents(
                checked_sequence=[(role.id, role.name) for role in admin_user.roles],
                expected_sequence=expected_admin_roles,
            )

        create_app_admin_user(engine=test_engine, admin_credentials=admin_credentials, user_full_name=admin_full_name)
        with Session(test_engine) as session:
            admin_user = session.scalar(select(User).where(User.email == admin_credentials.email))
            assert admin_user.email == admin_credentials.email
            assert admin_user.first_name == extract_names(full_name=admin_full_name).first
            assert check_password(password=admin_credentials.password, password_hash=admin_user.password_hash)

            check_sequences_contents(
                checked_sequence=[(role.id, role.name) for role in admin_user.roles],
                expected_sequence=expected_admin_roles,
            )

get_roles_params_combinations = [
    GetRolesParams(
        roles=role_combination,
        result=role_combination
    ) for role_combination in get_user_roles_combinations()
]

class TestDatabaseOperationalFunctions:
    @pytest.mark.parametrize(
        argnames=GetRolesParams.get_params_names(),
        argvalues=get_roles_params_combinations
    )
    def test_get_roles__implicit_session(
        self,
        test_engine: Engine,
        tables_with_roles: None,
        roles: list[UserRole],
        result: list[UserRole],
    ) -> None:
        user_roles = get_roles(engine=test_engine, roles=roles)

        check_sequences_contents(
            checked_sequence=[role.name for role in user_roles],
            expected_sequence=[role.value for role in result]
        )

    @pytest.mark.parametrize(
        argnames=GetRolesParams.get_params_names(),
        argvalues=get_roles_params_combinations
    )
    def test_get_roles__explicit_session(
        self,
        test_engine: Engine,
        tables_with_roles: None,
        roles: list[UserRole],
        result: list[UserRole]
    ) -> None:
        with Session(test_engine) as session:
            user_roles = get_roles(engine=test_engine, roles=roles, session_=session)

        check_sequences_contents(
            checked_sequence=[role.name for role in user_roles],
            expected_sequence=[role.value for role in result]
        )

    def test_get_roles__empty_roles__implicit_session(
        self,
        test_engine: Engine,
        tables_with_roles: None,
    ) -> None:
        user_roles = get_roles(engine=test_engine, roles=[])

        assert user_roles == []

    def test_get_roles__empty_roles__explicit_session(
        self,
        test_engine: Engine,
        tables_with_roles: None,
    ) -> None:
        with Session(test_engine) as session:
            user_roles = get_roles(engine=test_engine, roles=[], session_=session)

        assert user_roles == []

    @pytest.mark.parametrize(
        argnames="user_roles",
        argvalues=get_user_roles_combinations() + [()]
    )
    def test_create_user__new_user__no_address(
        self,
        test_engine: Engine,
        user_credentials: UserCredentials,
        user_full_name: str,
        tables_with_roles: None,
        user_roles: list[UserRole],
    ) -> None:
        # Check user do not exists on User table.
        with Session(test_engine) as session:
            user = session.scalar(select(User).where(User.email == user_credentials.email))
            assert user is None

        create_user(engine=test_engine, user_full_name=user_full_name, credentials=user_credentials, roles=user_roles)
        with Session(test_engine) as session:
            user = session.scalar(select(User).where(User.email == user_credentials.email))
            assert user.email == user_credentials.email
            assert user.first_name == extract_names(full_name=user_full_name).first
            assert check_password(password=user_credentials.password, password_hash=user.password_hash)
            assert user.address is None

            check_sequences_contents(
                checked_sequence=[role.name for role in user.roles],
                expected_sequence=[role.value for role in user_roles],
            )

    @pytest.mark.parametrize(
        argnames="user_roles",
        argvalues=get_user_roles_combinations() + [()]
    )
    def test_create_user__new_user__with_address(
        self,
        test_engine: Engine,
        user_credentials: UserCredentials,
        user_full_name: str,
        tables_with_roles: None,
        user_roles: list[UserRole],
        user_address: Address,
    ) -> None:
        # Check user do not exists on User table.
        with Session(test_engine) as session:
            user = session.scalar(select(User).where(User.email == user_credentials.email))
            assert user is None

        create_user(
            engine=test_engine,
            user_full_name=user_full_name,
            credentials=user_credentials,
            roles=user_roles,
            address=user_address
        )
        with Session(test_engine) as session:
            user = session.scalar(select(User).where(User.email == user_credentials.email))
            assert user.email == user_credentials.email
            assert user.first_name == extract_names(full_name=user_full_name).first
            assert check_password(password=user_credentials.password, password_hash=user.password_hash)
            assert user.address.street == user_address.street
            assert user.address.district == user_address.district
            assert user.address.city == user_address.city
            assert user.address.state == user_address.state
            assert user.address.country == user_address.country
            assert user.address.zip_code == user_address.zip_code

            check_sequences_contents(
                checked_sequence=[role.name for role in user.roles],
                expected_sequence=[role.value for role in user_roles],
            )

    @pytest.mark.parametrize(
        argnames="parametrized_user_roles",
        argvalues=get_user_roles_combinations() + [()]
    )
    def test_create_user__existing_user__no_address(
        self,
        test_engine: Engine,
        user_credentials: UserCredentials,
        user_full_name: str,
        database_user: None,
        user_roles: list[UserRole],
        parametrized_user_roles: list[UserRole],
    ) -> None:
        # Check user already exists on User table.
        with Session(test_engine) as session:
            user = session.scalar(select(User).where(User.email == user_credentials.email))
            assert user is not None

        create_user(
            engine=test_engine,
            user_full_name=user_full_name,
            credentials=user_credentials,
            roles=parametrized_user_roles
        )
        with Session(test_engine) as session:
            user = session.scalar(select(User).where(User.email == user_credentials.email))
            assert user.email == user_credentials.email
            assert user.first_name == extract_names(full_name=user_full_name).first
            assert check_password(password=user_credentials.password, password_hash=user.password_hash)
            assert user.address is None

            check_sequences_contents(
                checked_sequence=[role.name for role in user.roles],
                expected_sequence=[role.value for role in user_roles],
            )

    @pytest.mark.parametrize(
        argnames="parametrized_user_roles",
        argvalues=get_user_roles_combinations() + [()]
    )
    def test_create_user__existing_user__with_address(
        self,
        test_engine: Engine,
        user_credentials: UserCredentials,
        user_full_name: str,
        database_user: None,
        user_roles: list[UserRole],
        parametrized_user_roles: list[UserRole],
        user_address: Address,
    ) -> None:
        # Check user do not exists on User table.
        with Session(test_engine) as session:
            user = session.scalar(select(User).where(User.email == user_credentials.email))
            assert user is not None

        create_user(
            engine=test_engine,
            user_full_name=user_full_name,
            credentials=user_credentials,
            roles=parametrized_user_roles,
            address=user_address
        )
        with Session(test_engine) as session:
            user = session.scalar(select(User).where(User.email == user_credentials.email))
            assert user.email == user_credentials.email
            assert user.first_name == extract_names(full_name=user_full_name).first
            assert check_password(password=user_credentials.password, password_hash=user.password_hash)
            assert user.address.street == user_address.street
            assert user.address.district == user_address.district
            assert user.address.city == user_address.city
            assert user.address.state == user_address.state
            assert user.address.country == user_address.country
            assert user.address.zip_code == user_address.zip_code

            check_sequences_contents(
                checked_sequence=[role.name for role in user.roles],
                expected_sequence=[role.value for role in user_roles],
            )
