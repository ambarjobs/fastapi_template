from collections.abc import Sequence

import pytest

def check_sequences_contents(checked_sequence: Sequence, expected_sequence: Sequence) -> None:
    """Check if two sequences have the same content irrespective to the order of their elements."""

    if len(checked_sequence) != len(expected_sequence):
        pytest.fail("The sequences don't have the same size")
    if set(checked_sequence) != set(expected_sequence):
        pytest.fail("The sequences don't have the same elements.")
