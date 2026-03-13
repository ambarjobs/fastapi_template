from datetime import datetime, timezone

import pytest
from pydantic import SecretStr
from sqlalchemy import URL, Engine, MetaData, create_engine

import fastapi_template.config as cfg
from fastapi_template import UserRole
from fastapi_template.database import create_app_admin_user, create_user, fill_roles
from fastapi_template.models.database import Base
from fastapi_template.models.input import UserCredentials


# ------------------------------------------------------------------------------
#   Authentication fixtures.
# ------------------------------------------------------------------------------
@pytest.fixture
def test_password() -> SecretStr:
    return SecretStr("OH-p<*ph<<P~q#2.r=9Ef")


@pytest.fixture
def test_salt() -> bytes:
    # spell-checker: disable
    return b"\x87Ff\xf5\xc7?P\xea|6Q?\x04i\xa4\x0e\x89\x92\xf5\xaa\xfa@\xac\xfd\xa9\x85\x08\x90\x9c\x8a\xdft"
    # spell-checker: enable


@pytest.fixture
def admin_email() -> str:
    return "admin_user@fake.domain.xyz"


@pytest.fixture
def admin_password() -> SecretStr:
    return SecretStr("*1$f}01O4D6eOK[v|/=9q")


@pytest.fixture
def admin_full_name() -> str:
    return "Admin User"


@pytest.fixture
def admin_credentials(admin_email: str, admin_password: SecretStr) -> UserCredentials:
    return UserCredentials(email=admin_email, password=admin_password)


@pytest.fixture
def user_email() -> str:
    return "test_user@fake.domain.xyz"


@pytest.fixture
def user_password() -> SecretStr:
    return SecretStr("|QW3C'-w8C~FsGC#,z#B_")


@pytest.fixture
def user_full_name() -> str:
    return "Test User"


@pytest.fixture
def user_credentials(user_email: str, user_password: SecretStr) -> UserCredentials:
    return UserCredentials(email=user_email, password=user_password)


@pytest.fixture
def token_secret_key() -> str:
    return "42a0675552f8261e0f323eaae6b9cadc2627d240f244fc3d52b4ece409015d67"

@pytest.fixture
def frozen_time() -> datetime:
    return  datetime(
        year=2026,
        month=3,
        day=8,
        hour=18,
        minute=58,
        second=26,
        tzinfo=timezone.utc
    )


# ------------------------------------------------------------------------------
#   Database fixtures.
# ------------------------------------------------------------------------------
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
def test_engine() -> Engine:
    engine = create_engine(url=test_database_url, isolation_level="REPEATABLE READ")
    yield engine

    metadata = MetaData()
    metadata.reflect(bind=engine)
    metadata.drop_all(bind=engine)


@pytest.fixture
def empty_tables(test_engine: Engine) -> None:
    Base.metadata.create_all(bind=test_engine, checkfirst=True)


@pytest.fixture
def tables_with_roles(test_engine: Engine, empty_tables: None) -> None:
    fill_roles(engine=test_engine)


@pytest.fixture
def basic_tables(test_engine: Engine, admin_credentials: UserCredentials,  tables_with_roles: None) -> None:
    create_app_admin_user(engine=test_engine, admin_credentials=admin_credentials)


@pytest.fixture
def database_user(
    test_engine: Engine,
    tables_with_roles: None,
    user_full_name: str,
    user_credentials: UserCredentials
) -> None:
    create_user(
        engine=test_engine,
        user_full_name=user_full_name,
        credentials=user_credentials,
        roles=[UserRole.USER]
    )
