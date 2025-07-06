"""Skaha Authentication Configuration Module."""

from __future__ import annotations

import time
from datetime import datetime, timezone
from os import R_OK, access
from pathlib import Path
from typing import Annotated

from cryptography import x509
from cryptography.hazmat.backends import default_backend
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings

from skaha import get_logger
from skaha.models.http import Server
from skaha.models.types import Mode  # noqa: TC001

log = get_logger(__name__)


class Endpoint(BaseModel):
    """OIDC URL configuration."""

    discovery: str | None = Field(default=None, description="OIDC discovery URL")
    device: str | None = Field(
        default=None, description="OIDC device authorization URL"
    )
    registration: str | None = Field(
        default=None, description="OIDC client registration URL"
    )
    token: str | None = Field(default=None, description="OIDC token endpoint URL")


class Client(BaseModel):
    """OIDC client configuration."""

    identity: str | None = Field(default=None, description="OIDC client ID")
    secret: str | None = Field(default=None, description="OIDC client secret")


class Token(BaseModel):
    """OIDC token configuration."""

    access: str | None = Field(default=None, description="Access token")
    refresh: str | None = Field(default=None, description="Refresh token")


class Expiry(BaseModel):
    """OIDC token expiry times."""

    access: float | None = Field(
        default=None, description="Access token expiry in ctime"
    )
    refresh: float | None = Field(
        default=None, description="Refresh token expiry in ctime"
    )


class OIDC(BaseModel):
    """Complete OIDC configuration."""

    endpoints: Annotated[
        Endpoint, Field(default_factory=Endpoint, description="OIDC Endpoints.")
    ]
    client: Annotated[
        Client,
        Field(default_factory=Client, description="OIDC Client Credentials."),
    ]
    token: Annotated[
        Token,
        Field(default_factory=Token, description="OIDC Tokens"),
    ]
    server: Annotated[
        Server,
        Field(default_factory=Server, description="Science Platform Server."),
    ]
    expiry: Annotated[
        Expiry,
        Field(default_factory=Expiry, description="OIDC Token Expiry."),
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
        if self.expiry.refresh is None:
            return True
        return self.expiry.refresh < time.time()


class X509(BaseModel):
    """X.509 certificate configuration."""

    path: Annotated[
        Path,
        Field(
            default_factory=lambda: Path.home() / ".ssl" / "cadcproxy.pem",
            title="x509 Certificate",
            description="Pathlike to PEM certificate",
        ),
    ]
    expiry: Annotated[
        float,
        Field(
            default=0.0,
            title="x509 Expiry Time",
            description="ctime of cert expiration",
            gt=time.time(),
            validate_default=False,
        ),
    ]
    server: Annotated[
        Server,
        Field(default_factory=Server, description="X509 server information"),
    ]

    def valid(self) -> bool:
        """Check if the certificate filepath is defined and expiry is in the future.

        Returns:
            bool: True if certificate path exists and is not expired, False otherwise.
        """
        destination = self.path.resolve(strict=True)
        if not destination.is_file():
            msg = f"cert file {destination} does not exist."
            raise FileNotFoundError(msg)
        if not access(destination, R_OK):
            msg = f"cert file {destination} is not readable."
            raise PermissionError(msg)
        return True

    @property
    def expired(self) -> bool:
        """Check if the X.509 certificate is expired.

        Returns:
            bool: True if the certificate is expired, False otherwise.
        """
        return self.expiry < time.time()

    def get_expiry(self) -> float:
        """Get the x509 cert expiry ctime.

        Raises:
            ValueError: If the cert is already expired,
                or not yet valid.

        Returns:
            float: expiry utc in ctime
        """
        destination = self.path.resolve(strict=True)
        data = destination.read_bytes()
        cert = x509.load_pem_x509_certificate(data, default_backend())
        now_utc = datetime.now(timezone.utc)
        if cert.not_valid_after_utc <= now_utc:
            msg = f"cert {destination} expired."
            raise ValueError(msg)
        if cert.not_valid_before_utc >= now_utc:
            msg = f"cert {destination} not valid yet."
            raise ValueError(msg)
        return cert.not_valid_after_utc.timestamp()


class Authentication(BaseSettings):
    """Authentication configuration."""

    mode: Annotated[Mode, Field(default="x509", description="Authentication mode")]
    oidc: Annotated[
        OIDC,
        Field(
            default_factory=lambda: OIDC,
            description="OIDC settings",
        ),
    ]
    x509: Annotated[
        X509,
        Field(
            default_factory=lambda: X509,
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
        status: bool = False
        if self.mode == "oidc":
            status = self.oidc.valid()
        if self.mode == "x509":
            status = self.x509.valid()
        return status

    def expired(self) -> bool:
        """Check if the authentication configuration is expired.

        Returns:
            bool: True if the authentication configuration is expired, False otherwise.
        """
        status: bool = False
        if self.mode == "oidc":
            status = self.oidc.expired
        if self.mode == "x509":
            status = self.x509.expired
        return status
