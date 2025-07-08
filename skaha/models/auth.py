"""Skaha Authentication Configuration Module."""

from __future__ import annotations

import time
from os import R_OK, access
from pathlib import Path
from typing import Annotated

from cryptography import x509
from cryptography.hazmat.backends import default_backend
from pydantic import AnyHttpUrl, AnyUrl, BaseModel, Field, model_validator
from typing_extensions import Self

from skaha import get_logger
from skaha.models.http import Server
from skaha.models.types import Mode  # noqa: TC001

log = get_logger(__name__)


class Endpoint(BaseModel):
    """OIDC URL configuration."""

    discovery: Annotated[str | None, Field(description="OIDC discovery URL")] = None
    device: Annotated[
        str | None, Field(description="OIDC device authorization URL")
    ] = None
    registration: Annotated[
        str | None, Field(description="OIDC client registration URL")
    ] = None
    token: Annotated[str | None, Field(description="OIDC token endpoint URL")] = None


class Client(BaseModel):
    """OIDC client configuration."""

    identity: Annotated[str | None, Field(description="OIDC client ID")] = None
    secret: Annotated[str | None, Field(description="OIDC client secret")] = None


class Token(BaseModel):
    """OIDC token configuration."""

    access: Annotated[str | None, Field(description="Access token")] = None
    refresh: Annotated[str | None, Field(description="Refresh token")] = None


class Expiry(BaseModel):
    """OIDC token expiry times."""

    access: Annotated[
        float | None, Field(description="Access token expiry in ctime")
    ] = None
    refresh: Annotated[
        float | None, Field(description="Refresh token expiry in ctime")
    ] = None


class OIDC(BaseModel):
    """Complete OIDC configuration."""

    endpoints: Annotated[
        Endpoint,
        Field(default_factory=Endpoint, description="OIDC Endpoints."),
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
        ),
    ]
    server: Annotated[
        Server,
        Field(description="X509 server information"),
    ] = Server(
        name="CADC-CANFAR",
        uri=AnyUrl("ivo://cadc.nrc.ca/skaha"),
        url=AnyHttpUrl("https://ws-uv.canfar.net/skaha"),
        version="v0",
    )

    @model_validator(mode="after")
    def _compute_expiry(self) -> Self:
        """Compute expiry from certificate file if not already set."""
        # Only compute if expiry is still the default value (0.0)
        if self.expiry == 0.0:
            self.expiry = self._read_expiry_from_cert()
        return self

    def _read_expiry_from_cert(self) -> float:
        """Read expiry time from the certificate file.

        Returns:
            float: expiry utc in ctime or 0.0 if cert doesn't exist/can't be read.
        """
        try:
            self.valid()
            data = self.path.read_bytes()
            cert = x509.load_pem_x509_certificate(data, default_backend())
            return cert.not_valid_after_utc.timestamp()
        except (FileNotFoundError, PermissionError, ValueError) as err:
            log.debug("Failed to read expiry from certificate: %s", err)
            return 0.0

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

    def refresh_expiry(self) -> None:
        """Refresh the expiry time from the certificate file.

        This method updates the expiry time by reading the certificate file.
        It does not check if the certificate is expired or not.
        """
        self.expiry = self._read_expiry_from_cert()

    @property
    def expired(self) -> bool:
        """Check if the X.509 certificate is expired.

        Returns:
            bool: True if the certificate is expired, False otherwise.
        """
        if self.expiry == 0.0:
            self.expiry = self._read_expiry_from_cert()
        return self.expiry < time.time()


class Authentication(BaseModel):
    """Science Platform Authentication Configuration."""

    mode: Annotated[Mode, Field(description="Authentication Mode.")] = "x509"
    oidc: Annotated[
        OIDC,
        Field(
            default_factory=lambda: OIDC(),
            description="OIDC settings",
        ),
    ]
    x509: Annotated[
        X509,
        Field(
            default_factory=lambda: X509(),
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
