"""Integration tests for SkahaClient auth hook integration."""

from __future__ import annotations

from unittest.mock import Mock, patch

import pytest
from pydantic import SecretStr

from skaha.client import SkahaClient
from skaha.hooks.httpx.auth import ahook, hook


class TestClientAuthIntegration:
    """Test that auth hooks are properly integrated with SkahaClient."""

    def test_oidc_mode_includes_auth_hooks(self):
        """Test that OIDC mode includes auth hooks in client kwargs."""
        with patch("skaha.client.SkahaClient._check_certificate"):
            client = SkahaClient()
            client.auth = Mock()
            client.auth.mode = "oidc"
            client.token = None
            client.certificate = None

            # Get client kwargs for sync client
            kwargs = client._get_client_kwargs(is_async=False)

            # Should include request hooks for auth
            assert "event_hooks" in kwargs
            assert "request" in kwargs["event_hooks"]
            assert len(kwargs["event_hooks"]["request"]) == 1

            # Get client kwargs for async client
            kwargs_async = client._get_client_kwargs(is_async=True)

            # Should include request hooks for auth
            assert "event_hooks" in kwargs_async
            assert "request" in kwargs_async["event_hooks"]
            assert len(kwargs_async["event_hooks"]["request"]) == 1

    def test_user_token_skips_auth_hooks(self):
        """Test that user-provided token skips auth hooks."""
        with patch("skaha.client.SkahaClient._check_certificate"):
            client = SkahaClient(token=SecretStr("user-token"))
            client.auth = Mock()
            client.auth.mode = "oidc"

            # Get client kwargs
            kwargs = client._get_client_kwargs(is_async=False)

            # Should not include request hooks for auth
            assert "event_hooks" in kwargs
            assert "request" not in kwargs["event_hooks"]

    def test_user_certificate_skips_auth_hooks(self):
        """Test that user-provided certificate skips auth hooks."""
        with patch("skaha.client.SkahaClient._check_certificate"):
            client = SkahaClient()
            client.auth = Mock()
            client.auth.mode = "oidc"
            client.token = None
            client.certificate = "/path/to/cert.pem"

            # Get client kwargs
            kwargs = client._get_client_kwargs(is_async=False)

            # Should not include request hooks for auth
            assert "event_hooks" in kwargs
            assert "request" not in kwargs["event_hooks"]

    def test_non_oidc_mode_skips_auth_hooks(self):
        """Test that non-OIDC modes skip auth hooks."""
        with patch("skaha.client.SkahaClient._check_certificate"), \
             patch("skaha.client.SkahaClient._get_ssl_context") as mock_ssl:
            mock_ssl.return_value = Mock()

            client = SkahaClient()
            client.auth = Mock()
            client.auth.mode = "x509"
            client.auth.x509 = Mock()
            client.auth.x509.path = Mock()
            client.token = None
            client.certificate = None

            # Get client kwargs
            kwargs = client._get_client_kwargs(is_async=False)

            # Should not include request hooks for auth
            assert "event_hooks" in kwargs
            assert "request" not in kwargs["event_hooks"]

    def test_response_hooks_always_included(self):
        """Test that response hooks for error handling are always included."""
        with patch("skaha.client.SkahaClient._check_certificate"):
            client = SkahaClient()
            client.auth = Mock()
            client.auth.mode = "oidc"
            client.token = None
            client.certificate = None

            # Get client kwargs
            kwargs = client._get_client_kwargs(is_async=False)

            # Should always include response hooks for error handling
            assert "event_hooks" in kwargs
            assert "response" in kwargs["event_hooks"]
            assert len(kwargs["event_hooks"]["response"]) == 1

    def test_auth_hook_functions_are_correct_type(self):
        """Test that the correct auth hook functions are used."""
        with patch("skaha.client.SkahaClient._check_certificate"):
            client = SkahaClient()
            client.auth = Mock()
            client.auth.mode = "oidc"
            client.token = None
            client.certificate = None

            # Get sync client kwargs
            kwargs_sync = client._get_client_kwargs(is_async=False)
            sync_hook_func = kwargs_sync["event_hooks"]["request"][0]

            # Get async client kwargs
            kwargs_async = client._get_client_kwargs(is_async=True)
            async_hook_func = kwargs_async["event_hooks"]["request"][0]

            # Verify the hook functions are created by the correct factory functions
            # We can't directly compare functions, but we can verify they're callable
            assert callable(sync_hook_func)
            assert callable(async_hook_func)

            # The sync hook should be a regular function
            import inspect
            assert not inspect.iscoroutinefunction(sync_hook_func)

            # The async hook should be a coroutine function
            assert inspect.iscoroutinefunction(async_hook_func)

    @patch("skaha.hooks.httpx.auth.hook")
    @patch("skaha.hooks.httpx.auth.ahook")
    def test_hook_factory_functions_called(self, mock_ahook, mock_hook):
        """Test that the correct hook factory functions are called."""
        with patch("skaha.client.SkahaClient._check_certificate"):
            client = SkahaClient()
            client.auth = Mock()
            client.auth.mode = "oidc"
            client.token = None
            client.certificate = None

            # Create sync client kwargs
            client._get_client_kwargs(is_async=False)
            mock_hook.assert_called_once_with(client)

            # Create async client kwargs
            client._get_client_kwargs(is_async=True)
            mock_ahook.assert_called_once_with(client)

    def test_client_creation_with_auth_hooks(self):
        """Test that clients can be created successfully with auth hooks."""
        with patch("skaha.client.SkahaClient._check_certificate"):
            client = SkahaClient()
            client.auth = Mock()
            client.auth.mode = "oidc"
            client.token = None
            client.certificate = None

            # Should be able to create sync client without errors
            sync_client = client.client
            assert sync_client is not None

            # Should be able to create async client without errors
            async_client = client.asynclient
            assert async_client is not None

    def test_multiple_client_access_reuses_instances(self):
        """Test that multiple accesses to client properties reuse the same instances."""
        with patch("skaha.client.SkahaClient._check_certificate"):
            client = SkahaClient()
            client.auth = Mock()
            client.auth.mode = "oidc"
            client.token = None
            client.certificate = None

            # First access creates the client
            sync_client1 = client.client
            sync_client2 = client.client

            # Should be the same instance
            assert sync_client1 is sync_client2

            # Same for async client
            async_client1 = client.asynclient
            async_client2 = client.asynclient

            # Should be the same instance
            assert async_client1 is async_client2
