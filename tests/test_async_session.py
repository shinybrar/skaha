"""Test the async session."""

from time import time
from typing import List
from uuid import uuid4

import pytest
from httpx import HTTPError
from pydantic import ValidationError

from skaha.session import AsyncSession


@pytest.fixture(scope="module")
def name():
    """Return a random name."""
    yield str(uuid4().hex[:7])


@pytest.fixture()
def async_session():
    """Test images."""
    session = AsyncSession()
    yield session


@pytest.mark.asyncio
async def test_fetch_with_kind(async_session: AsyncSession):
    """Test fetching images with kind."""
    await async_session.fetch(kind="headless")


@pytest.mark.asyncio
async def test_fetch_malformed_kind(async_session: AsyncSession):
    """Test fetching images with malformed kind."""
    with pytest.raises(ValidationError):
        await async_session.fetch(kind="invalid")  # type: ignore


@pytest.mark.asyncio
async def test_fetch_with_malformed_view(async_session: AsyncSession):
    """Test fetching images with malformed view."""
    with pytest.raises(ValidationError):
        await async_session.fetch(view="invalid")  # type: ignore


@pytest.mark.asyncio
async def test_get_session_stats(async_session: AsyncSession):
    """Test fetching images with kind."""
    response = await async_session.stats()
    assert "instances" in response.keys()


@pytest.mark.asyncio
async def test_create_session_invalid(async_session: AsyncSession, name: str):
    """Test creating a session with malformed kind."""
    with pytest.raises(ValidationError):
        await async_session.create(
            name=name,
            kind="invalid",  # type: ignore
            image="jupyter/base-notebook",
        )


@pytest.mark.asyncio
@pytest.mark.order(1)
async def test_create_session(async_session: AsyncSession, name: str):
    """Test creating a session."""
    identity: List[str] = await async_session.create(
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


@pytest.mark.asyncio
@pytest.mark.order(2)
async def test_get_succeeded(async_session: AsyncSession):
    """Test getting succeeded sessions."""
    limit: float = time() + 60  # 1 minute
    while time() < limit:
        response = await async_session.fetch(status="Succeeded")
        for result in response:
            if result["id"] == pytest.IDENTITY[0]:  # type: ignore
                assert result["status"] == "Succeeded"
                break


@pytest.mark.asyncio
@pytest.mark.order(3)
async def test_get_logs(async_session: AsyncSession):
    """Test getting logs for a session."""
    logs = await async_session.logs(ids=pytest.IDENTITY)
    assert logs != ""
    assert "TEST" in logs[pytest.IDENTITY[0]]  # type: ignore
    no_logs = await async_session.logs(ids=pytest.IDENTITY, verbose=True)
    assert no_logs is None


@pytest.mark.asyncio
@pytest.mark.order(4)
async def test_delete_session(async_session: AsyncSession, name: str):
    """Test deleting a session."""
    # Delete the session
    done = False
    while not done:
        info = await async_session.info(ids=pytest.IDENTITY)  # type: ignore
        for status in info:
            if status["status"] == "Succeeded":
                done = True
    deletion = await async_session.destroy_with(prefix=name)  # type: ignore
    assert deletion == {pytest.IDENTITY[0]: True}  # type: ignore


@pytest.mark.asyncio
async def test_bad_error_exceptions():
    """Test error handling."""
    asession = AsyncSession(server="https://bad.server.com")
    with pytest.raises(HTTPError):
        await asession.fetch()
    with pytest.raises(HTTPError):
        await asession.stats()
    with pytest.raises(HTTPError):
        await asession.destroy_with(prefix="bad")

    assert not await asession.create(
        name="bad",
        image="images.canfar.net/skaha/terminal:1.1.2",
    )

    assert not await asession.info(["bad"])
    assert not await asession.logs(["bad"])
    assert {"bad": False} == await asession.destroy(["bad"])
