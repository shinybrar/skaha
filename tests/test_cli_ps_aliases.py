"""Tests for ps command aliases (ls, list)."""

from __future__ import annotations

import pytest
from typer.testing import CliRunner

from skaha.cli.main import cli


class TestPsAliases:
    """Test cases for ps command aliases."""

    @pytest.fixture
    def runner(self) -> CliRunner:
        """Create a CLI test runner."""
        return CliRunner()

    def test_ps_command_help(self, runner: CliRunner) -> None:
        """Test that ps command shows help correctly."""
        result = runner.invoke(cli, ["ps", "--help"])
        assert result.exit_code == 0
        assert "Show running sessions" in result.stdout
        assert "Usage: skaha ps" in result.stdout

    def test_ls_alias_help(self, runner: CliRunner) -> None:
        """Test that ls alias shows help correctly."""
        result = runner.invoke(cli, ["ls", "--help"])
        assert result.exit_code == 0
        assert "Show running sessions" in result.stdout
        assert "Usage: skaha ls" in result.stdout

    def test_list_alias_help(self, runner: CliRunner) -> None:
        """Test that list alias shows help correctly."""
        result = runner.invoke(cli, ["list", "--help"])
        assert result.exit_code == 0
        assert "Show running sessions" in result.stdout
        assert "Usage: skaha list" in result.stdout

    def test_main_help_shows_aliases(self, runner: CliRunner) -> None:
        """Test that main help shows all aliases."""
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "ps | ls | list" in result.stdout
        assert "Show running sessions" in result.stdout

    def test_all_aliases_have_same_options(self, runner: CliRunner) -> None:
        """Test that all aliases have the same command options."""
        commands = ["ps", "ls", "list"]

        for cmd in commands:
            result = runner.invoke(cli, [cmd, "--help"])
            assert result.exit_code == 0
            # All help outputs should contain the same options
            assert "--all" in result.stdout
            assert "--quiet" in result.stdout
            assert "--kind" in result.stdout
            assert "--status" in result.stdout
            assert "--debug" in result.stdout
            assert "Show running sessions" in result.stdout
