"""Skaha Client Configuration."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Annotated

import yaml
from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from skaha import CONFIG_PATH
from skaha.models.auth import Authentication
from skaha.models.http import Connection
from skaha.models.registry import ContainerRegistry


class Configuration(Connection, BaseSettings):
    """Unified configuration settings for Skaha client and authentication."""

    model_config = SettingsConfigDict(
        title="Skaha Configuration",
        env_prefix="SKAHA_",
        env_nested_delimiter="__",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="forbid",
        json_schema_mode_override="serialization",
        str_strip_whitespace=True,
        str_max_length=256,
        str_min_length=1,
    )
    certificate: Path | None = Field(
        default=None,
        title="X509 TLS Certificate",
        description="Pathlike location for the x509 certificate.",
        examples=[Path.home() / ".custom" / "cert.pem"],
        validate_default=False,
    )
    token: SecretStr | None = Field(
        default=None,
        title="Authentication Token",
        description="Bearer token for the server.",
        exclude=True,
        validate_default=False,
    )
    auth: Annotated[
        Authentication,
        Field(
            default_factory=lambda: Authentication(),
            description="Authentication Settings.",
        ),
    ]
    registry: Annotated[
        ContainerRegistry,
        Field(
            default_factory=lambda: ContainerRegistry(),
            description="Container Registry Settings.",
        ),
    ]
    loglevel: int = Field(
        default=logging.INFO,
        title="Logging Level",
        description="10=DEBUG, 20=INFO, 30=WARNING, 40=ERROR, 50=CRITICAL",
        le=50,
        ge=10,
    )

    @property
    def url(self) -> str:
        """Return the URL for the server.

        Returns:
            str | None: The URL for the server.
        """
        mode = self.auth.mode
        return str(getattr(self.auth, mode).server.url)

    @property
    def uri(self) -> str:
        """Return the URI for the server.

        Returns:
            str | None: The URI for the server.
        """
        mode = self.auth.mode
        return str(getattr(self.auth, mode).server.uri)

    @property
    def name(self) -> str:
        """Return the name for the server.

        Returns:
            str | None: The name for the server.
        """
        mode = self.auth.mode
        return str(getattr(self.auth, mode).server.name)

    @property
    def version(self) -> str:
        """Return the version for the server.

        Returns:
            str | None: The version for the server.
        """
        mode = self.auth.mode
        return str(getattr(self.auth, mode).server.version)

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

        data = self.model_dump(mode="json", exclude_defaults=True)

        try:
            with CONFIG_PATH.open(mode="w", encoding="utf-8") as filepath:
                yaml.dump(
                    data, filepath, default_flow_style=False, sort_keys=True, indent=2
                )
        except Exception as error:
            msg = f"failed to save config {CONFIG_PATH}: {error}"
            raise OSError(msg) from error
