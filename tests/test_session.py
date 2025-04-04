"""Test Skaha Session API."""

from time import sleep, time
from typing import Any, Dict, List
from uuid import uuid4

import pytest
from httpx import HTTPError
from pydantic import ValidationError

from skaha.models import CreateSpec
from skaha.session import Session

pytest.IDENTITY: List[str] = []  # type: ignore


@pytest.fixture(scope="module")
def name():
    """Return a random name."""
    yield str(uuid4().hex[:7])


@pytest.fixture(scope="session")
def session():
    """Test images."""
    session = Session()
    yield session
    del session


def test_fetch_with_kind(session: Session):
    """Test fetching images with kind."""
    session.fetch(kind="headless")


def test_fetch_malformed_kind(session: Session):
    """Test fetching images with malformed kind."""
    with pytest.raises(ValidationError):
        session.fetch(kind="invalid")  # type: ignore


def test_fetch_with_malformed_view(session: Session):
    """Test fetching images with malformed view."""
    with pytest.raises(ValidationError):
        session.fetch(view="invalid")  # type: ignore


def test_fetch_with_malformed_status(session: Session):
    """Test fetching images with malformed status."""
    with pytest.raises(ValidationError):
        session.fetch(status="invalid")  # type: ignore


def test_session_stats(session: Session):
    """Test fetching images with kind."""
    assert "instances" in session.stats().keys()


def test_create_session_with_malformed_kind(session: Session, name: str):
    """Test creating a session with malformed kind."""
    with pytest.raises(ValidationError):
        session.create(
            name=name,
            kind="invalid",  # type: ignore
            image="ubuntu:latest",
            cmd="bash",
            replicas=1,
        )


def test_create_session_cmd_without_headless(session: Session, name: str):
    """Test creating a session without headless."""
    with pytest.raises(ValidationError):
        session.create(
            name=name,
            kind="notebook",
            image="ubuntu:latest",
            cmd="bash",
            replicas=1,
        )


def test_create_session(session: Session, name: str):
    """Test creating a session."""
    identity: List[str] = session.create(
        name=name,
        kind="headless",
        cores=1,
        ram=1,
        image="images.canfar.net/skaha/terminal:1.1.2",
        cmd="env",
        replicas=1,
        env={"TEST": "test"},
    )
    assert len(identity) == 1
    assert identity[0] != ""
    pytest.IDENTITY = identity  # type: ignore


def test_get_session_info(session: Session, name: str):
    """Test getting session info."""
    info: List[Dict[str, Any]] = [{}]
    limit = time() + 60  # 1 minute
    success: bool = False
    while time() < limit:
        sleep(1)
        info = session.info(pytest.IDENTITY)  # type: ignore
        if len(info) == 1:
            success = True
            break
    assert success, "Session info not found."


def test_session_logs(session: Session, name: str):
    """Test getting session logs."""
    limit = time() + 60  # 1 minute
    logs: Dict[str, str] = {}
    while time() < limit:
        sleep(1)
        info = session.info(pytest.IDENTITY)  # type: ignore
        if info[0]["status"] == "Succeeded":
            logs = session.logs(pytest.IDENTITY)  # type: ignore
            break
    success = False
    for line in logs[pytest.IDENTITY[0]].split("\n"):  # type: ignore
        if "TEST=test" in line:
            success = True
            break
    stdout = session.logs(pytest.IDENTITY, verbose=True)  # type: ignore
    assert stdout is None
    assert success


def test_delete_session(session: Session, name: str):
    """Test deleting a session."""
    # Delete the session
    deletion = session.destroy_with(prefix=name)  # type: ignore
    assert deletion == {pytest.IDENTITY[0]: True}  # type: ignore


def test_create_session_with_type_field(session: Session, name: str):
    """Test creating a session and confirm kind field is changed to type."""

    specification: CreateSpec = CreateSpec(
        name=name,
        image="images.canfar.net/skaha/terminal:1.1.2",
        cores=1,
        ram=1,
        kind="headless",
        cmd="env",
        replicas=1,
        env={"TEST": "test"},
    )
    data: Dict[str, Any] = specification.model_dump(exclude_none=True, by_alias=True)
    assert "type" in data
    assert data["type"] == "headless"
    assert "kind" not in data


def test_bad_error_exceptions():
    """Test error handling."""
    session = Session(server="https://bad.server.com")
    with pytest.raises(HTTPError):
        session.fetch()
    with pytest.raises(HTTPError):
        session.stats()
    with pytest.raises(HTTPError):
        session.destroy_with(prefix="bad")

    assert not session.create(
        name="bad",
        image="images.canfar.net/skaha/terminal:1.1.2",
    )

    assert not session.info(["bad"])
    assert not session.logs(["bad"])
    assert {"bad": False} == session.destroy(["bad"])
