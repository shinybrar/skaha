"""Session-related models for Skaha API.

This module contains Pydantic models related to session management,
including specifications for creating and fetching sessions.
"""

from __future__ import annotations

import warnings
from datetime import datetime  # noqa: TC003
from typing import Any, get_args

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationInfo,
    field_validator,
    model_validator,
)
from typing_extensions import Self

from skaha.models.types import Kind, Status, View


class CreateRequest(BaseModel):
    """Payload specification for creating a new session."""

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
    kind: Kind = Field(
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
    def _validate_headless(self) -> Self:
        """Validate that cmd, args and env are only used for headless sessions.

        Returns:
            Self: The validated model instance.
        """
        if (self.cmd or self.args or self.env) and self.kind != "headless":
            msg = "cmd, args, env only allowed for headless sessions."
            raise ValueError(msg)
        return self

    @field_validator("kind", mode="after")
    @classmethod
    def _validate_kind(cls, value: Kind, context: ValidationInfo) -> Kind:
        """Validate kind.

        Args:
            value (Kind): Value to validate.
            context (ValidationInfo): Class validation context.

        Returns:
            Kind: Validated value.
        """
        valid: tuple[str] = get_args(Kind)
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
            context (ValidationInfo): Class validation context.

        Returns:
            int: Validated value.
        """
        kind: str = context.data.get("kind", "")
        if kind in {"firefly", "desktop"} and value > 1:
            msg = f"multiple replicas invalid for {kind} sessions."
            raise ValueError(msg)
        return value


class FetchRequest(BaseModel):
    """Payload specification for fetching session[s] information."""

    kind: Kind | None = Field(
        None,
        description="Type of skaha session.",
        examples=["headless"],
        alias="type",
    )
    status: Status | None = Field(
        None,
        description="Status of the session.",
        examples=["Running"],
    )
    view: View | None = Field(None, description="Number of views.", examples=["all"])

    model_config = ConfigDict(validate_assignment=True, populate_by_name=True)


# This model is excluded from pep8-naming checks, since its the data shape
# of the response from the server. See [tool.ruff.per-file-ignores] in pyproject.toml
class FetchResponse(BaseModel):
    """Data model for a single session returned by the fetch API."""

    id: str
    userid: str
    runAsUID: str
    runAsGID: str
    supplementalGroups: list[int]
    appid: str
    image: str
    type: Kind
    status: Status
    name: str
    startTime: datetime
    expiryTime: datetime
    connectURL: str
    requestedRAM: str
    requestedCPUCores: str
    requestedGPUCores: str
    ramInUse: str
    gpuRAMInUse: str
    cpuCoresInUse: str
    gpuUtilization: str
