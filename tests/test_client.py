"""Test Skaha Client API."""

import tempfile
from os import chmod

import httpx
import pytest
from pydantic import ValidationError

from skaha.client import SkahaClient


def test_client_has_session_attribute():
    """Test if it SkahaClient object contains requests.Session attribute."""
    client = SkahaClient()
    assert hasattr(client, "client")
    assert isinstance(client.client, httpx.Client)


def test_client_session():
    """Test SkahaClient object's session attribute contains ther right headers."""
    headers = [
        "x-skaha-server",
        "content-type",
        "acccept",
        "user-agent",
        "date",
        "user-agent",
        "x-skaha-registry-auth",
    ]
    skaha = SkahaClient(registry={"username": "test", "secret": "test"}, loglevel=30)
    assert any(header in skaha.client.headers.keys() for header in headers)


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
    with pytest.raises(FileNotFoundError):
        SkahaClient(certificate="abcdefd")


def test_bad_certificate_path():
    """Test bad certificate."""
    with pytest.raises(FileNotFoundError):
        SkahaClient(certificate="/gibberish/path")  # nosec: B108


def test_token_setup():
    """Test token setup."""
    token: str = "abcdef"
    skaha = SkahaClient(token=token)
    assert skaha.token == token
    assert skaha.client.headers["Authorization"] == f"Bearer {token}"


def test_non_readible_certfile():
    # Create a temporary file
    temp = tempfile.NamedTemporaryFile(delete=False)
    temp.close()
    # Change the permissions
    chmod(temp.name, 0o000)
    with pytest.raises(ValidationError):
        SkahaClient(certificate=temp.name)
