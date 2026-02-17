from sys import exit

from sqlalchemy import create_engine, URL
from sqlalchemy.dialects.postgresql import insert as pg_upsert
from sqlalchemy.orm import DeclarativeBase, Session

import fastapi_template.config as cfg
from fastapi_template.models.database import Role


# ------------------------------------------------------------------------------
#   Resources initialization.
# ------------------------------------------------------------------------------
if not all([cfg.APP_DATABASE, cfg.APP_ADMIN_USER, cfg.APP_ADMIN_PASSWORD]):
    print("Missing database credentials.")
    exit(-1)

database_url = URL(
    drivername="postgresql+psycopg2",
    username=cfg.APP_ADMIN_USER,
    password=cfg.APP_ADMIN_PASSWORD,
    host="postgresql-db",
    database=cfg.APP_DATABASE,
    port=None,
    query={}
)

engine = create_engine(
    url=database_url,
    isolation_level="REPEATABLE READ"
)

session = Session(engine)
# ------------------------------------------------------------------------------


def create_all_tables(declarative_base: DeclarativeBase) -> None:
    """Create all tables that were not already created."""

    declarative_base.metadata.create_all(bind=engine, checkfirst=True)


def fill_roles() -> None:
    """Fill the roles table."""

    records = [{"name": role} for role in cfg.AppRole.get_roles()]
    base_statement = pg_upsert(Role).values(records)
    statement = base_statement.on_conflict_do_nothing(index_elements=["name"])
    session.execute(statement=statement)
    session.commit()
