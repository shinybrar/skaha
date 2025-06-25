"""Container-related models for Skaha API.

This module contains Pydantic models related to container registries
and container authentication.
"""

from __future__ import annotations

from base64 import b64encode

from pydantic import BaseModel, Field, field_validator


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
