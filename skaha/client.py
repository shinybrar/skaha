"""Skaha Client."""

import logging
from os import R_OK, access, environ
from pathlib import Path
from time import asctime, gmtime
from typing import Annotated, Dict, Optional

from httpx import AsyncClient, Client
from pydantic import (
    AnyHttpUrl,
    BaseModel,
    ConfigDict,
    Field,
    FilePath,
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

    Raises:
        ValidationError: If the client is misconfigured.

    Examples:
        >>> from skaha.client import SkahaClient

            class Sample(SkahaClient):
                pass
    """

    server: AnyHttpUrl = Field(
        default="https://ws-uv.canfar.net/skaha",
        title="Skaha Server URL",
        description="Skaha API Server.",
    )
    version: str = Field(
        default="v0",
        title="Skaha API Version",
        description="Version of the Skaha API to use.",
    )
    certificate: FilePath = Field(
        default=Path(f"{environ['HOME']}/.ssl/cadcproxy.pem"),
        title="X509 Certificate",
        description="Path to the X509 certificate used for authentication.",
        validate_default=True,
    )
    timeout: int = Field(
        default=15,
        title="HTTP Timeout",
        description="HTTP Timeout.",
    )
    verify: bool = Field(default=True)
    registry: Annotated[
        Optional[ContainerRegistry],
        Field(
            default=None,
            title="Container Registry",
            description="Credentials for a private container registry.",
        ),
    ] = None

    client: Client = Field(
        default=None, title="HTTPx Client", description="Synchronous HTTPx Client"
    )
    asynclient: AsyncClient = Field(
        default=None, title="HTTPx Client", description="Asynchronous HTTPx Client"
    )
    concurrency: int = Field(
        128,
        title="Concurrency",
        description="Number of concurrent requests for the async client.",
        le=1024,
        ge=1,
    )

    model_config: ConfigDict = ConfigDict(arbitrary_types_allowed=True, extra="forbid")

    @field_validator("certificate")
    @classmethod
    def _check_certificate(cls, value: FilePath) -> FilePath:
        """Validate the certificate file.

        Args:
            value (FilePath): Path to the certificate file.

        Returns:
            FilePath: Validated Path to the certificate file.
        """
        # Check if the certificate is a valid path
        assert (
            Path(value).resolve(strict=True).is_file()
        ), f"{value} is not a file or does not exist."
        assert access(Path(value), R_OK), f"{value} is not readable."
        return value

    @model_validator(mode="after")
    def _configure_clients(self) -> Self:
        """Configure the HTTPx Clients.

        Returns:
            Self: Updated SkahaClient object.
        """
        # Create the HTTPx clients if they are not passed in
        if not self.client:
            self.client: Client = Client(
                cert=str(self.certificate),
                timeout=self.timeout,
                verify=self.verify,
            )

        if not self.asynclient:
            self.asynclient: AsyncClient = AsyncClient(
                cert=str(self.certificate),
                timeout=self.timeout,
                verify=self.verify,
            )

        # Configure the HTTP headers
        headers = self._set_headers()
        self.client.headers.update(headers)
        self.asynclient.headers.update(headers)
        # Configure the base URL for the clients
        self.client.base_url = f"{self.server}/{self.version}"
        self.asynclient.base_url = f"{self.server}/{self.version}"
        return self

    def _set_headers(self) -> Dict[str, str]:
        """Set the HTTP headers for the client.

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
        return headers
