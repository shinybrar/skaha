"""Skaha Client."""

import logging
import ssl
from os import R_OK, access, environ
from pathlib import Path
from time import asctime, gmtime
from typing import Annotated, Dict, Optional, Tuple

from httpx import AsyncClient, Client
from pydantic import (
    AnyHttpUrl,
    BaseModel,
    ConfigDict,
    Field,
    ValidationInfo,
    field_validator,
    model_validator,
)
from typing_extensions import Self

from skaha import __version__
from skaha.models import ContainerRegistry

# Setup logging format
logging.basicConfig(format="%(asctime)s %(levelname)s %(message)s", level=logging.INFO)
# Get the logger
log = logging.getLogger(__name__)


class SkahaClient(BaseModel):
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

    server: str = Field(
        default="https://ws-uv.canfar.net/skaha",
        title="Skaha Server URL",
        description="Skaha API Server.",
    )
    version: str = Field(
        default="v0",
        title="Skaha API Version",
        description="Version of the Skaha API to use.",
    )
    certificate: str = Field(
        default=f"{environ['HOME']}/.ssl/cadcproxy.pem",
        title="X509 Certificate",
        description="Path to the X509 certificate used for authentication.",
        validate_default=False,
    )
    timeout: int = Field(
        default=15,
        title="HTTP Timeout",
        description="HTTP Timeout.",
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
            description="Credentials for a private container registry.",
        ),
    ] = None

    client: Annotated[
        Client,
        Field(
            default=None,
            title="HTTPx Client",
            description="Synchronous HTTPx Client",
            validate_default=False,
            exclude=True,
        ),
    ]

    asynclient: Annotated[
        AsyncClient,
        Field(
            default=None,
            title="HTTPx Client",
            description="Asynchronous HTTPx Client",
            validate_default=False,
            exclude=True,
        ),
    ]

    token: Optional[str] = Field(
        None,
        title="Authentication Token",
        description="Authentication Token for the Skaha Server.",
        exclude=True,
        frozen=True,
    )

    concurrency: int = Field(
        16,
        title="Concurrency",
        description="Number of concurrent requests for the async client.",
        le=256,
        ge=1,
    )

    loglevel: int = Field(
        20,
        title="Logging Level",
        description="10=DEBUG, 20=INFO, 30=WARNING, 40=ERROR, 50=CRITICAL",
        le=50,
        ge=10,
    )

    # Pydantic Configuration
    model_config = ConfigDict(arbitrary_types_allowed=True, extra="forbid")

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
    def _check_certificate(cls, value: str, info: ValidationInfo) -> str:
        """Validate the certificate file.

        Args:
            value (FilePath): Path to the certificate file.

        Returns:
            FilePath: Validated Path to the certificate file.
        """
        if not info.data.get("token"):
            # Check if the certificate is a valid path
            assert (
                Path(value).resolve(strict=True).is_file()
            ), f"{value} is not a file or does not exist."
            assert access(Path(value), R_OK), f"{value} is not readable."
        return value

    @field_validator("server")
    @classmethod
    def _check_server(cls, value: str) -> str:
        """Validate the server URL.

        Args:
            value (str): Server URL.

        Returns:
            str: Validated Server URL.
        """
        return str(AnyHttpUrl(value))

    @model_validator(mode="after")
    def _configure_clients(self) -> Self:
        """Configure the HTTPx Clients.

        Returns:
            Self: Updated SkahaClient object.
        """
        if self.token:
            self.client, self.asynclient = self._get_token_clients()
        else:
            self.client, self.asynclient = self._get_cert_clients()

        # Configure the HTTP headers
        headers = self._get_headers()
        self.client.headers.update(headers)
        self.asynclient.headers.update(headers)
        # Configure the base URL for the clients
        self.client.base_url = f"{self.server}/{self.version}"
        self.asynclient.base_url = f"{self.server}/{self.version}"
        return self

    def _get_token_clients(self) -> Tuple[Client, AsyncClient]:
        """Get the clients with token authentication.

        Returns:
            Tuple[Client, AsyncClient]: Synchronous and Asynchronous HTTPx Clients.
        """
        log.info("Using token authentication.")
        client: Client = Client(
            timeout=self.timeout,
        )
        asynclient: AsyncClient = AsyncClient(
            timeout=self.timeout,
        )
        return client, asynclient

    def _get_cert_clients(self) -> Tuple[Client, AsyncClient]:
        """Get the clients with certificate authentication.

        Returns:
            Tuple[Client, AsyncClient]: Synchronous and Asynchronous HTTPx Clients.
        """
        log.info("Using certificate authentication.")
        ctx = ssl.create_default_context()
        ctx.load_cert_chain(certfile=self.certificate)
        client: Client = Client(
            timeout=self.timeout,
            verify=ctx,
        )
        asynclient: AsyncClient = AsyncClient(
            timeout=self.timeout,
            verify=ctx,
        )
        return client, asynclient

    def _get_headers(self) -> Dict[str, str]:
        """Get the HTTP headers for the client.

        Returns:
            Dict[str, str]: HTTP headers.
        """
        headers: Dict[str, str] = {}
        headers.update({"X-Skaha-Server": str(self.server)})
        headers.update({"Content-Type": "application/x-www-form-urlencoded"})
        headers.update({"Accept": "*/*"})
        headers.update({"Date": asctime(gmtime())})
        headers.update({"X-Skaha-Client": f"python/{__version__}"})
        headers.update({"X-Skaha-Authentication-Type": "certificate"})
        if self.registry:
            headers.update({"X-Skaha-Registry-Auth": f"{self.registry.encoded()}"})
        if self.token:
            headers.update({"Authorization": f"Bearer {self.token}"})
            headers.update({"X-Skaha-Authentication-Type": "token"})
        return headers
