"""Test Skaha Client API."""

import pytest
import requests
from pydantic import ValidationError

from skaha.client import SkahaClient


def test_client_has_session_attribute():
    """Test if it SkahaClient object contains requests.Session attribute."""
    client = SkahaClient()
    assert hasattr(client, "session")
    assert isinstance(client.session, requests.Session)


def test_client_session():
    """Test SkahaClient object's session attribute contains ther right headers."""
    headers = [
        "X-Skaha-Server",
        "Content-Type",
        "Accept",
        "User-Agent",
        "Date",
        "X-Skaha-Version",
        "X-Skaha-Client-Python-Version",
        "X-Skaha-Client-Arch",
        "X-Skaha-Client-OS",
        "X-Skaha-Client-OS-Version",
        "X-Skaha-Client-Platform",
    ]
    client = SkahaClient()
    assert any(list(map(lambda h: h in client.session.headers.keys(), headers)))


def test_bad_server_no_schema():
    """Test server URL without schema."""
    with pytest.raises(ValidationError):
        SkahaClient(server="ws-uv.canfar.net")


def test_default_certificate():
    """Test validation with default certificate value."""
    try:
        SkahaClient()
    except ValidationError:
        raise AssertionError()
    assert True


def test_bad_certificate():
    """Test bad certificate."""
    with pytest.raises(ValidationError):
        SkahaClient(certificate="abcdefd")


def test_bad_certificate_path():
    """Test bad certificate."""
    with pytest.raises(ValidationError):
        SkahaClient(certificate="/gibberish/path")  # nosec: B108
