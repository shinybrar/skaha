"""HTTPx authentication hooks for automatic token refresh and certificate renewal.

This module provides httpx event hooks that automatically handle authentication
expiry and refresh for different authentication modes:

- **X509/Default Mode**: Automatically renews certificates when expired
- **OIDC Mode**: Automatically refreshes access tokens using refresh tokens
- **User-provided credentials**: Bypasses automatic refresh

The hooks are designed to be used with httpx clients to provide seamless
authentication management without requiring manual intervention.

Usage:
    ```python
    from skaha.client import SkahaClient
    from skaha.hooks.httpx.auth import create_auth_hook

    client = SkahaClient()
    auth_hook = create_auth_hook(client)

    # The hook is automatically applied to the client's httpx instances
    ```

Note:
    The hooks modify the request before it's sent, updating headers and
    authentication credentials as needed. They also save updated configuration
    to disk when credentials are refreshed.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Callable

import jwt

from skaha import get_logger
from skaha.auth import oidc

if TYPE_CHECKING:
    from collections.abc import Awaitable

    import httpx
    from pydantic import SecretStr

    from skaha.client import SkahaClient

log = get_logger(__name__)


class AuthenticationError(Exception):
    """Exception raised when authentication refresh fails."""


def hook(client: SkahaClient) -> Callable[[httpx.Request], None]:
    """Create an authentication refresh hook for httpx clients.

    Args:
        client (SkahaClient): The SkahaClient instance containing auth configuration.

    Returns:
        Callable[[httpx.Request], None]: The auth hook function.
    """

    def refresh(request: httpx.Request) -> None:
        """Synchronous refresh hook for httpx clients.

        Args:
            request (httpx.Request): The outgoing HTTP request.
        """
        if client.auth.expired:
            if (
                not client.auth.oidc.expiry.refresh
                or client.auth.oidc.expiry.refresh < time.time()
            ):
                log.debug("refresh token expired, skipping refresh")
                msg = "refresh token expired, run `skaha auth login` to re-authenticate"
                raise AuthenticationError(msg)

            try:
                log.debug("Starting synchronous OIDC token refresh")
                token: SecretStr = oidc.sync_refresh(
                    url=str(client.auth.oidc.endpoints.token),
                    identity=str(client.auth.oidc.client.identity),
                    secret=str(client.auth.oidc.client.secret),
                    token=str(client.auth.oidc.token.refresh),
                )
                log.debug("Synchronous OIDC token refresh successful")
                client.auth.oidc.token.access = token.get_secret_value()
                client.auth.oidc.expiry.access = jwt.decode(  # type: ignore [attr-defined]
                    client.auth.oidc.token.access, options={"verify_signature": False}
                ).get("exp")
                client.save()
                log.debug("Authentication refreshed and configuration saved")
                client.client.headers.update(
                    {"Authorization": f"Bearer {client.auth.oidc.token.access}"}
                )
                request.headers.update(
                    {"Authorization": f"Bearer {client.auth.oidc.token.access}"}
                )
                log.debug("HTTP request headers updated with new authentication")
                log.info("OIDC Access Token Refreshed")
            except Exception as err:
                msg = f"Failed to refresh authentication: {err}"
                log.exception(msg)
                raise AuthenticationError(msg) from err

    return refresh


def ahook(client: SkahaClient) -> Callable[[httpx.Request], Awaitable[None]]:
    """Create an asynchronous authentication refresh hook for httpx clients.

    Args:
        client (SkahaClient): The SkahaClient instance containing auth configuration.

    Returns:
        Callable[[httpx.Request], Awaitable[None]]: The asynchronous auth hook function.
    """

    async def refresh(request: httpx.Request) -> None:
        """Asynchronous refresh hook for httpx clients.

        Args:
            request (httpx.Request): The outgoing HTTP request.
        """
        # Skip refresh for user-provided credentials
        if client.auth.expired:
            if (
                not client.auth.oidc.expiry.refresh
                or client.auth.oidc.expiry.refresh < time.time()
            ):
                msg = "Refresh token expired, run `skaha auth login` to re-authenticate"
                raise AuthenticationError(msg)

            try:
                log.debug("starting oidc async refresh")
                token: SecretStr = await oidc.refresh(
                    url=str(client.auth.oidc.endpoints.token),
                    identity=str(client.auth.oidc.client.identity),
                    secret=str(client.auth.oidc.client.secret),
                    token=str(client.auth.oidc.token.refresh),
                )
                client.auth.oidc.token.access = token.get_secret_value()
                client.auth.oidc.expiry.access = jwt.decode(  # type: ignore [attr-defined]
                    client.auth.oidc.token.access, options={"verify_signature": False}
                ).get("exp")
                client.save()
                log.debug("authentication refreshed and configuration saved")
                client.client.headers.update(
                    {"Authorization": f"Bearer {client.auth.oidc.token.access}"}
                )
                request.headers.update(
                    {"Authorization": f"Bearer {client.auth.oidc.token.access}"}
                )
                log.debug("request headers updated with new authentication")
                log.info("oidc authentication token refreshed")
            except Exception as err:
                msg = f"Failed to refresh authentication: {err}"
                log.exception(msg)
                raise AuthenticationError(msg) from err

    return refresh
