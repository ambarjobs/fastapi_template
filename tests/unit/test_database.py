import pytest   # noqa: F401
from sqlalchemy import Engine, inspect, select
from sqlalchemy.orm import Session

import fastapi_template.database as database_module
from fastapi_template import UserRole
from fastapi_template.database import Base, create_all_tables, fill_roles
from fastapi_template.models.database import Role
from tests.utils import check_sequences_contents

EXPECTED_TABLE_NAMES = ["user", "address", "role", "user_role"]

class TestDatabase:
    def test_initial_database_empty(self, test_engine) -> None:
        assert inspect(test_engine).get_table_names() == []

    def test_creation_of_all_tables(self, test_engine, monkeypatch) -> None:
        assert inspect(test_engine).get_table_names() == []
        monkeypatch.setattr(database_module, "engine", test_engine)
        create_all_tables(declarative_base=Base)
        database_table_names = inspect(test_engine).get_table_names()
        check_sequences_contents(database_table_names, EXPECTED_TABLE_NAMES)

    def test_roles_filling(self, test_engine: Engine, empty_tables, monkeypatch) -> None:
        with Session(test_engine) as session:
            initial_roles = session.scalars(select(Role.name)).all()
        assert initial_roles == []
        monkeypatch.setattr(database_module, "engine", test_engine)
        fill_roles()
        with Session(test_engine) as session:
            current_roles = session.scalars(select(Role.name)).all()
        check_sequences_contents(current_roles, UserRole.get_roles())
