"""Tests for HTTPx authentication hooks."""
# ruff: noqa: ARG002

from __future__ import annotations

import time
from unittest.mock import Mock, patch

import httpx
import pytest
from pydantic import SecretStr

from skaha.client import SkahaClient
from skaha.hooks.httpx.auth import (
    AuthenticationError,
    ahook,
    hook,
)


class TestAuthenticationError:
    """Test the AuthenticationError exception."""

    def test_authentication_error_creation(self):
        """Test creating AuthenticationError."""
        error = AuthenticationError("Test error message")
        assert str(error) == "Test error message"
        assert isinstance(error, Exception)


class TestSyncHook:
    """Test the synchronous hook function."""

    @patch("skaha.hooks.httpx.auth.oidc.sync_refresh")
    @patch("skaha.utils.jwt.expiry")
    def test_successful_token_refresh(self, mock_jwt_expiry, mock_sync_refresh):
        """Test successful token refresh in sync hook."""
        # Setup mocks
        mock_jwt_expiry.return_value = 1234567890
        mock_sync_refresh.return_value = SecretStr("new-access-token")

        # Create mock client
        client = Mock(spec=SkahaClient)
        client.auth = Mock()
        client.auth.expired = True
        client.auth.oidc = Mock()
        client.auth.oidc.expiry = Mock()
        client.auth.oidc.expiry.refresh = time.time() + 3600  # Valid refresh token
        client.auth.oidc.endpoints = Mock()
        client.auth.oidc.endpoints.token = "https://example.com/token"
        client.auth.oidc.client = Mock()
        client.auth.oidc.client.identity = "client_id"
        client.auth.oidc.client.secret = "client_secret"
        client.auth.oidc.token = Mock()
        client.auth.oidc.token.refresh = "refresh_token"
        client.client = Mock()
        client.client.headers = {}
        client.save = Mock()

        # Create hook and request
        hook_func = hook(client)
        request = Mock(spec=httpx.Request)
        request.headers = {}

        # Execute hook
        hook_func(request)

        # Verify token refresh was called
        mock_sync_refresh.assert_called_once_with(
            url="https://example.com/token",
            identity="client_id",
            secret="client_secret",
            token="refresh_token",
        )

        # Verify token was updated
        assert client.auth.oidc.token.access == "new-access-token"
        assert client.auth.oidc.expiry.access == 1234567890

        # Verify save was called
        client.save.assert_called_once()

        # Verify headers were updated
        assert request.headers["Authorization"] == "Bearer new-access-token"
        assert client.client.headers["Authorization"] == "Bearer new-access-token"

    def test_skip_refresh_when_not_expired(self):
        """Test that hook skips refresh when auth is not expired."""
        client = Mock(spec=SkahaClient)
        client.auth = Mock()
        client.auth.expired = False

        hook_func = hook(client)
        request = Mock(spec=httpx.Request)

        # Should not raise any exceptions and should not call any refresh methods
        hook_func(request)

    def test_refresh_token_expired_error(self):
        """Test error when refresh token is expired."""
        client = Mock(spec=SkahaClient)
        client.auth = Mock()
        client.auth.expired = True
        client.auth.oidc = Mock()
        client.auth.oidc.expiry = Mock()
        client.auth.oidc.expiry.refresh = time.time() - 3600  # Expired refresh token

        hook_func = hook(client)
        request = Mock(spec=httpx.Request)

        with pytest.raises(AuthenticationError, match="refresh token expired"):
            hook_func(request)

    def test_refresh_token_none_error(self):
        """Test error when refresh token is None."""
        client = Mock(spec=SkahaClient)
        client.auth = Mock()
        client.auth.expired = True
        client.auth.oidc = Mock()
        client.auth.oidc.expiry = Mock()
        client.auth.oidc.expiry.refresh = None

        hook_func = hook(client)
        request = Mock(spec=httpx.Request)

        with pytest.raises(AuthenticationError, match="refresh token expired"):
            hook_func(request)

    @patch("skaha.hooks.httpx.auth.log")
    @patch("skaha.hooks.httpx.auth.oidc.sync_refresh")
    def test_refresh_failure_error(self, mock_sync_refresh, mock_log):
        """Test error handling when token refresh fails."""
        mock_sync_refresh.side_effect = Exception("Network error")

        client = Mock(spec=SkahaClient)
        client.auth = Mock()
        client.auth.expired = True
        client.auth.oidc = Mock()
        client.auth.oidc.expiry = Mock()
        client.auth.oidc.expiry.refresh = time.time() + 3600
        client.auth.oidc.endpoints = Mock()
        client.auth.oidc.endpoints.token = "https://example.com/token"
        client.auth.oidc.client = Mock()
        client.auth.oidc.client.identity = "client_id"
        client.auth.oidc.client.secret = "client_secret"
        client.auth.oidc.token = Mock()
        client.auth.oidc.token.refresh = "refresh_token"

        hook_func = hook(client)
        request = Mock(spec=httpx.Request)

        with pytest.raises(AuthenticationError, match="Failed to refresh"):
            hook_func(request)


