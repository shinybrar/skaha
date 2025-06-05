"""Models for Skaha API."""

from __future__ import annotations

import warnings
from base64 import b64encode
from typing import Any, Literal, get_args

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationInfo,
    field_validator,
    model_validator,
)
from typing_extensions import Self

from skaha import get_logger

log = get_logger(__name__)

KINDS = Literal["desktop", "notebook", "carta", "headless", "firefly"]
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
        ...,
        description="A unique name for the session.",
        examples=["skaha-test"],
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
        serialization_alias="type",
    )
    gpus: int | None = Field(None, description="Number of GPUs.", ge=1, le=28)
    cmd: str | None = Field(None, description="Command to run.", examples=["ls"])
    args: str | None = Field(
        None,
        description="Arguments to the command.",
        examples=["-la"],
    )
    env: dict[str, Any] | None = Field(
        None,
        description="Environment variables.",
        examples=[{"FOO": "BAR"}],
    )
    replicas: int = Field(
        1,
        description="Number of sessions to launch.",
        ge=1,
        le=512,
        exclude=True,
    )

    model_config = ConfigDict(validate_assignment=True, populate_by_name=True)

    # Validate that cmd, args and env are only used with headless sessions.
    @model_validator(mode="after")
    def validate_headless(self) -> Self:
        """Validate that cmd, args and env are only used for headless sessions.

        Args:
            values (Dict[str, Any]): Values to validate.

        Returns:
            Dict[str, Any]: Validated values.
        """
        if (self.cmd or self.args or self.env) and self.kind != "headless":
            msg = "cmd, args, env only allowed for headless sessions."
            raise ValueError(msg)
        return self

    @field_validator("kind", mode="after")
    @classmethod
    def _validate_kind(cls, value: KINDS, context: ValidationInfo) -> KINDS:
        """Validate kind.

        Args:
            value (KINDS): Value to validate.
            context(ValidationInfo): Class validation context.

        Returns:
            KINDS: Validated value.
        """
        valid: tuple[str] = get_args(KINDS)
        if value not in valid:
            msg = f"invalid session kind: {value}"
            raise ValueError(msg)

        if value in {"firefly", "desktop"} and (
            context.data.get("cmd")
            or context.data.get("args")
            or context.data.get("cores")
            or context.data.get("ram")
        ):
            warnings.warn(
                f"cmd, args, cores and ram ignored for {value} sessions.",
                stacklevel=2,
            )

        return value

    @field_validator("replicas")
    @classmethod
    def _validate_replicas(cls, value: int, context: ValidationInfo) -> int:
        """Validate replicas.

        Args:
            value (int): Value to validate.
            context(ValidationInfo): Class validation context.

        Returns:
            int: Validated value.
        """
        kind: str = context.data.get("kind", "")
        if kind in {"firefly", "desktop"} and value > 1:
            msg = f"multiple replicas invalid for {kind} sessions."
            raise ValueError(msg)
        return value


class FetchSpec(BaseModel):
    """Payload specification for fetching session[s] information.

    Args:
        BaseModel (pydantic.BaseModel): Pydantic BaseModel.

    Returns:
        object: Pydantic BaseModel object.
    """

    kind: KINDS | None = Field(
        None,
        description="Type of skaha session.",
        examples=["headless"],
        alias="type",
    )
    status: STATUS | None = Field(
        None,
        description="Status of the session.",
        examples=["Running"],
    )
    view: VIEW | None = Field(None, description="Number of views.", examples=["all"])

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
        min_length=1,
        validate_default=True,
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
        if value != "images.canfar.net":
            msg = "only images.canfar.net is supported."
            raise ValueError(msg)
        return value

    def encoded(self) -> str:
        """Return the encoded username:secret.

        Returns:
            str: String encoded in base64 format.
        """
        return b64encode(f"{self.username}:{self.secret}".encode()).decode()
