from datetime import datetime
from typing import Optional

from sqlalchemy import CheckConstraint, Column, ForeignKey, Identity, String, Table
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from fastapi_template import UserRole


class Base(DeclarativeBase):
    pass

# Association table between user and role tables.
user_roles = Table(
    "user_role",
    Base.metadata,
    Column("user_id", ForeignKey("user.id"), primary_key=True),
    Column("role_id", ForeignKey("role.id"), primary_key=True),
)

def generate_role_constraint_clause() -> str:
    """Generate the constraint clause for available roles."""

    quoted_roles = [f"'{elem}'" for elem in UserRole.get_roles()]
    return f"name in ({", ".join(quoted_roles)})"


class User(Base):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(Identity(always=True), primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True)
    first_name: Mapped[str] = mapped_column(String(255))
    last_name: Mapped[str | None]
    password_hash: Mapped[str] = mapped_column(String(255))
    address_id: Mapped[int | None] = mapped_column(ForeignKey("address.id"))
    created_at: Mapped[datetime] = mapped_column(default=datetime.now)

    address: Mapped[Optional["Address"]] = relationship(back_populates="users")
    roles: Mapped[list["Role"]] = relationship(secondary=user_roles)

    def __repr__(self) -> str:
        return (
            f"User(id={self.id},"
            f" name={" ".join(filter(bool, [self.first_name, self.last_name]))}"
            f", email={self.email})")


class Address(Base):
    __tablename__ = "address"

    id: Mapped[int] = mapped_column(Identity(always=True), primary_key=True)
    street: Mapped[str] = mapped_column(String(255))
    district: Mapped[str | None]
    city: Mapped[str] = mapped_column(String(255))
    state: Mapped[str] = mapped_column(String(2))
    country:Mapped[str] = mapped_column(String(2))
    zip_code:Mapped[str] = mapped_column(String(9))

    users: Mapped[list["User"]] = relationship(back_populates="address", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return (
            f"Address(id={self.id}"
            f", street={self.street}"
            f", city={self.city}"
            f", state={self.state}"
            f", country={self.country})")


class Role(Base):
    __tablename__ = "role"

    id: Mapped[int] = mapped_column(Identity(always=True), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), CheckConstraint(generate_role_constraint_clause()), unique=True)
