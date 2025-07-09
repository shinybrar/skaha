"""Test Skaha Client API."""

import tempfile
from pathlib import Path

import httpx
import pytest
from pydantic import ValidationError

from skaha.client import SkahaClient


def test_client_has_session_attribute():
    """Test if it SkahaClient object contains requests.Session attribute."""
    client = SkahaClient(token="test_token")
    assert hasattr(client, "client")
    assert isinstance(client.client, httpx.Client)


def test_client_session():
    """Test SkahaClient object's session attribute contains ther right headers."""
    headers = [
        "x-skaha-server",
        "content-type",
        "accept",
        "user-agent",
        "date",
        "x-skaha-registry-auth",
    ]
    from skaha.models.registry import ContainerRegistry

    registry = ContainerRegistry(username="test", secret="test")
    skaha = SkahaClient(registry=registry, token="test_token", loglevel=30)
    assert any(header in skaha.client.headers for header in headers)


def test_bad_server_no_schema():
    """Test server URL without schema."""
    with pytest.raises(ValidationError):
        SkahaClient(url="ws-uv.canfar.net")


def test_default_certificate():
    """Test validation with default certificate value."""
    try:
        SkahaClient()
    except ValidationError as err:
        raise AssertionError from err
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
    assert skaha.token.get_secret_value() == token
    assert skaha.client.headers["Authorization"] == f"Bearer {token}"


def test_non_readible_certfile():
    """Test non-readable certificate file."""
    with tempfile.NamedTemporaryFile(delete=False) as temp:
        temp_path = temp.name
    # Change the permissions
    Path(temp_path).chmod(0o000)
    with pytest.raises(PermissionError):
        SkahaClient(certificate=temp_path)
