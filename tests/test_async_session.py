from uuid import uuid4

import pytest
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
