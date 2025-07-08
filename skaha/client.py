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
    """Skaha Client.

    Args:
        server (str): Server URL.
        version (str): Skaha API version.
        certificate (str): Certificate file.
        timeout (int): HTTP Timeout.
        verify (bool): Verify SSL certificate.
        registry (ContainerRegistry): Credentials for a private registry.
        client (Client): HTTPx Client.
        asynclient (AsyncClient): HTTPx Async Client.
        concurrency (int): Number of concurrent requests.
        token (str): Authentication token.
        loglevel (int): Logging level. Default is 20 (INFO).

    Raises:
        ValidationError: If the client is misconfigured.
        FileNotFoundError: If the cert file does not exist or is not readable.

    Examples:
        >>> from skaha.client import SkahaClient

            class Sample(SkahaClient):
                pass
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
        return self._client

    @property
    def asynclient(self) -> AsyncClient:
        """Get the HTTPx Async Client.

        Returns:
            AsyncClient: HTTPx Async Client.
        """
        if self._asynclient is None:
            self._asynclient = self._create_asynclient()
        return self._asynclient

    # Client Configuration Methods
    def _create_client(self) -> Client:
        """Create synchronous HTTPx Client.

        Returns:
            Client: HTTPx Client.
        """
        kwargs: dict[str, Any] = {
            "timeout": self.timeout,
            "event_hooks": {"response": [errors.catch]},
        }
        if not self.token:
            kwargs.update({"verify": self._get_ssl_context()})
        client: Client = Client(**kwargs)
        client.headers.update(self._get_headers())
        client.base_url = URL(f"{self.url}/{self.version}")
        return client

    def _create_asynclient(self) -> AsyncClient:
        """Create asynchronous HTTPx Client.

        Returns:
            AsyncClient: HTTPx Async Client.
        """
        kwargs: dict[str, Any] = {
            "timeout": self.timeout,
            "event_hooks": {"response": [errors.acatch]},
            "limits": Limits(
                max_connections=self.concurrency,
                max_keepalive_connections=self.concurrency // 4,
                keepalive_expiry=5,
            ),
        }
        if not self.token:
            kwargs.update({"verify": self._get_ssl_context()})
        asynclient: AsyncClient = AsyncClient(**kwargs)
        asynclient.headers.update(self._get_headers())
        asynclient.base_url = URL(f"{self.url}/{self.version}")
        return asynclient

    def _get_ssl_context(self) -> ssl.SSLContext:
        """Get SSL Context from X509 certiticate.

        Return:
            ssl.SSLContext: SSL Context.
        """
        if not self.certificate:
            msg = "No x509 certificate provided."
            raise ValueError(msg)
        certfile: str = self.certificate.as_posix()
        ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        ctx.minimum_version = ssl.TLSVersion.TLSv1_2
        ctx.load_cert_chain(certfile=certfile)
        return ctx

    def _get_headers(self) -> dict[str, str]:
        """Generate HTTP headers for the client.

        Returns:
            Dict[str, str]: HTTP headers.
        """
        headers: dict[str, str] = {
            "X-Skaha-Server": str(self.name),
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
            "Date": asctime(gmtime()),
            "User-Agent": f"python/{__version__}",
        }

        if self.token:
            headers.update(
                {
                    "Authorization": f"Bearer {self.token.get_secret_value()}",
                    "X-Skaha-Authentication-Type": "token",
                },
            )
        if self.registry:
            headers.update(
                {
                    "X-Skaha-Registry-Auth": self.registry.encoded(),
                },
            )
        if self.certificate:
            headers.update(
                {
                    "X-Skaha-Authentication-Type": "certificate",
                },
            )
        return headers

    # Context Manager Methods
    @contextmanager
    def _session(self) -> Iterator[Client]:
        """Sync context."""
        try:
            yield self.client
        finally:
            self._close()

    def __enter__(self) -> Self:
        """Sync context manager entry."""
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Sync context manager exit."""
        self._close()

    def _close(self) -> None:
        """Close sync client."""
        if self._client:
            self._client.close()
            self._client = None

    @asynccontextmanager
    async def _asession(self) -> AsyncIterator[AsyncClient]:
        """Async context."""
        try:
            yield self.asynclient
        finally:
            await self._aclose()

    async def __aenter__(self) -> Self:
        """Async context manager entry."""
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Async context manager exit."""
        await self._aclose()

    async def _aclose(self) -> None:
        """Close async client."""
        if self._asynclient:
            await self._asynclient.aclose()
            self._asynclient = None

    def __del__(self) -> None:
        """Cleanup on deletion."""
        # Sync session cleanup
        self._client = None
        # Async session cleanup
        self._asynclient = None
