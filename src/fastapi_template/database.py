from sys import exit
from typing import Any, Type

from pydantic import EmailStr
from sqlalchemy import URL, Engine, Insert, create_engine, select
from sqlalchemy.dialects.postgresql import insert as pg_upsert
from sqlalchemy.orm import DeclarativeBase, Session

import fastapi_template.config as cfg
from fastapi_template import UserRole, get_logger
from fastapi_template.logic import calc_password_hash, extract_names
from fastapi_template.models.database import Address, Base, Role, User
from fastapi_template.models.input import Address as InputAddress
from fastapi_template.models.input import UserCredentials

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
#   Structural functions.
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


# ------------------------------------------------------------------------------
#   Operational functions.
# ------------------------------------------------------------------------------
def get_roles(
    engine: Engine,
    roles: list[UserRole],
    session_: Session | None = None,
) -> list[Role] | None:
    """Get a list of database roles as specified by a list of UserRoles."""

    def _get_roles(normalized_session: Session) -> list[Role] | None:
        """Internal query using a normalized session."""
        return normalized_session.scalars(
            select(Role)
            .where(Role.name.in_([role.value for role in roles]))
        ).all()

    if session_:
        return _get_roles(normalized_session=session_)
    with Session(engine) as session:
        return _get_roles(normalized_session=session)


def create_user(
    engine: Engine,
    user_full_name: str,
    credentials: UserCredentials,
    roles: list[UserRole],
    address: InputAddress | None = None,
) -> None:
    """Create database user and associate it with the indicated roles."""

    with Session(engine) as session:
        user_roles = get_roles(engine=engine, roles=roles, session_=session)
        username_parts = extract_names(full_name=user_full_name)
        records = [
            {
                "email": credentials.email,
                "first_name": username_parts.first,
                "last_name": username_parts.last or None,
                "password_hash": calc_password_hash(password=credentials.password),
            }
        ]
        base_statement = pg_upsert(User).values(records)
        statement = base_statement.on_conflict_do_nothing(index_elements=["email"])
        user = session.scalar(statement=statement.returning(User))
        session.commit()

        if user:
            msg = f"User {username_parts.first} created and respective roles assigned."
            user.roles.extend(user_roles)
            session.commit()
        else:
            user = session.scalar(select(User).where(User.email == credentials.email))
            msg = f"User {username_parts.first} already existed. Nothing changed."
        if user and address:
            address_base_statement = pg_upsert(Address).values([address.model_dump()])
            address_statement = address_base_statement.on_conflict_do_nothing(
                index_elements=["street", "city", "state", "country"]
            )
            user_address = session.scalar(statement=address_statement.returning(Address))
            user.address = user_address
            session.commit()
    logger.info(msg=msg)


def create_app_admin_user(
    engine: Engine,
    admin_credentials=UserCredentials(email=cfg.APP_ADMIN_FAKE_EMAIL, password=cfg.APP_ADMIN_PASSWORD),
    user_full_name: str = cfg.APP_ADMIN_FAKE_NAME,
)  -> None:
    """Create admin user and associate it with the appropriate roles."""

    create_user(
        engine=engine,
        user_full_name=user_full_name,
        credentials=admin_credentials,
        roles=[UserRole.USER, UserRole.ADMIN]
    )


def get_user_by_email(
    engine: Engine,
    email: EmailStr,
    session_: Session | None = None
) -> User | None:
    """Get a user by email."""

    def _get_user_by_email(normalized_session: Session) -> User | None:
        """Internal query using a normalized session."""

        return normalized_session.scalar(select(User).where(User.email == email))

    if session_:
        return _get_user_by_email(normalized_session=session_)
    with Session(engine) as session:
        return _get_user_by_email(normalized_session=session)


def get_user_by_credentials(
    engine: Engine,
    credentials: UserCredentials,
    session_: Session | None = None
) -> User | None:
    """Get a user by the information present on credentials."""

    return get_user_by_email(engine=engine, email=credentials.email, session_=session_)
