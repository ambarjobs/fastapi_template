import pytest   # noqa: F401
from sqlalchemy import Engine, inspect, select
from sqlalchemy.orm import Session

import fastapi_template.config as cfg
from fastapi_template import UserRole
from fastapi_template.database import Base, create_all_tables, create_app_admin_user, fill_roles
from fastapi_template.logic import check_password
from fastapi_template.models.database import Role, User
from tests.utils import check_sequences_contents

EXPECTED_TABLE_NAMES = ["user", "address", "role", "user_role"]

class TestDatabase:
    def test_initial_database_empty(self, test_engine) -> None:
        assert inspect(test_engine).get_table_names() == []

    def test_creation_of_all_tables__nonexisting_tables(self, test_engine) -> None:
        assert inspect(test_engine).get_table_names() == []

        create_all_tables(engine=test_engine, declarative_base=Base)
        database_table_names = inspect(test_engine).get_table_names()
        check_sequences_contents(database_table_names, EXPECTED_TABLE_NAMES)

    def test_creation_of_all_tables__already_existing_tables(self, test_engine, empty_tables) -> None:
        initial_database_table_names = inspect(test_engine).get_table_names()
        check_sequences_contents(initial_database_table_names, EXPECTED_TABLE_NAMES)

        create_all_tables(engine=test_engine, declarative_base=Base)
        database_table_names = inspect(test_engine).get_table_names()
        check_sequences_contents(database_table_names, EXPECTED_TABLE_NAMES)

    def test_roles_filling__empty_roles(self, test_engine: Engine, empty_tables) -> None:
        with Session(test_engine) as session:
            initial_roles = session.scalars(select(Role.name)).all()
        assert initial_roles == []

        fill_roles(engine=test_engine)
        with Session(test_engine) as session:
            current_roles = session.scalars(select(Role.name)).all()
        check_sequences_contents(current_roles, UserRole.get_roles())

    def test_roles_filling__already_existing_roles(self, test_engine: Engine, tables_with_roles) -> None:
        with Session(test_engine) as session:
            initial_roles = session.scalars(select(Role.name)).all()
        check_sequences_contents(initial_roles, UserRole.get_roles())

        fill_roles(engine=test_engine)
        with Session(test_engine) as session:
            current_roles = session.scalars(select(Role.name)).all()
        check_sequences_contents(current_roles, UserRole.get_roles())

    def test_create_admin_user(self, test_engine: Engine, tables_with_roles) -> None:
        with Session(test_engine) as session:
            admin_user = session.scalar(select(User).where(User.email == cfg.APP_ADMIN_FAKE_EMAIL))
            assert admin_user is None

        with Session(test_engine) as session:
            expected_admin_roles = session.execute(
                select(Role.id, Role.name)
                .where(
                    (Role.name == UserRole.USER.value) |
                    (Role.name == UserRole.ADMIN.value)
                )
            ).all()

        create_app_admin_user(engine=test_engine)
        with Session(test_engine) as session:
            admin_user = session.scalar(select(User).where(User.email == cfg.APP_ADMIN_FAKE_EMAIL))
            assert admin_user.email == cfg.APP_ADMIN_FAKE_EMAIL
            assert admin_user.first_name == cfg.APP_ADMIN_FAKE_NAME
            assert check_password(password=cfg.APP_ADMIN_PASSWORD, password_hash=admin_user.password_hash)

            check_sequences_contents(
                checked_sequence=[(role.id, role.name) for role in admin_user.roles],
                expected_sequence=expected_admin_roles,
            )
