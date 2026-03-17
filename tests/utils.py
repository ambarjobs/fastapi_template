from collections.abc import Sequence

import pytest
from sqlalchemy import Engine
from sqlalchemy.orm import Session

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
