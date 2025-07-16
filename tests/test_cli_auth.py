"""Tests for the refactored auth CLI commands."""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import Mock, patch

import pytest
from typer.testing import CliRunner

from skaha.cli.auth import auth
from skaha.models.auth import OIDC, X509
from skaha.models.registry import Server as RegistryServer

if TYPE_CHECKING:
    from pathlib import Path


class TestAuthCLI:
    """Test cases for the auth CLI functionality."""

    @pytest.fixture
    def runner(self) -> CliRunner:
        """Create a CLI test runner."""
        return CliRunner()

    @pytest.fixture
    def mock_config_path(self, tmp_path: Path):
        """Mock CONFIG_PATH to use a temporary directory."""
        config_path = tmp_path / "config.yaml"
        with patch("skaha.cli.auth.CONFIG_PATH", config_path):
            yield config_path

    def test_logout_with_existing_config(
        self, runner: CliRunner, mock_config_path: Path
    ) -> None:
        """Test logout command when config file exists."""
        # Create a config file
        mock_config_path.write_text("test: config")

        result = runner.invoke(auth, ["logout", "--yes"])

        assert result.exit_code == 0
        assert "Authentication credentials cleared" in result.stdout
        assert not mock_config_path.exists()

    def test_logout_with_no_config(
        self, runner: CliRunner, mock_config_path: Path
    ) -> None:
        """Test logout command when no config file exists."""
        result = runner.invoke(auth, ["logout", "--yes"])

        assert result.exit_code == 0
        assert "No configuration found to clear" in result.stdout

    def test_logout_cancelled(self, runner: CliRunner, mock_config_path: Path) -> None:
        """Test logout command when user cancels."""
        result = runner.invoke(auth, ["logout"], input="n\n")

        assert result.exit_code == 0
        assert "Logout cancelled" in result.stdout

    @patch("skaha.cli.auth.Configuration")
    def test_login_with_valid_credentials(
        self, mock_config_class, runner: CliRunner
    ) -> None:
        """Test login command when valid credentials exist."""
        # Mock configuration with valid, non-expired context
        mock_config = Mock()
        mock_config.context.expired = False
        mock_config.context.server.name = "Test Server"
        mock_config.context.server.url = "https://test.example.com"
        mock_config_class.return_value = mock_config

        result = runner.invoke(auth, ["login"])

        assert result.exit_code == 0
        assert "Credentials valid" in result.stdout
        assert "Test Server" in result.stdout
