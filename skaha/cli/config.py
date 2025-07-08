"""Configuration Management."""

from __future__ import annotations

from typing import Annotated

import typer
from rich.console import Console

from skaha import CONFIG_PATH
from skaha.hooks.typer.aliases import AliasGroup
from skaha.models.config import Configuration

config: typer.Typer = typer.Typer(
    cls=AliasGroup,
)
console = Console(width=120)


@config.command("show | list | ls")
def show(
    defaults: Annotated[
        bool,
        typer.Option(
            "--defaults",
            "-d",
            help="Show default configuration",
        ),
    ] = False,
) -> None:
    """Displays the current configuration."""
    try:
        cfg = Configuration.assemble()
        console.print(CONFIG_PATH)
        console.print(
            cfg.model_dump(
                mode="python", exclude_none=True, exclude_defaults=(not defaults)
            )
        )
    except (FileNotFoundError, OSError, ValueError):
        console.print("[yellow italic]No local configuration found.[/yellow italic]")
        if not defaults:
            console.print("[dim]Use --defaults to show default configuration.[/dim]")
            return
        console.print("[dim]Default Client Configuration[/dim]")
        cfg = Configuration()
        console.print(cfg.model_dump(mode="python", exclude_none=True))
        return
    except Exception as error:
        console.print(f"[bold red]Error: {error}[/bold red]")
        raise typer.Exit(1) from error
