"""Skaha Authentication Configuration Module."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Annotated

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings

from skaha import get_logger

log = get_logger(__name__)


class Server(BaseModel):
    """Server information for authentication configuration."""

    name: str | None = Field(default=None, description="Server display name")
    uri: str | None = Field(default=None, description="Server URI identifier")
    url: str | None = Field(default=None, description="Server URL endpoint")


class OIDCUrls(BaseModel):
    """OIDC URL configuration."""

    discovery: str | None = Field(default=None, description="OIDC discovery URL")
    device: str | None = Field(
        default=None, description="OIDC device authorization URL"
    )
    registration: str | None = Field(
        default=None, description="OIDC client registration URL"
    )
    token: str | None = Field(default=None, description="OIDC token endpoint URL")


class OIDCClient(BaseModel):
    """OIDC client configuration."""

    identity: str | None = Field(default=None, description="OIDC client ID")
    secret: str | None = Field(default=None, description="OIDC client secret")


class OIDCTokens(BaseModel):
    """OIDC token configuration."""

    access: str | None = Field(default=None, description="Access token")
    refresh: str | None = Field(default=None, description="Refresh token")
    expiry: float | None = Field(default=None, description="Refresh Token expiry ctime")


class OIDC(BaseModel):
    """Complete OIDC configuration."""

    endpoints: Annotated[
        OIDCUrls, Field(default_factory=OIDCUrls, description="OIDC URLs")
    ]
    client: Annotated[
        OIDCClient,
        Field(default_factory=OIDCClient, description="OIDC client credentials"),
    ]
    token: Annotated[
        OIDCTokens,
        Field(default_factory=OIDCTokens, description="OIDC tokens"),
    ]
    server: Annotated[
        Server,
        Field(default_factory=Server, description="OIDC server information"),
    ]

    def valid(self) -> bool:
        """Check if all required information for getting new access tokens exists.

        Returns:
            bool: True if all required OIDC information is present, False otherwise.
        """
        required: list[str | float | None] = [
            self.endpoints.discovery,
            self.endpoints.token,
            self.client.identity,
            self.client.secret,
            self.token.refresh,
            self.token.expiry,
        ]

        # Check if all required fields are defined
        if not all(required):
            log.debug("Missing required OIDC configuration.")
            return False

        return True

    @property
    def expired(self) -> bool:
        """Check if the OIDC access token is active.

        Returns:
            bool: True if the access token is active, False otherwise.
        """
        if self.token.refresh is None:
            return True
        if self.token.expiry is None:
            return True
        return self.token.expiry < time.time()


class X509(BaseModel):
    """X.509 certificate configuration."""

    path: str | None = Field(default=None, description="Path to PEM certificate file")
    expiry: float | None = Field(default=None, description="Certificate expiry ctime")
    server: Annotated[
        Server,
        Field(default_factory=Server, description="X509 server information"),
    ]

    def valid(self) -> bool:
        """Check if the certificate filepath is defined and expiry is in the future.

        Returns:
            bool: True if certificate path exists and is not expired, False otherwise.
        """
        if self.path is None:
            return False
        if not Path(self.path).exists():
            return False
        return self.expiry is not None

    @property
    def expired(self) -> bool:
        """Check if the X.509 certificate is expired.

        Returns:
            bool: True if the certificate is expired, False otherwise.
        """
        if self.expiry is None:
            return True
        return self.expiry < time.time()


class AuthConfig(BaseSettings):
    """Authentication configuration."""

    mode: Annotated[str | None, Field(default=None, description="Authentication mode")]
    oidc: Annotated[
        OIDC,
        Field(
            default_factory=lambda: OIDC(
                endpoints=OIDCUrls(),
                client=OIDCClient(),
                token=OIDCTokens(),
                server=Server(),
            ),
            description="OIDC settings",
        ),
    ]
    x509: Annotated[
        X509,
        Field(
            default_factory=lambda: X509(server=Server()),
            description="X.509 certificate settings",
        ),
    ]

    def valid(self) -> bool:
        """Validate that the selected authentication mode has valid configuration.

        Returns:
            AuthConfig: The validated configuration.

        Raises:
            ValueError: If the selected mode's configuration is invalid.
        """
        if self.mode == "oidc":
            return self.oidc.valid()
        if self.mode == "x509":
            return self.x509.valid()
        return False

    def expired(self) -> bool:
        """Check if the authentication configuration is expired.

        Returns:
            bool: True if the authentication configuration is expired, False otherwise.
        """
        if self.mode == "oidc":
            return self.oidc.expired
        if self.mode == "x509":
            return self.x509.expired
        return True