class TestAsyncHook:
    """Test the asynchronous hook function."""

    @patch("skaha.hooks.httpx.auth.oidc.refresh")
    @patch("skaha.utils.jwt.expiry")
    async def test_successful_token_refresh(self, mock_jwt_expiry, mock_refresh):
        """Test successful token refresh in async hook."""
        # Setup mocks
        mock_jwt_expiry.return_value = 1234567890
        mock_refresh.return_value = SecretStr("new-access-token")

        # Create mock client
        client = Mock(spec=SkahaClient)
        client.auth = Mock()
        client.auth.expired = True
        client.auth.oidc = Mock()
        client.auth.oidc.expiry = Mock()
        client.auth.oidc.expiry.refresh = time.time() + 3600  # Valid refresh token
        client.auth.oidc.endpoints = Mock()
        client.auth.oidc.endpoints.token = "https://example.com/token"
        client.auth.oidc.client = Mock()
        client.auth.oidc.client.identity = "client_id"
        client.auth.oidc.client.secret = "client_secret"
        client.auth.oidc.token = Mock()
        client.auth.oidc.token.refresh = "refresh_token"
        client.client = Mock()
        client.client.headers = {}
        client.save = Mock()

        # Create hook and request
        hook_func = ahook(client)
        request = Mock(spec=httpx.Request)
        request.headers = {}

        # Execute hook
        await hook_func(request)

        # Verify token refresh was called
        mock_refresh.assert_called_once_with(
            url="https://example.com/token",
            identity="client_id",
            secret="client_secret",
            token="refresh_token",
        )

        # Verify token was updated
        assert client.auth.oidc.token.access == "new-access-token"
        assert client.auth.oidc.expiry.access == 1234567890

        # Verify save was called
        client.save.assert_called_once()

        # Verify headers were updated
        assert request.headers["Authorization"] == "Bearer new-access-token"
        assert client.client.headers["Authorization"] == "Bearer new-access-token"

    async def test_skip_refresh_when_not_expired(self):
        """Test that async hook skips refresh when auth is not expired."""
        client = Mock(spec=SkahaClient)
        client.auth = Mock()
        client.auth.expired = False

        hook_func = ahook(client)
        request = Mock(spec=httpx.Request)

        # Should not raise any exceptions and should not call any refresh methods
        await hook_func(request)

    async def test_refresh_token_expired_error(self):
        """Test error when refresh token is expired in async hook."""
        client = Mock(spec=SkahaClient)
        client.auth = Mock()
        client.auth.expired = True
        client.auth.oidc = Mock()
        client.auth.oidc.expiry = Mock()
        client.auth.oidc.expiry.refresh = time.time() - 3600  # Expired refresh token

        hook_func = ahook(client)
        request = Mock(spec=httpx.Request)

        with pytest.raises(AuthenticationError, match="Refresh token expired"):
            await hook_func(request)

    async def test_refresh_token_none_error(self):
        """Test error when refresh token is None in async hook."""
        client = Mock(spec=SkahaClient)
        client.auth = Mock()
        client.auth.expired = True
        client.auth.oidc = Mock()
        client.auth.oidc.expiry = Mock()
        client.auth.oidc.expiry.refresh = None

        hook_func = ahook(client)
        request = Mock(spec=httpx.Request)

        with pytest.raises(AuthenticationError, match="Refresh token expired"):
            await hook_func(request)

    @patch("skaha.hooks.httpx.auth.log")
    @patch("skaha.hooks.httpx.auth.oidc.refresh")
    async def test_refresh_failure_error(self, mock_refresh, mock_log):
        """Test error handling when token refresh fails in async hook."""
        mock_refresh.side_effect = Exception("Network error")

        client = Mock(spec=SkahaClient)
        client.auth = Mock()
        client.auth.expired = True
        client.auth.oidc = Mock()
        client.auth.oidc.expiry = Mock()
        client.auth.oidc.expiry.refresh = time.time() + 3600
        client.auth.oidc.endpoints = Mock()
        client.auth.oidc.endpoints.token = "https://example.com/token"
        client.auth.oidc.client = Mock()
        client.auth.oidc.client.identity = "client_id"
        client.auth.oidc.client.secret = "client_secret"
        client.auth.oidc.token = Mock()
        client.auth.oidc.token.refresh = "refresh_token"

        hook_func = ahook(client)
        request = Mock(spec=httpx.Request)

        with pytest.raises(AuthenticationError, match="Failed to refresh"):
            await hook_func(request)
