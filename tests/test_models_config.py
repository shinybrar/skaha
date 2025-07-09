"""Comprehensive tests for the configuration module."""

import logging
import tempfile
import yaml
from pathlib import Path
from unittest.mock import patch, mock_open

import pytest
from pydantic import SecretStr, ValidationError

from skaha.models.config import Configuration
from skaha.models.auth import Authentication
from skaha.models.http import Connection
from skaha.models.registry import ContainerRegistry


class TestConfiguration:
    """Test Configuration class."""

    def test_default_values(self) -> None:
        """Test default values for Configuration."""
        config = Configuration()
        assert config.certificate is None
        assert config.token is None
        assert isinstance(config.auth, Authentication)
        assert isinstance(config.registry, ContainerRegistry)
        assert config.loglevel == logging.INFO
        assert config.concurrency == 32  # from Connection
        assert config.timeout == 30  # from Connection

    def test_with_values(self) -> None:
        """Test Configuration with custom values."""
        cert_path = Path("/path/to/cert.pem")
        token = SecretStr("test_token")
        
        config = Configuration(
            certificate=cert_path,
            token=token,
            loglevel=logging.DEBUG,
            concurrency=64,
            timeout=60,
        )
        
        assert config.certificate == cert_path
        assert config.token == token
        assert config.loglevel == logging.DEBUG
        assert config.concurrency == 64
        assert config.timeout == 60

    def test_inheritance_from_connection(self) -> None:
        """Test that Configuration inherits from Connection."""
        config = Configuration()
        assert isinstance(config, Connection)
        assert hasattr(config, "concurrency")
        assert hasattr(config, "timeout")

    def test_loglevel_validation(self) -> None:
        """Test loglevel field validation."""
        # Valid values
        config = Configuration(loglevel=10)  # DEBUG
        assert config.loglevel == 10
        
        config = Configuration(loglevel=50)  # CRITICAL
        assert config.loglevel == 50
        
        # Invalid values
        with pytest.raises(ValidationError):
            Configuration(loglevel=5)  # Too low
            
        with pytest.raises(ValidationError):
            Configuration(loglevel=60)  # Too high

    def test_url_property(self) -> None:
        """Test url property."""
        from skaha.models.http import Server

        config = Configuration()
        # Set up auth mode and server
        config.auth.mode = "x509"
        config.auth.x509.server = Server(url="https://example.com/skaha")

        assert config.url == "https://example.com/skaha"

    def test_uri_property(self) -> None:
        """Test uri property."""
        config = Configuration()
        # Set up auth mode and server
        config.auth.mode = "oidc"
        config.auth.oidc.server.uri = "ivo://example.com/skaha"
        
        assert config.uri == "ivo://example.com/skaha"

    def test_name_property(self) -> None:
        """Test name property."""
        from skaha.models.http import Server

        config = Configuration()
        # Set up auth mode and server
        config.auth.mode = "x509"
        config.auth.x509.server = Server(name="Test Server")

        assert config.name == "Test Server"

    def test_version_property(self) -> None:
        """Test version property."""
        config = Configuration()
        # Set up auth mode and server
        config.auth.mode = "oidc"
        config.auth.oidc.server.version = "v1"
        
        assert config.version == "v1"

    def test_assemble_file_not_found(self) -> None:
        """Test assemble method when config file doesn't exist."""
        with patch("skaha.models.config.CONFIG_PATH") as mock_path:
            mock_path.exists.return_value = False

            with pytest.raises(FileNotFoundError, match="does not exist"):
                Configuration.assemble()

    def test_assemble_empty_file(self) -> None:
        """Test assemble method with empty config file."""
        with patch("skaha.models.config.CONFIG_PATH") as mock_path:
            mock_path.exists.return_value = True
            mock_path.open.return_value.__enter__.return_value = mock_open(read_data="").return_value

            with pytest.raises(ValueError, match="config .* is empty"):
                Configuration.assemble()

    def test_assemble_invalid_yaml(self) -> None:
        """Test assemble method with invalid YAML."""
        with patch("skaha.models.config.CONFIG_PATH") as mock_path:
            mock_path.exists.return_value = True
            mock_path.open.return_value.__enter__.return_value = mock_open(read_data="invalid: yaml: content:").return_value

            with pytest.raises(OSError, match="failed to load config"):
                Configuration.assemble()

    def test_assemble_valid_config(self) -> None:
        """Test assemble method with valid config."""
        config_data = {
            "loglevel": 10,
            "concurrency": 16,
            "auth": {"mode": "x509"}
        }
        
        with patch("skaha.models.config.CONFIG_PATH") as mock_path:
            mock_path.exists.return_value = True
            mock_path.open.return_value.__enter__.return_value = mock_open(read_data=yaml.dump(config_data)).return_value
            
            config = Configuration.assemble()
            assert config.loglevel == 10
            assert config.concurrency == 16
            assert config.auth.mode == "x509"

    def test_assemble_with_kwargs_override(self) -> None:
        """Test assemble method with runtime overrides."""
        config_data = {"loglevel": 20}
        
        with patch("skaha.models.config.CONFIG_PATH") as mock_path:
            mock_path.exists.return_value = True
            mock_path.open.return_value.__enter__.return_value = mock_open(read_data=yaml.dump(config_data)).return_value
            
            config = Configuration.assemble(loglevel=30, concurrency=8)
            assert config.loglevel == 30  # overridden
            assert config.concurrency == 8  # overridden

    def test_save_method(self) -> None:
        """Test save method."""
        config = Configuration(loglevel=logging.DEBUG, concurrency=16)
        
        with patch("skaha.models.config.CONFIG_PATH") as mock_path:
            mock_path.parent.mkdir = lambda parents=True, exist_ok=True: None
            mock_file = mock_open()
            mock_path.open.return_value.__enter__.return_value = mock_file.return_value
            
            config.save()
            
            # Verify file was opened for writing
            mock_path.open.assert_called_once_with(mode="w", encoding="utf-8")
            # Verify yaml.dump was called (indirectly through write calls)
            assert mock_file.return_value.write.called

    def test_save_method_error(self) -> None:
        """Test save method with write error."""
        config = Configuration()

        with patch("skaha.models.config.CONFIG_PATH") as mock_path:
            mock_path.parent.mkdir = lambda parents=True, exist_ok=True: None
            mock_path.open.side_effect = OSError("Write failed")

            with pytest.raises(OSError, match="failed to save config"):
                config.save()

    def test_model_config_settings(self) -> None:
        """Test model configuration settings."""
        config = Configuration()
        
        # Test that extra fields are forbidden
        with pytest.raises(ValidationError):
            Configuration(invalid_field="value")
        
        # Test string stripping and length validation
        with pytest.raises(ValidationError):
            Configuration(certificate="")  # Empty string should fail min_length

    def test_token_field_exclusion(self) -> None:
        """Test that token field is excluded from serialization."""
        config = Configuration(token=SecretStr("secret_token"))
        
        # Token should be excluded from model dump
        data = config.model_dump()
        assert "token" not in data
        
        # But should be accessible directly
        assert config.token.get_secret_value() == "secret_token"
