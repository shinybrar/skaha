"""Skaha Client."""

import asyncio
import logging
import ssl
from contextlib import asynccontextmanager, contextmanager
from datetime import datetime, timezone
from os import R_OK, access
from pathlib import Path
from time import asctime, gmtime
from typing import Annotated, Any, Dict, Optional

from cryptography import x509
from cryptography.hazmat.backends import default_backend
from httpx import AsyncClient, Client, Limits
from pydantic import (
    AnyHttpUrl,
    Field,
    PrivateAttr,
    SecretStr,
    ValidationInfo,
    computed_field,
    field_validator,
    model_validator,
)
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing_extensions import Self

from skaha import __version__
from skaha.hooks.httpx import errors
from skaha.models import ContainerRegistry

# Setup logging format
logging.basicConfig(format="%(asctime)s %(levelname)s %(message)s", level=logging.INFO)
# Get the logger
log = logging.getLogger(__name__)


class SkahaClient(BaseSettings):
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

    model_config = SettingsConfigDict(
        title="Skaha Client Settings",
        env_prefix="SKAHA_",
        extra="forbid",
        json_schema_mode_override="serialization",
        str_strip_whitespace=True,
        str_max_length=256,
        str_min_length=1,
    )

    server: AnyHttpUrl = Field(
        default="https://ws-uv.canfar.net/skaha",
        title="API Server URL",
        description="API Server URL.",
    )
    version: str = Field(
        default="v0",
        title="API Version",
        description="Version of the API to use.",
        pattern=r"^v\d+$",
    )
    certificate: Path = Field(
        default_factory=lambda: Path.home() / ".ssl" / "cadcproxy.pem",
        title="X509 Certificate",
        description="Path to the X509 certificate used for authentication.",
        validate_default=False,
    )
    timeout: int = Field(
        default=30,
        title="HTTP Timeout",
        description="HTTP Timeout in seconds.",
    )
    verify: bool = Field(
        default=True,
        title="Verify SSL Certificate[DEPRECATED]",
        description="Whether verify SSL Certs[DEPRECATED].",
        deprecated=True,
    )
    registry: Annotated[
        Optional[ContainerRegistry],
        Field(
            default=None,
            title="Container Registry",
            description="Credentials for a private images from a registry.",
        ),
    ] = None

    token: Optional[SecretStr] = Field(
        default=None,
        title="Authentication Token",
        description="Authentication token for the server.",
        exclude=True,
    )

    concurrency: int = Field(
        32,
        title="Concurrency",
        description="Maximum concurrent requests.",
        le=256,
        ge=1,
    )

    loglevel: int = Field(
        default=logging.INFO,
        title="Logging Level",
        description="10=DEBUG, 20=INFO, 30=WARNING, 40=ERROR, 50=CRITICAL",
        le=50,
        ge=10,
    )

    _client: Optional[Client] = PrivateAttr(
        default=None,
        init=False,
    )

    _asynclient: Optional[AsyncClient] = PrivateAttr(
        default=None,
        init=False,
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
        log.setLevel(value)
        return value

    @field_validator("certificate")
    @classmethod
    def _check_certificate(cls, value: Path, info: ValidationInfo) -> Path:
        """Validate the certificate file.

        Args:
            value (Path): Path to the certificate file.

        Returns:
            Path: Validated Path to the certificate file.
        """
        # If token is provided, skip certificate validation
        if info.data.get("token"):
            return value

        if value is None:
            raise ValueError("X509 cert path required when not using token auth.")

        # Certificate Validation
        destination = value.resolve(strict=True)

        if not destination.is_file():
            raise FileNotFoundError(f"cert file {value} does not exist.")

        if not access(destination, R_OK):
            raise PermissionError(f"cert file {value} is not readable.")

        # Certifcation Date Validation
        try:
            data = destination.read_bytes()
            cert = x509.load_pem_x509_certificate(data, default_backend())
            now_utc = datetime.now(timezone.utc)

            if cert.not_valid_after_utc <= now_utc:
                raise ValueError(f"cert {value} expired.")
            if cert.not_valid_before_utc >= now_utc:
                raise ValueError(f"cert {value} not valid yet.")
        except Exception as e:
            raise ValueError(f"invalid cert file {value}: {e}")
        return value

    @model_validator(mode="after")
    def _check_authentication(self) -> Self:
        """Check that exactly one authentication method is configured.

        Returns:
            Self: Updated object.
        """
        has_token = self.token is not None
        has_cert = self.certificate is not None

        if not has_token and not has_cert:
            raise ValueError("either token or certificate must be provided")
        return self

    # Model Properties
    @property
    @computed_field
    def client(self) -> Client:
        """Get the HTTPx Client.

        Returns:
            Client: HTTPx Client.
        """
        if self._client is None:
            self._client = self._create_client()
        return self._client

    @property
    @computed_field
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
        kwargs: Dict[str, Any] = {
            "timeout": self.timeout,
            "event_hooks": {"response": [errors.catch]},
        }
        if not self.token:
            kwargs.update({"verify": self._get_ssl_context()})
        client: Client = Client(**kwargs)
        client.headers.update(self._get_headers())
        client.base_url = f"{self.server}/{self.version}"
        return client

    def _create_asynclient(self) -> AsyncClient:
        """Create asynchronous HTTPx Client.

        Returns:
            AsyncClient: HTTPx Async Client.
        """
        kwargs: Dict[str, Any] = {
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
        asynclient.base_url = f"{self.server}/{self.version}"
        return asynclient

    def _get_ssl_context(self) -> ssl.SSLContext:
        """Get SSL Context from X509 certiticate.

        Return:
            ssl.SSLContext: SSL Context.
        """
        certfile: str = self.certificate.absolute().as_posix()
        ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        ctx.minimum_version = ssl.TLSVersion.TLSv1_2
        ctx.load_cert_chain(certfile=certfile)
        return ctx

    def _get_headers(self) -> Dict[str, str]:
        """Generate HTTP headers for the client.

        Returns:
            Dict[str, str]: HTTP headers.
        """
        headers: Dict[str, str] = {
            "X-Skaha-Server": str(self.server),
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
                }
            )
        if self.registry:
            headers.update(
                {
                    "X-Skaha-Registry-Auth": self.registry.encoded(),
                }
            )
        if self.certificate:
            headers.update(
                {
                    "X-Skaha-Authentication-Type": "certificate",
                }
            )
        return headers

    # Context Manager Methods
    @contextmanager
    def _session(self):
        """Sync context."""
        try:
            yield self.client
        finally:
            self._close()

    def __enter__(self):
        """Sync context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Sync context manager exit."""
        self._close()

    def _close(self):
        """Close sync client."""
        if self._client:
            self._client.close()
            self._client = None

    @asynccontextmanager
    async def _asession(self):
        """Async context."""
        try:
            yield self.asynclient
        finally:
            await self._aclose()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self._aclose()

    async def _aclose(self):
        """Close async client."""
        if self._asynclient:
            await self._asynclient.aclose()
            self._asynclient = None

    def _force_aclose(self):
        if not self._asynclient:
            return
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self._aclose())
        except RuntimeError:
            if hasattr(self._asynclient, "_transport"):
                if self._asynclient._transport:
                    self._asynclient._transport.close()
        except Exception as error:
            raise error
        finally:
            self._asynclient = None

    def __del__(self):
        """Cleanup on deletion."""
        try:
            # Sync session cleanup
            self._close()
            # Async session cleanup
            self._force_aclose()
        except Exception as error:
            log.error(error)
