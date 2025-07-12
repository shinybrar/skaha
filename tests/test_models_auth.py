"""Comprehensive tests for the authentication configuration module."""

import math
import time
from pathlib import Path
from tempfile import NamedTemporaryFile

import pytest
from pydantic import ValidationError

from skaha.models.auth import (
    OIDC,
    X509,
    Authentication,
    Client,
    Endpoint,
    Expiry,
    Server,
    Token,
)


class TestOIDCURLConfig:
    """Test OIDC URL configuration."""

    def test_default_values(self) -> None:
        """Test default values for OIDC URL configuration."""
        config = Endpoint()
        assert config.discovery is None
        assert config.device is None
        assert config.registration is None
        assert config.token is None

    def test_with_values(self) -> None:
        """Test OIDC URL configuration with values."""
        config = Endpoint(
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
        config = Client()
        assert config.identity is None
        assert config.secret is None

    def test_with_values(self) -> None:
        """Test OIDC client configuration with values."""
        config = Client(
            identity="test_client_id",
            secret="test_client_secret",  # nosec B106
        )
        assert config.identity == "test_client_id"
        assert config.secret == "test_client_secret"  # nosec B105


class TestOIDCTokenConfig:
    """Test OIDC token configuration."""

    def test_default_values(self) -> None:
        """Test default values for OIDC token configuration."""
        config = Token()
        assert config.access is None
        assert config.refresh is None

    def test_with_values(self) -> None:
        """Test OIDC token configuration with values."""
        config = Token(
            access="test_access_token",
            refresh="test_refresh_token",
        )
        assert config.access == "test_access_token"
        assert config.refresh == "test_refresh_token"


class TestOIDCExpiryConfig:
    """Test OIDC expiry configuration."""

    def test_default_values(self) -> None:
        """Test default values for OIDC expiry configuration."""
        config = Expiry()
        assert config.access is None
        assert config.refresh is None

    def test_with_values(self) -> None:
        """Test OIDC expiry configuration with values."""
        future_time = time.time() + 3600
        config = Expiry(
            access=future_time,
            refresh=future_time + 3600,
        )
        assert config.access == future_time
        assert config.refresh == future_time + 3600


class TestOIDC:
    """Test complete OIDC configuration."""

    def test_default_values(self) -> None:
        """Test default values for OIDC configuration."""
        config = OIDC()
        assert isinstance(config.endpoints, Endpoint)
        assert isinstance(config.client, Client)
        assert isinstance(config.token, Token)
        assert isinstance(config.server, Server)
        assert isinstance(config.expiry, Expiry)

    def test_valid_with_missing_fields(self) -> None:
        """Test valid method with missing required fields."""
        config = OIDC()
        assert not config.valid

    def test_valid_with_partial_fields(self) -> None:
        """Test valid method with some required fields missing."""
        config = OIDC()
        config.endpoints.discovery = (
            "https://example.com/.well-known/openid-configuration"
        )
        config.endpoints.token = "https://example.com/token"  # nosec B105
        config.client.identity = "test_client_id"
        # Missing client.secret, token.refresh, token.expiry
        assert not config.valid

    def test_valid_with_all_required_fields(self) -> None:
        """Test valid method with all required fields present."""
        config = OIDC()
        config.endpoints.discovery = (
            "https://example.com/.well-known/openid-configuration"
        )
        config.endpoints.token = "https://example.com/token"  # nosec B105
        config.client.identity = "test_client_id"
        config.client.secret = "test_client_secret"  # nosec B105
        config.token.refresh = "test_refresh_token"
        assert config.valid

    def test_expired_no_access_token(self) -> None:
        """Test expired property when access token is None."""
        config = OIDC()
        assert config.expired is True

    def test_expired_no_expiry(self) -> None:
        """Test expired property when expiry is None."""
        config = OIDC()
        config.token.refresh = "test_refresh_token"
        assert config.expired is True

    def test_expired_token_expired(self) -> None:
        """Test expired property when token is expired."""
        past_time = time.time() - 3600
        config = OIDC()
        config.token.refresh = "test_refresh_token"
        config.expiry.refresh = past_time
        assert config.expired is True

    def test_expired_token_valid(self) -> None:
        """Test expired property when token is still valid."""
        future_time = time.time() + 3600
        config = OIDC()
        config.token.access = "test_refresh_token"
        config.expiry.access = future_time
        assert config.expired is False


class TestX509:
    """Test X.509 certificate configuration."""

    def test_default_values(self) -> None:
        """Test default values for X.509 configuration."""
        config = X509()
        assert config.path is None
        assert math.isclose(config.expiry, 0.0, abs_tol=1e-9)

    def test_with_values(self) -> None:
        """Test X.509 configuration with values."""
        future_time = time.time() + 3600
        config = X509(
            path="/path/to/cert.pem",
            expiry=future_time,
        )
        assert str(config.path) == "/path/to/cert.pem"
        assert config.expiry == future_time

    def test_valid_no_path(self) -> None:
        """Test valid method when path is None."""
        config = X509()
        assert not config.valid

    def test_valid_path_exists_no_expiry(self) -> None:
        """Test valid method when path exists but expiry is default."""
        with NamedTemporaryFile() as temp_file:
            config = X509(path=Path(temp_file.name))
            assert config.valid  # Should be valid if file exists

    def test_valid_path_exists_with_expiry(self) -> None:
        """Test valid method when path exists and expiry is set."""
        future_time = time.time() + 3600
        with NamedTemporaryFile() as temp_file:
            config = X509(path=Path(temp_file.name), expiry=future_time)
            assert config.valid

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
        """Test that AuthConfig can be instantiated with default values."""
        config = Authentication()
        assert config.mode == "default"
        assert isinstance(config.oidc, OIDC)
        assert isinstance(config.x509, X509)
        assert isinstance(config.default, X509)

    def test_with_oidc_mode(self) -> None:
        """Test AuthConfig with OIDC mode."""
        config = Authentication(mode="oidc")
        assert config.mode == "oidc"

    def test_with_x509_mode(self) -> None:
        """Test AuthConfig with X.509 mode."""
        config = Authentication(mode="x509")
        assert config.mode == "x509"

    def test_valid_oidc_mode_invalid_config(self) -> None:
        """Test valid method with OIDC mode but invalid OIDC configuration."""
        config = Authentication(mode="oidc")
        assert config.valid is False

    def test_valid_x509_mode_invalid_config(self) -> None:
        """Test valid method with X.509 mode but invalid X.509 configuration."""
        config = Authentication(mode="x509")
        assert config.valid is False

    def test_valid_oidc_mode_valid_config(self) -> None:
        """Test valid method with OIDC mode and valid OIDC configuration."""
        config = Authentication(mode="oidc")
        config.oidc.endpoints.discovery = (
            "https://example.com/.well-known/openid-configuration"
        )
        config.oidc.endpoints.token = "https://example.com/token"  # nosec B105
        config.oidc.client.identity = "test_client_id"
        config.oidc.client.secret = "test_client_secret"  # nosec B105
        config.oidc.token.refresh = "test_refresh_token"
        assert config.valid is True

    def test_valid_x509_mode_valid_config(self) -> None:
        """Test valid method with X.509 mode and valid X.509 configuration."""
        future_time = time.time() + 3600
        with NamedTemporaryFile() as temp_file:
            config = Authentication(mode="x509")
            config.x509.path = Path(temp_file.name)
            config.x509.expiry = future_time
            assert config.valid is True

    def test_expired_oidc_mode(self) -> None:
        """Test expired method with OIDC mode."""
        config = Authentication(mode="oidc")
        # OIDC config is expired by default (no refresh token)
        assert config.expired is True

        # Set valid refresh token
        future_time = time.time() + 3600
        config.oidc.token.access = "test_refresh_token"
        config.oidc.expiry.access = future_time
        assert config.expired is False

    def test_expired_x509_mode(self) -> None:
        """Test expired method with X.509 mode."""
        config = Authentication(mode="x509")
        # X.509 config is expired by default (no expiry)
        assert config.expired is True

        # Set valid expiry
        future_time = time.time() + 3600
        config.x509.expiry = future_time
        assert config.expired is False

    def test_expired_unknown_mode(self) -> None:
        """Test expired method with unknown mode."""
        with pytest.raises(ValidationError):
            Authentication(mode="unknown")


class TestServerInfo:
    """Test server information configuration."""

    def test_default_values(self) -> None:
        """Test default values for ServerInfo."""
        server = Server()
        assert server.name is None
        assert server.uri is None
        assert server.url is None

    def test_with_values(self) -> None:
        """Test ServerInfo with custom values."""
        server = Server(
            name="Test Server",
            uri="ivo://test.example.com/skaha",
            url="https://test.example.com/skaha",
        )
        assert server.name == "Test Server"
        assert str(server.uri) == "ivo://test.example.com/skaha"
        assert str(server.url) == "https://test.example.com/skaha"

    def test_partial_values(self) -> None:
        """Test ServerInfo with partial values."""
        server = Server(name="Test Server")
        assert server.name == "Test Server"
        assert server.uri is None
        assert server.url is None


class TestOIDCWithServer:
    """Test OIDC configuration with server information."""

    def test_default_server_field(self) -> None:
        """Test that OIDC has a default server field."""
        oidc = OIDC()
        assert isinstance(oidc.server, Server)
        assert oidc.server.name is None
        assert oidc.server.uri is None
        assert oidc.server.url is None

    def test_with_server_info(self) -> None:
        """Test OIDC with server information."""
        server_info = Server(
            name="Canada",
            uri="ivo://canfar.net/src/skaha",
            url="https://ws-uv.canfar.net/skaha",
        )
        oidc = OIDC(server=server_info)
        assert oidc.server.name == "Canada"
        assert str(oidc.server.uri) == "ivo://canfar.net/src/skaha"
        assert str(oidc.server.url) == "https://ws-uv.canfar.net/skaha"

    def test_server_field_serialization(self) -> None:
        """Test that OIDC server field is properly serialized."""
        server_info = Server(
            name="Test Server",
            uri="ivo://test.example.com/skaha",
            url="https://test.example.com/skaha",
        )
        oidc = OIDC(server=server_info)

        # Test model dump includes server field
        data = oidc.model_dump()
        assert "server" in data
        assert data["server"]["name"] == "Test Server"
        assert str(data["server"]["uri"]) == "ivo://test.example.com/skaha"
        assert str(data["server"]["url"]) == "https://test.example.com/skaha"


class TestX509WithServer:
    """Test X509 configuration with server information."""

    def test_default_server_field(self) -> None:
        """Test that X509 has a default server field."""
        x509 = X509()
        assert x509.server is None

    def test_with_server_info(self) -> None:
        """Test X509 with server information."""
        from pydantic import AnyHttpUrl, AnyUrl

        server_info = Server(
            name="CANFAR",
            uri=AnyUrl("ivo://cadc.nrc.ca/skaha"),
            url=AnyHttpUrl("https://ws-uv.canfar.net/skaha"),
        )
        x509 = X509(server=server_info)
        assert x509.server.name == "CANFAR"
        assert str(x509.server.uri) == "ivo://cadc.nrc.ca/skaha"
        assert str(x509.server.url) == "https://ws-uv.canfar.net/skaha"

    def test_server_field_serialization(self) -> None:
        """Test that X509 server field is properly serialized."""
        from pydantic import AnyHttpUrl, AnyUrl

        server_info = Server(
            name="Test Server",
            uri=AnyUrl("ivo://test.example.com/skaha"),
            url=AnyHttpUrl("https://test.example.com/skaha"),
        )
        x509 = X509(server=server_info)

        # Test model dump includes server field
        data = x509.model_dump()
        assert "server" in data
        assert data["server"]["name"] == "Test Server"
        assert str(data["server"]["uri"]) == "ivo://test.example.com/skaha"
        assert str(data["server"]["url"]) == "https://test.example.com/skaha"


class TestAuthConfigWithMethodSpecificServers:
    """Test authentication configuration with method-specific server information."""

    def test_oidc_server_access(self) -> None:
        """Test accessing server info through OIDC method."""
        from pydantic import AnyHttpUrl, AnyUrl

        server_info = Server(
            name="Test OIDC Server",
            uri=AnyUrl("ivo://test.example.com/skaha"),
            url=AnyHttpUrl("https://test.example.com/skaha"),
        )
        config = Authentication(mode="oidc")
        config.oidc.server = server_info

        assert config.oidc.server.name == "Test OIDC Server"
        assert str(config.oidc.server.uri) == "ivo://test.example.com/skaha"
        assert str(config.oidc.server.url) == "https://test.example.com/skaha"

    def test_x509_server_access(self) -> None:
        """Test accessing server info through X509 method."""
        from pydantic import AnyHttpUrl, AnyUrl

        server_info = Server(
            name="Test X509 Server",
            uri=AnyUrl("ivo://cadc.nrc.ca/skaha"),
            url=AnyHttpUrl("https://ws-uv.canfar.net/skaha"),
        )
        config = Authentication(mode="x509")
        config.x509.server = server_info

        assert config.x509.server.name == "Test X509 Server"
        assert str(config.x509.server.uri) == "ivo://cadc.nrc.ca/skaha"
        assert str(config.x509.server.url) == "https://ws-uv.canfar.net/skaha"

    def test_both_methods_with_different_servers(self) -> None:
        """Test that both auth methods can have different server info."""
        from pydantic import AnyHttpUrl, AnyUrl

        oidc_server = Server(
            name="OIDC Server",
            uri=AnyUrl("ivo://oidc.example.com/skaha"),
            url=AnyHttpUrl("https://oidc.example.com/skaha"),
        )
        x509_server = Server(
            name="X509 Server",
            uri=AnyUrl("ivo://x509.example.com/skaha"),
            url=AnyHttpUrl("https://x509.example.com/skaha"),
        )

        config = Authentication()
        config.oidc.server = oidc_server
        config.x509.server = x509_server

        # Verify both servers are stored independently
        assert config.oidc.server.name == "OIDC Server"
        assert str(config.oidc.server.url) == "https://oidc.example.com/skaha"
        assert config.x509.server.name == "X509 Server"
        assert str(config.x509.server.url) == "https://x509.example.com/skaha"
