"""Skaha Client."""
import logging
from os import environ
from platform import machine, platform, python_version, release, system
from time import asctime, gmtime
from typing import Any, Dict, Type

from pydantic import (
    AnyHttpUrl,
    BaseModel,
    Field,
    FilePath,
    ValidationError,
    root_validator,
    validator,
)
from pydantic.tools import parse_obj_as
from requests import Session

from skaha import __version__
from skaha.exceptions import InvalidCertificateError, InvalidServerURL

# Setup logging format
logging.basicConfig(format="%(asctime)s %(levelname)s %(message)s", level=logging.INFO)
# Get the logger
log = logging.getLogger(__name__)


class SkahaClient(BaseModel):
    """SkahaClient is the base class for all other API clients.

    Args:
        server (str): Server URL.
        version (str): Skaha API version.
        certificate (str): Certificate file.
        timeout (int): Timeout for requests.

    Raises:
        InvalidServerURL: If the server URL is invalid.
        InvalidCertificateError: If the client is given an invalid certificate.

    Examples:
        >>> from skaha.client import SkahaClient
            class MyClient(SkahaClient):
                pass

    """

    server: AnyHttpUrl = Field(
        default="https://ws-uv.canfar.net/skaha", title="Server URL", type=AnyHttpUrl
    )
    version: str = Field(default="v0", title="Skaha API Version")
    certificate: FilePath = Field(
        default="{HOME}/.ssl/cadcproxy.pem".format(HOME=environ["HOME"]),
        type=str,
        title="Certificate File",
    )
    timeout: int = Field(default=15, title="Timeout")
    session: Type[Session] = Field(default=Session())
    cert: str = Field(default="")
    verify: bool = Field(default=True)

    @validator("server", pre=True, always=True)
    def server_has_valid_url(cls, value: str):
        """Check if server is a valid url."""
        try:
            value = parse_obj_as(AnyHttpUrl, value)
        except ValidationError as error:
            log.error(error)
            raise InvalidServerURL("invalid server url")
        return value

    @validator("certificate", pre=True, always=True)
    def certificate_exists_and_is_readable(cls, value: str):
        """Check the certificate."""
        try:
            value = parse_obj_as(FilePath, value)  # type: ignore
        except ValidationError as error:
            log.error(error)
            raise InvalidCertificateError(
                "certificate needs to be absolute path and readable"
            )
        return value

    @root_validator(skip_on_failure=True)
    def session_set_headers(cls, values: Dict[str, Any]):
        """Set headers to session object after all values has been obtained."""
        values["session"].headers.update({"X-Skaha-Server": str(values["server"])})
        values["session"].headers.update(
            {"Content-Type": "application/x-www-form-urlencoded"}
        )
        values["session"].headers.update({"Accept": "*/*"})
        values["session"].headers.update({"User-Agent": "skaha-client"})
        values["session"].headers.update({"Date": asctime(gmtime())})
        values["session"].headers.update({"X-Skaha-Version": __version__})
        values["session"].headers.update(
            {"X-Skaha-Client-Python-Version": python_version()}
        )
        values["session"].headers.update({"X-Skaha-Client-Arch": machine()})
        values["session"].headers.update({"X-Skaha-Client-OS": system()})
        values["session"].headers.update({"X-Skaha-Client-OS-Version": release()})
        values["session"].headers.update({"X-Skaha-Client-Platform": platform()})
        return values

    @root_validator(skip_on_failure=True)
    def assign_cert_values(cls, values: Dict[str, Any]):
        """Check the certificate."""
        values["session"].headers.update({"X-Skaha-Authentication-Type": "certificate"})
        values["cert"] = str(values["certificate"])
        values["verify"] = True
        values["session"].cert = values["cert"]
        values["session"].verify = values["verify"]
        return values
