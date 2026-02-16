from sys import exit

from sqlalchemy import create_engine, URL
from sqlalchemy.orm import DeclarativeBase

import fastapi_template.config as cfg


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

def create_all_tables(declarative_base: DeclarativeBase) -> None:
    declarative_base.metadata.create_all(bind=engine, checkfirst=True)
