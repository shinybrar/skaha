"""Comprehensive tests for the authentication configuration module."""

import time
from tempfile import NamedTemporaryFile

import pytest

from skaha.config.auth import (
    OIDC,
    X509,
    AuthConfig,
    OIDCClientConfig,
    OIDCTokenConfig,
    OIDCURLConfig,
)


class TestOIDCURLConfig:
    """Test OIDC URL configuration."""

    def test_default_values(self) -> None:
        """Test default values for OIDC URL configuration."""
        config = OIDCURLConfig()
        assert config.discovery is None
        assert config.device is None
        assert config.registration is None
        assert config.token is None

    def test_with_values(self) -> None:
        """Test OIDC URL configuration with values."""
        config = OIDCURLConfig(
            discovery="https://example.com/.well-known/openid-configuration",
            device="https://example.com/device",
            registration="https://example.com/register",
            token="https://example.com/token",  # nosec B106
        )
        assert (
            config.discovery == "https://example.com/.well-known/openid-configuration"
        )
        assert config.device == "https://example.com/device"
        assert config.registration == "https://example.com/register"
        assert config.token == "https://example.com/token"  # nosec B105


class TestOIDCClientConfig:
    """Test OIDC client configuration."""

    def test_default_values(self) -> None:
        """Test default values for OIDC client configuration."""
        config = OIDCClientConfig()
        assert config.identity is None
        assert config.secret is None

    def test_with_values(self) -> None:
        """Test OIDC client configuration with values."""
        config = OIDCClientConfig(
            identity="test_client_id",
            secret="test_client_secret",  # nosec B106
        )
        assert config.identity == "test_client_id"
        assert config.secret == "test_client_secret"  # nosec B105


class TestOIDCTokenConfig:
    """Test OIDC token configuration."""

    def test_default_values(self) -> None:
        """Test default values for OIDC token configuration."""
        config = OIDCTokenConfig()
        assert config.access is None
        assert config.refresh is None
        assert config.expiry is None

    def test_with_values(self) -> None:
        """Test OIDC token configuration with values."""
        future_time = time.time() + 3600
        config = OIDCTokenConfig(
            access="test_access_token",
            refresh="test_refresh_token",
            expiry=future_time,
        )
        assert config.access == "test_access_token"
        assert config.refresh == "test_refresh_token"
        assert config.expiry == future_time


class TestOIDC:
    """Test complete OIDC configuration."""

    def test_default_values(self) -> None:
        """Test default values for OIDC configuration."""
        config = OIDC()
        assert isinstance(config.endpoints, OIDCURLConfig)
        assert isinstance(config.client, OIDCClientConfig)
        assert isinstance(config.token, OIDCTokenConfig)

    def test_valid_with_missing_fields(self) -> None:
        """Test valid method with missing required fields."""
        config = OIDC()
        assert not config.valid()

    def test_valid_with_partial_fields(self) -> None:
        """Test valid method with some required fields missing."""
        config = OIDC()
        config.endpoints.discovery = (
            "https://example.com/.well-known/openid-configuration"
        )
        config.endpoints.token = "https://example.com/token"  # nosec B105
        config.client.identity = "test_client_id"
        # Missing client.secret, token.refresh, token.expiry
        assert not config.valid()

    def test_valid_with_all_required_fields(self) -> None:
        """Test valid method with all required fields present."""
        future_time = time.time() + 3600
        config = OIDC()
        config.endpoints.discovery = (
            "https://example.com/.well-known/openid-configuration"
        )
        config.endpoints.token = "https://example.com/token"  # nosec B105
        config.client.identity = "test_client_id"
        config.client.secret = "test_client_secret"  # nosec B105
        config.token.refresh = "test_refresh_token"
        config.token.expiry = future_time
        assert config.valid()

    def test_expired_no_access_token(self) -> None:
        """Test expired property when access token is None."""
        config = OIDC()
        assert config.expired is True

    def test_expired_no_expiry(self) -> None:
        """Test expired property when expiry is None."""
        config = OIDC()
        config.token.access = "test_access_token"
        assert config.expired is True

    def test_expired_token_expired(self) -> None:
        """Test expired property when token is expired."""
        past_time = time.time() - 3600
        config = OIDC()
        config.token.access = "test_access_token"
        config.token.expiry = past_time
        assert config.expired is True

    def test_expired_token_valid(self) -> None:
        """Test expired property when token is still valid."""
        future_time = time.time() + 3600
        config = OIDC()
        config.token.access = "test_access_token"
        config.token.expiry = future_time
        assert config.expired is False


