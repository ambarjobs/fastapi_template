import pytest

from sqlalchemy import create_engine, MetaData, URL

import fastapi_template.config as cfg
from fastapi_template.database import fill_roles, create_app_admin_user
from fastapi_template.models.database import Base


if not all([cfg.TEST_DATABASE, cfg.TEST_DATABASE_PORT, cfg.APP_ADMIN_USER, cfg.APP_ADMIN_PASSWORD]):
    print("Missing database credentials.")
    exit(-1)

test_database_url = URL(
    drivername="postgresql+psycopg2",
    username=cfg.APP_ADMIN_USER,
    password=cfg.APP_ADMIN_PASSWORD.get_secret_value(),
    host="postgresql-test-db",
    database=cfg.TEST_DATABASE,
    port=cfg.TEST_DATABASE_PORT,
    query={},
)

@pytest.fixture
def test_engine():
    engine = create_engine(url=test_database_url, isolation_level="REPEATABLE READ")
    yield engine

    metadata = MetaData()
    metadata.reflect(bind=engine)
    metadata.drop_all(bind=engine)


@pytest.fixture
def empty_tables(test_engine):
    Base.metadata.create_all(bind=test_engine, checkfirst=True)


@pytest.fixture
def tables_with_roles(test_engine, empty_tables):
    fill_roles(engine=test_engine)


@pytest.fixture
def basic_tables(test_engine, tables_with_roles):
    create_app_admin_user(engine=test_engine)
