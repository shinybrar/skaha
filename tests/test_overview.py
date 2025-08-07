"""Test Skaha Overview API."""

import pytest

from skaha.overview import Overview


@pytest.fixture(scope="session")
def overview():
    """Test overview."""
    overview = Overview()
    yield overview
    del overview


def test_available(overview: Overview) -> None:
    """Test available."""
    assert overview.availability(), "Server should be available"
