from typing import Any, Type
from sys import exit

from sqlalchemy import create_engine, Engine, Insert, select, URL
from sqlalchemy.dialects.postgresql import insert as pg_upsert
from sqlalchemy.orm import DeclarativeBase, Session

import fastapi_template.config as cfg
from fastapi_template import get_logger, UserRole
from fastapi_template.logic import calc_password_hash
from fastapi_template.models.database import Base, Role, User


# ------------------------------------------------------------------------------
#   Resources initialization.
# ------------------------------------------------------------------------------
logger = get_logger(module_name=__name__)

if not all([cfg.APP_DATABASE, cfg.APP_ADMIN_USER, cfg.APP_ADMIN_PASSWORD]):
    print("Missing database credentials.")
    exit(-1)

database_url = URL(
    drivername="postgresql+psycopg2",
    username=cfg.APP_ADMIN_USER,
    password=cfg.APP_ADMIN_PASSWORD.get_secret_value(),
    host="postgresql-db",
    database=cfg.APP_DATABASE,
    port=None,
    query={}
)

engine = create_engine(
    url=database_url,
    isolation_level="REPEATABLE READ"
)


# ------------------------------------------------------------------------------
#   General database utils.
# ------------------------------------------------------------------------------
def get_session_generator():
    """Get a session generator."""

    with Session(engine) as session:
        yield session


def pg_bulk_upsert(
    session: Session,
    model: Type[Base],
    insert_class: Insert,
    insert_method: str,
    records: list[dict[str, Any]],
    indexes: list[str]
) -> None:
    """Execute a bulk upsert using PostgreSQL dialect."""

    base_statement = insert_class(model).values(records)
    statement = getattr(base_statement, insert_method)(index_elements=indexes)
    session.execute(statement=statement)
    session.commit()


# ------------------------------------------------------------------------------
#   Operational functions.
# ------------------------------------------------------------------------------
def create_all_tables(engine: Engine, declarative_base: DeclarativeBase) -> None:
    """Create all tables that were not already created."""

    declarative_base.metadata.create_all(bind=engine, checkfirst=True)
    logger.info(msg="All tables created if necessary.")


def fill_roles(engine: Engine) -> None:
    """Fill the roles table."""

    records = [{"name": role} for role in UserRole.get_roles()]
    with Session(engine) as session:
        pg_bulk_upsert(
            session=session,
            model=Role,
            insert_class=pg_upsert,
            insert_method="on_conflict_do_nothing",
            records=records,
            indexes=["name"]
        )
    logger.info(msg="Role table filled with valid roles.")


def create_app_admin_user(engine: Engine)  -> None:
    """Create admin user and associate it with the appropriate roles."""

    with Session(engine) as session:
        admin_user_roles = session.scalars(
            select(Role)
            .where(
                (Role.name == UserRole.USER.value) |
                (Role.name == UserRole.ADMIN.value)
            )
        ).all()
        records = [
            {
                "email": cfg.APP_ADMIN_FAKE_EMAIL,
                "first_name": cfg.APP_ADMIN_FAKE_NAME,
                "password_hash": calc_password_hash(password=cfg.APP_ADMIN_PASSWORD),
            }
        ]
        base_statement = pg_upsert(User).values(records)
        statement = base_statement.on_conflict_do_nothing(index_elements=["email"])
        admin_user = session.scalar(statement=statement.returning(User))
        session.commit()

        if admin_user:
            msg = "App admin user created and respective roles assigned."
            admin_user.roles.extend(admin_user_roles)
            session.commit()
        else:
            msg = "App admin user already existed. Nothing changed."
    logger.info(msg=msg)
