"""Tests for the `skaha auth` CLI commands."""

from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from skaha.cli.auth import auth
from skaha.models.auth import OIDC, X509
from skaha.models.config import Configuration
from skaha.models.http import Server

runner = CliRunner()


def test_auth_list_no_config():
    """Test `skaha auth list` when no config file exists."""
    with patch("skaha.config.CONFIG_PATH", Path("/tmp/nonexistent_config.yaml")):
        result = runner.invoke(auth, ["list"])
        assert result.exit_code == 0
        assert "No contexts configured" in result.stdout


def test_auth_list_with_config(tmp_path):
    """Test `skaha auth list` with a valid config file."""
    config_path = tmp_path / "config.yaml"
    oidc_context = OIDC(
        server=Server(name="OIDC-Server", url="https://oidc.example.com", version="v1")
    )
    x509_context = X509(
        server=Server(name="X509-Server", url="https://x509.example.com", version="v0"),
        path=Path("/tmp/cert.pem"),
    )
    config = Configuration(
        active="X509-Server",
        contexts={"OIDC-Server": oidc_context, "X509-Server": x509_context},
    )

    with patch("skaha.config.CONFIG_PATH", config_path):
        config.save()
        result = runner.invoke(auth, ["list"])

    assert result.exit_code == 0
    assert "Available Authentication Contexts" in result.stdout
    assert "OIDC-Server" in result.stdout
    assert "X509-Server" in result.stdout
    # Check that the active context is marked correctly
    # This is a bit brittle, but checks for the checkmark in the right row
    assert "✅      │ X509-Server" in result.stdout
