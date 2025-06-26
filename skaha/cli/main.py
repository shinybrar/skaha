"""Command Line Interface for Science Platform."""

from __future__ import annotations

import typer
from rich.console import Console

from skaha.cli.auth import auth
from skaha.cli.config import config
from skaha.cli.version import version

console = Console()


def callback(ctx: typer.Context) -> None:
    """Main callback that handles no subcommand case."""
    if ctx.invoked_subcommand is None:
        # No subcommand was invoked, show help and exit cleanly
        console.print(ctx.get_help())
        raise typer.Exit(0)


cli: typer.Typer = typer.Typer(
    name="skaha",
    help="Command Line Interface for Science Platform.",
    no_args_is_help=False,  # Disable automatic help to handle manually
    add_completion=True,
    pretty_exceptions_show_locals=False,
    pretty_exceptions_enable=False,
    pretty_exceptions_short=True,
    epilog="For more information, visit https://shinybrar.github.io/skaha/latest/",
    rich_markup_mode="rich",
    rich_help_panel="Skaha CLI Commands",
    callback=callback,
    invoke_without_command=True,  # Allow callback to be called without subcommand
)

cli.add_typer(
    auth,
    name="auth",
    help="Authenticate with Science Platform",
    no_args_is_help=True,
    rich_help_panel="Core",
)

cli.add_typer(
    config,
    name="config",
    help="Manage configuration for client",
    no_args_is_help=True,
    rich_help_panel="Info",
)
cli.add_typer(
    version,
    name="version",
    help="View client info",
    no_args_is_help=False,
    rich_help_panel="Info",
)


def main() -> None:
    """Main entry point."""
    cli()


if __name__ == "__main__":
    main()
