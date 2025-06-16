"""Skaha Authentication Configuration Module."""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings


class OIDCURLConfig(BaseModel):
    """OIDC URL configuration."""

    discovery: str | None = Field(default=None, description="OIDC discovery URL")
    device: str | None = Field(
        default=None, description="OIDC device authorization URL"
    )
    registration: str | None = Field(
        default=None, description="OIDC client registration URL"
    )
    token: str | None = Field(default=None, description="OIDC token endpoint URL")


class OIDCClientConfig(BaseModel):
    """OIDC client configuration."""

    identity: str | None = Field(default=None, description="OIDC client ID")
    secret: str | None = Field(default=None, description="OIDC client secret")


class OIDCTokenConfig(BaseModel):
    """OIDC token configuration."""

    access: str | None = Field(default=None, description="Access token")
    refresh: str | None = Field(default=None, description="Refresh token")
    expiry: float | None = Field(default=None, description="Token expiry ctime")


class OIDC(BaseModel):
    """Complete OIDC configuration."""

    url: OIDCURLConfig = Field(default_factory=OIDCURLConfig, description="OIDC URLs")
    client: OIDCClientConfig = Field(
        default_factory=OIDCClientConfig, description="OIDC client credentials"
    )
    token: OIDCTokenConfig = Field(
        default_factory=OIDCTokenConfig, description="OIDC tokens"
    )


class X509(BaseModel):
    """X.509 certificate configuration."""

    username: str | None = Field(default=None, description="Username for certificate")
    days: int | None = Field(default=None, description="Days certificate is valid for")
    path: str | None = Field(default=None, description="Path to PEM certificate file")
    expiry: float | None = Field(default=None, description="Certificate expiry ctime")


class AuthConfig(BaseSettings):
    """Authentication configuration."""

    mode: str = Field(default_factory=str, description="Authentication mode")
    oidc: OIDC = Field(default_factory=OIDC, description="OIDC settings")
    x509: X509 = Field(default_factory=X509, description="X.509 certificate settings")

    @field_validator("mode")
    @classmethod
    def _check_mode(cls, value: str | None) -> str | None:
        """Validate mode.

        Args:
            value (str | None): Value to validate.

        Returns:
            str | None: Validated value.
        """
        if value is not None and value not in {"oidc", "x509"}:
            msg = "mode must be either oidc or x509."
            raise ValueError(msg)
        return value
