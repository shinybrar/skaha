"""Simple tests for config/client and config/config modules."""

import tempfile
import yaml
from pathlib import Path
from unittest.mock import patch

import pytest

from skaha.config.client import ClientConfig, RegistryConfig
from skaha.config.config import Configuration


def test_client_config_instantiation() -> None:
    """Test that ClientConfig can be instantiated with defaults."""
    config = ClientConfig()
    assert config.url is None
    assert config.version is None
    assert config.concurrency == 10
    assert config.timeout == 30


def test_client_config_with_values() -> None:
    """Test that ClientConfig can be instantiated with custom values."""
    config = ClientConfig(
        url="https://example.com",
        version="v1",
        concurrency=5,
        timeout=60
    )
    assert str(config.url) == "https://example.com/"
    assert config.version == "v1"
    assert config.concurrency == 5
    assert config.timeout == 60


def test_registry_config_instantiation() -> None:
    """Test that RegistryConfig can be instantiated with defaults."""
    config = RegistryConfig()
    assert config.url is None
    assert config.username is None
    assert config.secret is None


def test_registry_config_with_values() -> None:
    """Test that RegistryConfig can be instantiated with custom values."""
    config = RegistryConfig(
        url="https://registry.example.com",
        username="testuser",
        secret="testsecret"
    )
    assert str(config.url) == "https://registry.example.com/"
    assert config.username == "testuser"
    assert config.secret == "testsecret"


def test_configuration_instantiation() -> None:
    """Test that Configuration can be instantiated with defaults."""
    # Configuration requires auth mode to be set
    config = Configuration.model_validate({"auth": {"mode": "x509"}})
    assert config.auth is not None
    assert config.client is not None
    assert config.registry is not None


def test_configuration_with_custom_values() -> None:
    """Test that Configuration can be instantiated with custom values."""
    config_data = {
        "auth": {"mode": "x509"},
        "client": {"url": "https://example.com", "timeout": 45},
        "registry": {"username": "testuser"}
    }
    config = Configuration.model_validate(config_data)
    assert str(config.client.url) == "https://example.com/"
    assert config.client.timeout == 45
    assert config.registry.username == "testuser"


def test_configuration_save() -> None:
    """Test that Configuration can be saved to a file."""
    config_data = {
        "auth": {"mode": "x509"},
        "client": {"url": "https://example.com", "timeout": 45},
        "registry": {"username": "testuser", "secret": "testsecret"}
    }
    config = Configuration.model_validate(config_data)

    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as temp_file:
        temp_path = Path(temp_file.name)

    # Mock CONFIG_PATH to use our temp file
    with patch('skaha.config.config.CONFIG_PATH', temp_path):
        config.save()

        # Verify the file was created and contains expected data
        assert temp_path.exists()

        # Read the raw content to verify it was saved
        with temp_path.open(encoding='utf-8') as f:
            content = f.read()

        # Basic checks that the content contains our data
        assert 'mode: x509' in content
        assert 'timeout: 45' in content
        assert 'username: testuser' in content
        assert 'secret: testsecret' in content

    # Clean up
    temp_path.unlink()


def test_configuration_assemble() -> None:
    """Test that Configuration can be assembled from a config file."""
    # Create a temporary config file
    config_data = {
        'auth': {'mode': 'x509'},
        'client': {'url': 'https://test.example.com', 'timeout': 60},
        'registry': {'username': 'assembleuser'}
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as temp_file:
        yaml.dump(config_data, temp_file)
        temp_path = Path(temp_file.name)
    
    # Mock CONFIG_PATH to use our temp file
    with patch('skaha.config.config.CONFIG_PATH', temp_path):
        config = Configuration.assemble()
        
        assert config.auth.mode == 'x509'
        assert str(config.client.url) == 'https://test.example.com/'
        assert config.client.timeout == 60
        assert config.registry.username == 'assembleuser'
    
    # Clean up
    temp_path.unlink()


def test_configuration_assemble_with_overrides() -> None:
    """Test that Configuration.assemble works with runtime overrides."""
    # Create a temporary config file
    config_data = {
        'auth': {'mode': 'x509'},
        'client': {'url': 'https://test.example.com', 'timeout': 60}
    }

    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as temp_file:
        yaml.dump(config_data, temp_file)
        temp_path = Path(temp_file.name)

    # Mock CONFIG_PATH to use our temp file
    with patch('skaha.config.config.CONFIG_PATH', temp_path):
        config = Configuration.assemble(
            client={'timeout': 90},
            registry={'username': 'overrideuser'}
        )

        assert config.auth.mode == 'x509'
        # The override replaces the entire client section, so URL is lost
        # This is the expected behavior based on how dict merging works
        assert config.client.url is None  # URL not preserved when overriding client
        assert config.client.timeout == 90  # Override applied
        assert config.registry.username == 'overrideuser'  # Override applied

    # Clean up
    temp_path.unlink()


def test_configuration_assemble_file_not_found() -> None:
    """Test that Configuration.assemble raises FileNotFoundError when config file doesn't exist."""
    non_existent_path = Path('/nonexistent/config.yaml')
    
    with patch('skaha.config.config.CONFIG_PATH', non_existent_path):
        with pytest.raises(FileNotFoundError, match="does not exist"):
            Configuration.assemble()


def test_configuration_assemble_empty_file() -> None:
    """Test that Configuration.assemble raises ValueError when config file is empty."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as temp_file:
        # Write empty content
        temp_file.write("")
        temp_path = Path(temp_file.name)
    
    with patch('skaha.config.config.CONFIG_PATH', temp_path):
        with pytest.raises(ValueError, match="is empty"):
            Configuration.assemble()
    
    # Clean up
    temp_path.unlink()
