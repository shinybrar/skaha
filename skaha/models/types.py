"""Common types and constants for Skaha API models.

This module contains type definitions and constants used across
the Skaha API client models.
"""

from __future__ import annotations

from typing import Annotated, Literal, TypeAlias

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from skaha import CONFIG_PATH
from skaha.models.auth import (
    AuthConfig,
)
from skaha.models.registry import ContainerRegistry

# Session type constants (new lowercase style)
Kind: TypeAlias = Literal["desktop", "notebook", "carta", "headless", "firefly"]
Status: TypeAlias = Literal["Pending", "Running", "Terminating", "Succeeded", "Error"]
View: TypeAlias = Literal["all"]


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


class Configuration(BaseSettings):
    """Configuration settings for Skaha."""

    auth: Annotated[
        AuthConfig,
        Field(default_factory=AuthConfig, description="Authentication Settings."),
    ]
    client: Annotated[
        ClientConfig,
        Field(default_factory=ClientConfig, description="Client Settings."),
    ]
    registry: Annotated[
        ContainerRegistry,
        Field(
            default_factory=ContainerRegistry,
            description="Container Registry Settings.",
        ),
    ]

    model_config = SettingsConfigDict(
        env_prefix="SKAHA_",
        env_nested_delimiter="__",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    @classmethod
    def assemble(cls, **kwargs: object) -> Configuration:
        """Assemble the configuration.

        Args:
            **kwargs: Runtime configuration overrides.

        Returns:
            Configuration: The assembled configuration object.

        Raises:
            FileNotFoundError: If the config file does not exist.
            OSError: If loading the config file fails.
            ValueError: If the config file is empty.
        """
        if not CONFIG_PATH.exists():
            msg = f"{CONFIG_PATH} does not exist."
            raise FileNotFoundError(msg)

        try:
            with CONFIG_PATH.open(encoding="utf-8") as filepath:
                data = yaml.safe_load(filepath)
                if not data:
                    msg = f"config {CONFIG_PATH} is empty."
                    raise ValueError(msg)
        except (OSError, yaml.YAMLError) as error:
            msg = f"failed to load config {CONFIG_PATH}: {error}"
            raise OSError(msg) from error

        merged: dict[str, object] = {**data, **kwargs}
        return cls.model_validate(merged)

    def save(self) -> None:
        """Save the current configuration to the configuration file."""
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)

        data = self.model_dump(mode="python")

        try:
            with CONFIG_PATH.open(mode="w", encoding="utf-8") as filepath:
                yaml.dump(
                    data, filepath, default_flow_style=False, sort_keys=True, indent=2
                )
        except Exception as error:
            msg = f"failed to save config {CONFIG_PATH}: {error}"
            raise OSError(msg) from error
