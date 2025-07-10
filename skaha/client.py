"""Skaha Client."""

from __future__ import annotations

import ssl
from contextlib import asynccontextmanager, contextmanager
from datetime import datetime, timezone
from os import R_OK, access
from time import asctime, gmtime
from typing import TYPE_CHECKING, Any

from cryptography import x509
from cryptography.hazmat.backends import default_backend
from httpx import URL, AsyncClient, Client, Limits
from pydantic import (
    PrivateAttr,
    ValidationInfo,
    field_validator,
)
from typing_extensions import Self

from skaha import __version__, get_logger, set_log_level
from skaha.hooks.httpx import errors
from skaha.models.config import Configuration

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Iterator
    from pathlib import Path
    from types import TracebackType


log = get_logger(__name__)


class SkahaClient(Configuration):
    """Skaha Client for interacting with CANFAR Science Platform services.

    The SkahaClient provides both synchronous and asynchronous HTTP clients with
    comprehensive authentication support including X.509 certificates, OIDC tokens,
    and bearer tokens. It automatically configures SSL contexts, headers, and
    connection settings based on the authentication mode.

    Authentication Modes:
        - **x509**: Uses X.509 certificate authentication from auth.x509 configuration
        - **oidc**: Uses OIDC bearer token authentication from auth.oidc configuration
        - **default**: Uses default X.509 certificate from auth.default configuration
        - **token**: Uses user-provided bearer token (overrides configuration)

    Args:
        certificate (Path | None): Path to X.509 certificate file for authentication.
            Overrides configuration-based authentication when provided.
        timeout (int): HTTP request timeout in seconds. Default is 30.
        registry (ContainerRegistry | None): Credentials for private container registry.
        concurrency (int): Maximum number of concurrent connections for async client.
            Default is 32.
        token (SecretStr | None): Bearer token for authentication. When provided,
            overrides all other authentication methods.
        loglevel (int): Logging level (10=DEBUG, 20=INFO, 30=WARNING, etc.).
            Default is 20 (INFO).
        auth (Authentication): Authentication configuration containing mode and
            credentials for different authentication types.

    Attributes:
        client (Client): Synchronous HTTPx client instance (lazy-loaded).
        asynclient (AsyncClient): Asynchronous HTTPx client instance (lazy-loaded).
        expiry (float | None): Expiry timestamp for current authentication method.
            Returns None for user-provided credentials.

    Raises:
        ValidationError: If the client configuration is invalid.
        FileNotFoundError: If certificate file does not exist or is not readable.
        PermissionError: If certificate file is not accessible.
        ValueError: If certificate is expired or not yet valid.

    Examples:
        Basic usage with default authentication:

        >>> from skaha.client import SkahaClient
        >>> client = SkahaClient()
        >>> response = client.client.get("/session")

        Using with bearer token:

        >>> from pydantic import SecretStr
        >>> client = SkahaClient(token=SecretStr("your-token-here"))
        >>> response = client.client.get("/session")

        Using with custom certificate:

        >>> from pathlib import Path
        >>> client = SkahaClient(certificate=Path("/path/to/cert.pem"))
        >>> response = client.client.get("/session")

        Async usage:

        >>> async with SkahaClient() as client:
        ...     response = await client.asynclient.aget("/session")

        Context manager usage:

        >>> with SkahaClient() as client:
        ...     response = client.client.get("/session")

    Note:
        The client automatically handles SSL context creation, header generation,
        and connection pooling. Debug logging is available by setting loglevel=10
        to trace client creation and authentication flow.
    """

    _client: Client | None = PrivateAttr(
        default=None,
    )

    _asynclient: AsyncClient | None = PrivateAttr(
        default=None,
    )

    # Model Validation Methods

    @field_validator("loglevel", mode="before")
    @classmethod
    def _set_log_level(cls, value: int) -> int:
        """Set the log level for the client.

        Args:
            value (int): Logging level.

        Returns:
            int: Logging level.
        """
        set_log_level(value)
        return value

    @field_validator("certificate")
    @classmethod
    def _check_certificate(cls, value: Path, info: ValidationInfo) -> Path:
        """Validate the certificate file.

        Args:
            value (Path): Path to the certificate file.
            info (ValidationInfo): Validation context.

        Returns:
            Path: Validated Path to the certificate file.
        """
        # If token is provided, skip certificate validation
        if info.data.get("token"):
            return value

        # Certificate Validation
        destination = value.resolve(strict=True)

        if not destination.is_file():
            msg = f"cert file {value} does not exist."
            raise FileNotFoundError(msg)

        if not access(destination, R_OK):
            msg = f"cert file {value} is not readable."
            raise PermissionError(msg)

        # Certifcation Date Validation
        data = destination.read_bytes()
        cert = x509.load_pem_x509_certificate(data, default_backend())
        now_utc = datetime.now(timezone.utc)

        if cert.not_valid_after_utc <= now_utc:
            msg = f"cert {value} expired."
            raise ValueError(msg)
        if cert.not_valid_before_utc >= now_utc:
            msg = f"cert {value} not valid yet."
            raise ValueError(msg)
        return value

    # Model Properties
    @property
    def client(self) -> Client:
        """Get the HTTPx Client.

        Returns:
            Client: HTTPx Client.
        """
        if self._client is None:
            self._client = self._create_client()
            log.debug("Synchronous HTTPx client created successfully")
        return self._client

    @property
    def asynclient(self) -> AsyncClient:
        """Get the HTTPx Async Client.

        Returns:
            AsyncClient: HTTPx Async Client.
        """
        if self._asynclient is None:
            self._asynclient = self._create_asynclient()
            log.debug("Asynchronous HTTPx client created successfully")
        return self._asynclient

    @property
    def expiry(self) -> float | None:
        """Get the expiry time for the current authentication method.

        Returns:
            float | None: Expiry time as Unix timestamp (seconds since epoch),
                or None if no expiry is available or user-provided credentials
                are being used.
        """
        # If user passes cert or token, do not set expiry
        if self.token or self.certificate:
            log.debug("User-passed credentials detected, returning None for expiry")
            return None

        # Map to appropriate expiry based on auth mode
        if self.auth.mode == "oidc":
            expiry = self.auth.oidc.expiry.access
            log.debug("OIDC mode: returning expiry %s", expiry)
            return expiry
        if self.auth.mode == "x509":
            expiry = self.auth.x509.expiry
            log.debug("X509 mode: returning expiry %s", expiry)
            return expiry
        if self.auth.mode == "default":
            expiry = self.auth.default.expiry
            log.debug("Default mode: returning expiry %s", expiry)
            return expiry
        log.debug("Unknown auth mode '%s', returning None for expiry", self.auth.mode)
        return None

    # Client Configuration Methods
    def _get_client_kwargs(self, is_async: bool) -> dict[str, Any]:
        """Get the keyword arguments for creating an HTTPx client.

        Args:
            is_async (bool): Whether the client is asynchronous.

        Returns:
            dict[str, Any]: Keyword arguments for creating an HTTPx client.
        """
        kwargs: dict[str, Any] = {
            "timeout": self.timeout,
            "event_hooks": {"response": [errors.acatch if is_async else errors.catch]},
        }

        if is_async:
            kwargs["limits"] = Limits(
                max_connections=self.concurrency,
                max_keepalive_connections=self.concurrency // 4,
                keepalive_expiry=5,
            )

        if self.token or self.auth.mode == "oidc":
            log.debug("Using token/OIDC authentication - no SSL context required")
        elif self.auth.mode == "x509":
            assert self.auth.x509.path is not None
            log.debug("Using X509 authentication with cert: %s", self.auth.x509.path)
            kwargs["verify"] = self._get_ssl_context(self.auth.x509.path)
        elif self.certificate:
            log.debug(
                "Using certificate authentication with cert: %s", self.certificate
            )
            kwargs["verify"] = self._get_ssl_context(self.certificate)
        elif self.auth.mode == "default":
            assert self.auth.default.path is not None
            log.debug(
                "Using default authentication with cert: %s", self.auth.default.path
            )
            kwargs["verify"] = self._get_ssl_context(self.auth.default.path)
        return kwargs

    def _create_client(self) -> Client:
        """Create and configure a synchronous HTTPx Client.

        Returns:
            Client: Configured synchronous HTTPx Client

        Note:
            This method is called lazily when the client property is first accessed.
            The created client is cached and reused for subsequent requests.
        """
        log.debug("Creating synchronous client with auth mode: %s", self.auth.mode)
        kwargs = self._get_client_kwargs(is_async=False)
        client: Client = Client(**kwargs)
        headers = self._get_headers()
        client.headers.update(headers)
        base_url = f"{self.url}/{self.version}"
        log.debug("Setting client base URL: %s", base_url)
        client.base_url = URL(base_url)
        return client

    def _create_asynclient(self) -> AsyncClient:
        """Create and configure an asynchronous HTTPx Client.

        Connection Pooling:
            - max_connections: Set to configured concurrency level
            - max_keepalive_connections: Set to 25% of max_connections
            - keepalive_expiry: 5 seconds for connection reuse

        Returns:
            AsyncClient: Configured asynchronous HTTPx Client

        Note:
            This method is called lazily when the asynclient property is first accessed.
            The created client is cached and reused for subsequent async requests.
        """
        log.debug("Creating asynchronous client with auth mode: %s", self.auth.mode)
        kwargs = self._get_client_kwargs(is_async=True)
        asynclient: AsyncClient = AsyncClient(**kwargs)
        headers = self._get_headers()
        asynclient.headers.update(headers)
        base_url = f"{self.url}/{self.version}"
        log.debug("Setting async client base URL: %s", base_url)
        asynclient.base_url = URL(base_url)
        return asynclient

    def _get_ssl_context(self, certpath: Path) -> ssl.SSLContext:
        """Get SSL Context from authentication configuration.

        Args:
            certpath (Path): Path to the certificate file.

        Returns:
            ssl.SSLContext: SSL Context.
        """
        if not certpath.exists():
            msg = f"Certificate path {certpath} does not exist."
            log.error(msg)
            raise FileNotFoundError(msg)

        certfile: str = str(certpath)
        log.debug("Loading certificate chain from: %s", certfile)
        ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        ctx.minimum_version = ssl.TLSVersion.TLSv1_2
        ctx.load_cert_chain(certfile=certfile)
        log.debug("SSL context created successfully")
        return ctx

    def _get_headers(self) -> dict[str, str]:
        """Generate HTTP headers for the client based on authentication mode.

        Standard Headers:
            - X-Skaha-Server: Server name identifier
            - Content-Type: application/x-www-form-urlencoded
            - Accept: application/json
            - Date: Current GMT timestamp
            - User-Agent: Python client version

        Authentication Headers:
            - **token**: Authorization: Bearer <token>,
              X-Skaha-Authentication-Type: token
            - **oidc**: Authorization: Bearer <access_token>,
              X-Skaha-Authentication-Type: oidc
            - **x509/default/certificate**: X-Skaha-Authentication-Type: certificate

        Registry Headers:
            - X-Skaha-Registry-Auth: Base64 encoded registry credentials (if configured)

        Returns:
            dict[str, str]: Complete HTTP headers dictionary ready for use with
                HTTPx clients. Headers include authentication, content type,
                and any configured registry authentication.

        Note:
            User-provided tokens take precedence over configuration-based
            authentication. Registry authentication headers are only added if a
            registry is configured.
        """
        headers: dict[str, str] = {
            "X-Skaha-Server": str(self.name),
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
            "Date": asctime(gmtime()),
            "User-Agent": f"python/{__version__}",
        }

        # Handle user-passed token first
        if self.token:
            assert self.token is not None
            headers.update(
                {
                    "Authorization": f"Bearer {self.token.get_secret_value()}",
                    "X-Skaha-Authentication-Type": "token",
                },
            )
        # Use authentication mode from configuration
        elif self.auth.mode == "oidc":
            # Use OIDC access token
            if self.auth.oidc.token.access:
                headers.update(
                    {
                        "Authorization": f"Bearer {self.auth.oidc.token.access}",
                        "X-Skaha-Authentication-Type": "oidc",
                    },
                )
            else:
                msg = "OIDC mode selected but no access token available"
                log.error(msg)
                raise ValueError(msg)
        elif self.auth.mode in ("x509", "default") or self.certificate:
            headers.update(
                {
                    "X-Skaha-Authentication-Type": "certificate",
                },
            )

        if self.registry:
            headers.update(
                {
                    "X-Skaha-Registry-Auth": self.registry.encoded(),
                },
            )

        log.debug("Generated headers: %s", list(headers.keys()))
        return headers

    # Context Manager Methods
    @contextmanager
    def _session(self) -> Iterator[Client]:
        """Sync context."""
        log.debug("Entering synchronous session context")
        try:
            yield self.client
        finally:
            log.debug("Exiting synchronous session context")
            self._close()

    def __enter__(self) -> Self:
        """Sync context manager entry."""
        log.debug("Entering synchronous context manager")
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Sync context manager exit."""
        log.debug("Exiting synchronous context manager")
        self._close()

    def _close(self) -> None:
        """Close sync client."""
        if self._client:
            log.debug("Closing synchronous HTTPx client")
            self._client.close()
            self._client = None
            log.debug("Synchronous HTTPx client closed")
        else:
            log.debug("No synchronous client to close")

    @asynccontextmanager
    async def _asession(self) -> AsyncIterator[AsyncClient]:
        """Async context."""
        log.debug("Entering asynchronous session context")
        try:
            yield self.asynclient
        finally:
            log.debug("Exiting asynchronous session context")
            await self._aclose()

    async def __aenter__(self) -> Self:
        """Async context manager entry."""
        log.debug("Entering asynchronous context manager")
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Async context manager exit."""
        log.debug("Exiting asynchronous context manager")
        await self._aclose()

    async def _aclose(self) -> None:
        """Close async client."""
        if self._asynclient:
            log.debug("Closing asynchronous HTTPx client")
            await self._asynclient.aclose()
            self._asynclient = None
            log.debug("Asynchronous HTTPx client closed")
        else:
            log.debug("No asynchronous client to close")

    def __del__(self) -> None:
        """Cleanup on deletion."""
        log.debug("SkahaClient instance being deleted - cleaning up clients")
        # Sync session cleanup
        self._client = None
        # Async session cleanup
        self._asynclient = None
