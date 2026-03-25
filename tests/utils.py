from collections.abc import Sequence
from functools import reduce
from itertools import combinations
from operator import add

import pytest
from sqlalchemy import Engine
from sqlalchemy.orm import Session

from fastapi_template import UserRole
from fastapi_template.database import get_user_by_email


def check_sequences_contents(checked_sequence: Sequence, expected_sequence: Sequence) -> None:
    """Check if two sequences have the same content irrespective to the order of their elements."""

    if len(checked_sequence) != len(expected_sequence):
        pytest.fail("The sequences don't have the same size")
    if set(checked_sequence) != set(expected_sequence):
        pytest.fail("The sequences don't have the same elements.")


def get_user_by_email_closure(missed_user_email: str):
    """Clojure to generate a conditional mocked get_user_by_email function."""

    def _selective_get_user_by_email(engine: Engine, email: str, session_: Session | None = None):
        """Selectively don't find a user by email for use in testing."""

        if email == missed_user_email:
            return
        return get_user_by_email(engine=engine, email=email, session_=session_)

    return _selective_get_user_by_email


def get_user_roles_combinations() -> list[tuple(UserRole)]:
    """Get a list with all the combinations of valid user roles."""

    user_roles = list(UserRole)
    return reduce(add, [list(combinations(user_roles, n)) for n in range(1, len(user_roles) + 1)])
