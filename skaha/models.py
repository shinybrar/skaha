"""Models for Skaha API."""

from base64 import b64encode
from os import environ
from typing import Any, Dict, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from typing_extensions import Self

from skaha.utils import logs

log = logs.get_logger(__name__)

KINDS = Literal["desktop", "notebook", "carta", "headless"]
STATUS = Literal["Pending", "Running", "Terminating", "Succeeded", "Error"]
VIEW = Literal["all"]


class CreateSpec(BaseModel):
    """Payload specification for creating a new session.

    Args:
        BaseModel (pydantic.BaseModel): Pydantic BaseModel.

    Returns:
        object: Pydantic BaseModel object.
    """

    name: str = Field(
        ..., description="A unique name for the session.", examples=["skaha-test"]
    )
    image: str = Field(
        ...,
        description="Container image to use for the session.",
        examples=["images.canfar.net/skaha/terminal:1.1.1"],
    )
    cores: int = Field(1, description="Number of cores.", ge=1, le=256)
    ram: int = Field(4, description="Amount of RAM (GB).", ge=1, le=512)
    kind: KINDS = Field(
        ...,
        description="Type of skaha session.",
        examples=["headless", "notebook"],
        alias="type",
    )
    gpus: Optional[int] = Field(None, description="Number of GPUs.", ge=1, le=28)
    cmd: Optional[str] = Field(None, description="Command to run.", examples=["ls"])
    args: Optional[str] = Field(
        None, description="Arguments to the command.", examples=["-la"]
    )
    env: Optional[Dict[str, Any]] = Field(
        None, description="Environment variables.", examples=[{"FOO": "BAR"}]
    )
    replicas: int = Field(
        1, description="Number of sessions to launch.", ge=1, le=256, exclude=True
    )

    model_config = ConfigDict(validate_assignment=True, populate_by_name=True)

    # Validate that cmd, args and env are only used with headless sessions.
    @model_validator(mode="after")
    def validate_headless(self) -> Self:
        """Validate that cmd, args and env are only used with headless sessions.

        Args:
            values (Dict[str, Any]): Values to validate.

        Returns:
            Dict[str, Any]: Validated values.
        """
        if self.cmd or self.args or self.env:
            assert (
                self.kind == "headless"
            ), "cmd, args and env are only supported for headless sessions."
        return self


class FetchSpec(BaseModel):
    """Payload specification for fetching session[s] information.

    Args:
        BaseModel (pydantic.BaseModel): Pydantic BaseModel.

    Returns:
        object: Pydantic BaseModel object.
    """

    kind: Optional[KINDS] = Field(
        None, description="Type of skaha session.", examples=["headless"], alias="type"
    )
    status: Optional[STATUS] = Field(
        None, description="Status of the session.", examples=["Running"]
    )
    view: Optional[VIEW] = Field(None, description="Number of views.", examples=["all"])

    model_config = ConfigDict(validate_assignment=True, populate_by_name=True)


class ContainerRegistry(BaseModel):
    """Authentication details for private container registry.

    Args:
        BaseModel (pydantic.BaseModel): Pydantic BaseModel.

    Returns:
        object: Pydantic BaseModel object.
    """

    url: str = Field(
        default="images.canfar.net",
        description="Server for the container registry.",
        examples=["ghcr.io"],
        validate_default=True,
    )
    username: str = Field(
        ...,
        description="Username for the container registry.",
        examples=["shiny"],
        min_length=1,
        validate_default=True,
    )
    secret: str = Field(
        ...,
        description="Personal Access Token (PAT) for the container registry.",
        examples=["ghp_1234567890"],
    )

    @field_validator("url")
    @classmethod
    def _check_url(cls, value: str) -> str:
        """Validate url.

        Args:
            value (str): Value to validate.

        Returns:
            str: Validated value.
        """
        assert (
            value == "images.canfar.net"
        ), "Currently only images.canfar.net is supported"
        return value

    @field_validator("username")
    @classmethod
    def _check_username(cls, value: str) -> str:
        """Validate username.

        Args:
            value (str): Value to validate.

        Returns:
            str: Validated value.
        """
        if not value:
            environ.get("SKAHA_REGISTRY_USERNAME", None)
        assert value, "username is required"
        return value

    @field_validator("secret")
    @classmethod
    def _check_secret(cls, value: str) -> str:
        """Validate secret.

        Args:
            value (str): Value to validate.

        Returns:
            str: Validated value.
        """
        if not value:
            value = environ.get("SKAHA_REGISTRY_SECRET", None)  # type: ignore
            log.info("Using SKAHA_REGISTRY_SECRET from environment")
        assert value, "secret is required"
        return value

    def encoded(self) -> str:
        """Return the encoded username:secret.

        Returns:
            str: String encoded in base64 format.
        """
        return b64encode(f"{self.username}:{self.secret}".encode()).decode()
