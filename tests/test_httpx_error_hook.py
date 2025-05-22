"""Test the error handling hooks for httpx."""

import logging
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

# Import the functions to be tested
from skaha.hooks.httpx.errors import acatch, catch

logging.disable(logging.CRITICAL)


@patch("skaha.hooks.httpx.errors.get_logger")
def test_sync_log_handles_error_response(mock_get_logger_sync):
    """Test that sync_log logs response.text and re-raises on HTTPStatusError."""
    mock_logger = MagicMock()
    mock_get_logger_sync.return_value = mock_logger

    mock_request = httpx.Request("GET", "http://example.com/error")
    # Prepare a mock response that will raise an error
    response_text = "Internal Server Error"
    mock_response = httpx.Response(500, text=response_text, request=mock_request)
    # Ensure read() is a MagicMock to check it's called
    mock_response.read = MagicMock()

    with pytest.raises(httpx.HTTPStatusError):
        catch(mock_response)

    mock_response.read.assert_called_once()
    mock_logger.error.assert_called_once_with(response_text)
    mock_get_logger_sync.assert_called_once_with("skaha.hooks.httpx.errors")


@patch("skaha.hooks.httpx.errors.get_logger")
def test_sync_log_handles_success_response(mock_get_logger_sync_success):
    """Test that sync_log does nothing if no HTTPStatusError is raised."""
    mock_logger = MagicMock()
    mock_get_logger_sync_success.return_value = mock_logger

    mock_request = httpx.Request("GET", "http://example.com/success")
    mock_response = httpx.Response(200, text="OK", request=mock_request)
    mock_response.read = MagicMock()
    # raise_for_status on a 200 OK response should not raise an error
    mock_response.raise_for_status = MagicMock()

    catch(mock_response)

    mock_response.read.assert_called_once()
    mock_response.raise_for_status.assert_called_once()  # Verify it was called
    mock_logger.error.assert_not_called()
    mock_get_logger_sync_success.assert_called_once_with("skaha.hooks.httpx.errors")


@pytest.mark.asyncio
@patch("skaha.hooks.httpx.errors.get_logger")
async def test_async_log_handles_error_response(mock_get_logger_async):
    """Test that async_log logs response.text and re-raises on HTTPStatusError."""
    mock_logger = MagicMock()
    mock_get_logger_async.return_value = mock_logger

    mock_request = httpx.Request("GET", "http://example.com/async_error")
    response_text = "Async Internal Server Error"
    mock_response = httpx.Response(500, text=response_text, request=mock_request)
    # Ensure aread() is an AsyncMock to check it's called
    mock_response.aread = AsyncMock()

    with pytest.raises(httpx.HTTPStatusError):
        await acatch(mock_response)

    mock_response.aread.assert_called_once()  # Use assert_called_once for AsyncMock too
    mock_logger.error.assert_called_once_with(response_text)
    mock_get_logger_async.assert_called_once_with("skaha.hooks.httpx.errors")


@pytest.mark.asyncio
@patch("skaha.hooks.httpx.errors.get_logger")
async def test_async_log_handles_success_response(mock_get_logger_async_success):
    """Test that async_log does nothing if no HTTPStatusError is raised (async)."""
    mock_logger = MagicMock()
    mock_get_logger_async_success.return_value = mock_logger

    mock_request = httpx.Request("GET", "http://example.com/async_success")
    mock_response = httpx.Response(200, text="OK", request=mock_request)
    mock_response.aread = AsyncMock()
    # raise_for_status on a 200 OK response should not raise an error
    mock_response.raise_for_status = MagicMock()

    await acatch(mock_response)

    mock_response.aread.assert_called_once()
    mock_response.raise_for_status.assert_called_once()
    mock_logger.error.assert_not_called()
    mock_get_logger_async_success.assert_called_once_with("skaha.hooks.httpx.errors")