class TestX509:
    """Test X.509 certificate configuration."""

    def test_default_values(self) -> None:
        """Test default values for X.509 configuration."""
        config = X509()
        assert config.path is None
        assert config.expiry is None

    def test_with_values(self) -> None:
        """Test X.509 configuration with values."""
        future_time = time.time() + 3600
        config = X509(
            path="/path/to/cert.pem",
            expiry=future_time,
        )
        assert config.path == "/path/to/cert.pem"
        assert config.expiry == future_time

    def test_valid_no_path(self) -> None:
        """Test valid method when path is None."""
        config = X509()
        assert not config.valid()

    def test_valid_path_not_exists(self) -> None:
        """Test valid method when path doesn't exist."""
        config = X509(path="/nonexistent/path/cert.pem")
        assert not config.valid()

    def test_valid_path_exists_no_expiry(self) -> None:
        """Test valid method when path exists but expiry is None."""
        with NamedTemporaryFile() as temp_file:
            config = X509(path=temp_file.name)
            assert not config.valid()

    def test_valid_path_exists_with_expiry(self) -> None:
        """Test valid method when path exists and expiry is set."""
        future_time = time.time() + 3600
        with NamedTemporaryFile() as temp_file:
            config = X509(path=temp_file.name, expiry=future_time)
            assert config.valid()

    def test_expired_no_expiry(self) -> None:
        """Test expired property when expiry is None."""
        config = X509()
        assert config.expired is True

    def test_expired_certificate_expired(self) -> None:
        """Test expired property when certificate is expired."""
        past_time = time.time() - 3600
        config = X509(expiry=past_time)
        assert config.expired is True

    def test_expired_certificate_valid(self) -> None:
        """Test expired property when certificate is still valid."""
        future_time = time.time() + 3600
        config = X509(expiry=future_time)
        assert config.expired is False


class TestAuthConfig:
    """Test authentication configuration."""

    def test_default_values(self) -> None:
        """Test that AuthConfig requires mode to be set."""
        with pytest.raises(ValueError, match="Field required"):
            AuthConfig()

    def test_with_oidc_mode(self) -> None:
        """Test AuthConfig with OIDC mode."""
        config = AuthConfig(mode="oidc")
        assert config.mode == "oidc"
        assert isinstance(config.oidc, OIDC)
        assert isinstance(config.x509, X509)

    def test_with_x509_mode(self) -> None:
        """Test AuthConfig with X.509 mode."""
        config = AuthConfig(mode="x509")
        assert config.mode == "x509"
        assert isinstance(config.oidc, OIDC)
        assert isinstance(config.x509, X509)

    def test_valid_oidc_mode_invalid_config(self) -> None:
        """Test valid method with OIDC mode but invalid OIDC configuration."""
        config = AuthConfig(mode="oidc")
        with pytest.raises(
            ValueError, match="OIDC mode selected but OIDC configuration is invalid"
        ):
            config.valid()

    def test_valid_x509_mode_invalid_config(self) -> None:
        """Test valid method with X.509 mode but invalid X.509 configuration."""
        config = AuthConfig(mode="x509")
        with pytest.raises(
            ValueError, match="X509 mode selected but X509 configuration is invalid"
        ):
            config.valid()

    def test_valid_oidc_mode_valid_config(self) -> None:
        """Test valid method with OIDC mode and valid OIDC configuration."""
        future_time = time.time() + 3600
        config = AuthConfig(mode="oidc")
        config.oidc.endpoints.discovery = (
            "https://example.com/.well-known/openid-configuration"
        )
        config.oidc.endpoints.token = "https://example.com/token"  # nosec B105
        config.oidc.client.identity = "test_client_id"
        config.oidc.client.secret = "test_client_secret"  # nosec B105
        config.oidc.token.refresh = "test_refresh_token"
        config.oidc.token.expiry = future_time
        assert config.valid() is True

    def test_valid_x509_mode_valid_config(self) -> None:
        """Test valid method with X.509 mode and valid X.509 configuration."""
        future_time = time.time() + 3600
        with NamedTemporaryFile() as temp_file:
            config = AuthConfig(mode="x509")
            config.x509.path = temp_file.name
            config.x509.expiry = future_time
            assert config.valid() is True

    def test_expired_oidc_mode(self) -> None:
        """Test expired method with OIDC mode."""
        config = AuthConfig(mode="oidc")
        # OIDC config is expired by default (no access token)
        assert config.expired() is True

        # Set valid access token
        future_time = time.time() + 3600
        config.oidc.token.access = "test_access_token"
        config.oidc.token.expiry = future_time
        assert config.expired() is False

    def test_expired_x509_mode(self) -> None:
        """Test expired method with X.509 mode."""
        config = AuthConfig(mode="x509")
        # X.509 config is expired by default (no expiry)
        assert config.expired() is True

        # Set valid expiry
        future_time = time.time() + 3600
        config.x509.expiry = future_time
        assert config.expired() is False

    def test_expired_unknown_mode(self) -> None:
        """Test expired method with unknown mode."""
        config = AuthConfig(mode="unknown")
        assert config.expired() is True
