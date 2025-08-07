"""Client HTTP Models."""

from __future__ import annotations

from pydantic import AnyHttpUrl, AnyUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Server(BaseSettings):
    """Science Platform Server Details."""

    model_config = SettingsConfigDict(
        title="Skaha Client Server Configuration",
        env_prefix="SKAHA_SERVER_",
        env_nested_delimiter="__",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="forbid",
        json_schema_mode_override="serialization",
        str_strip_whitespace=True,
        str_max_length=256,
        str_min_length=1,
    )

    name: str | None = Field(
        default=None,
        title="Server Name",
        description="Common name for the science platform server.",
        examples=["SRCnet-Sweden", "SRCnet-UK-CAM"],
        min_length=1,
        max_length=256,
        validate_default=False,
    )
    uri: AnyUrl | None = Field(
        default=None,
        title="Server URI identifier",
        description="IVOA static uri identifier for the server.",
        examples=["ivo://swesrc.chalmers.se/skaha", "ivo://canfar.cam.uksrc.org/skaha"],
    )
    url: AnyHttpUrl | None = Field(
        default=None,
        title="Server URL",
        description="URL where the server is currently accessible from.",
        examples=[
            "https://services.swesrc.chalmers.se/skaha",
            "https://canfar.cam.uksrc.org/skaha",
        ],
    )
    version: str | None = Field(
        default=None,
        title="API Version",
        description="Server API Version.",
        pattern=r"^v\d+$",
        examples=["v0", "v1", "v2"],
        min_length=2,
        max_length=8,
    )


class Connection(BaseSettings):
    """Skaha Client HTTP Connection Details."""

    model_config = SettingsConfigDict(
        title="Science Platform Client Server Configuration",
        env_prefix="SKAHA_CONNECTION_",
        env_nested_delimiter="__",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="forbid",
        json_schema_mode_override="serialization",
        str_strip_whitespace=True,
        str_max_length=256,
        str_min_length=1,
    )

    concurrency: int = Field(
        default=32,
        title="HTTP Concurrency",
        description="Maximum concurrent http requests.",
        le=256,
        ge=1,
    )
    timeout: int = Field(
        default=30,
        title="HTTP Timeout",
        description="HTTP timeout in seconds.",
        gt=0,
        le=300,
    )
