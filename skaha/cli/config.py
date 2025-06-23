"""Configuration Management."""

from __future__ import annotations

import typer
from rich.console import Console
from yaml import dump

from skaha import CONFIG_PATH
from skaha.config.config import Configuration
from skaha.hooks.typer.aliases import AliasGroup

config: typer.Typer = typer.Typer(
    cls=AliasGroup,
)
console = Console()


@config.command("show | list | ls")
def show() -> None:
    """Displays the current configuration."""
    cfg = Configuration.assemble()
    console.print(CONFIG_PATH)
    console.print(
        dump(
            cfg.model_dump(mode="python", exclude_none=False, exclude_unset=False),
        )
    )
