"""Client Configuration Model."""

from __future__ import annotations

from pydantic import AnyHttpUrl, BaseModel, Field


class ClientConfig(BaseModel):
    """Client Configuration Model."""

    url: str | None = Field(default=None, description="Server URL")
    version: str | None = Field(default=None, description="Server API version")
    concurrency: int | None = Field(
        default=32, description="Number of concurrent requests to the server"
    )
    timeout: int | None = Field(
        default=30, description="Timeout for server requests in seconds", gt=0, le=300
    )


class RegistryConfig(BaseModel):
    """Container Registry Configuration Model."""

    url: AnyHttpUrl | None = Field(default=None, description="Container Registry URL")
    username: str | None = Field(
        default=None,
        description="Username for the container registry",
        min_length=1,
        max_length=255,
        examples=["shinybrar"],
    )
    secret: str | None = Field(
        default=None,
        description="Secret for the container registry",
        min_length=1,
        max_length=255,
        examples=["sup3rs3cr3t"],
    )
