"""CLI command to prune Skaha sessions."""

from __future__ import annotations

import asyncio
from typing import Annotated

import typer
from rich.console import Console

from skaha.session import AsyncSession

console = Console()

prune = typer.Typer(
    name="prune",
    help="Prune sessions based on specified criteria.",
    no_args_is_help=True,
)


@prune.callback(invoke_without_command=True)
def prune_sessions(
    name: Annotated[
        str,
        typer.Argument(
            ...,
            help="Prefix to match session names.",
            metavar="NAME",
        ),
    ],
    kind: Annotated[
        str | None,
        typer.Argument(help="Filter by session kind."),
    ] = None,
    status: Annotated[
        str | None,
        typer.Argument(help="Filter by session status."),
    ] = None,
    debug: Annotated[
        bool,
        typer.Option("--debug", help="Enable debug logging."),
    ] = False,
) -> None:
    """Prune Skaha sessions based on name, kind, or status."""
    if not any([name, kind, status]):
        console.print(
            "[bold red]Error:[/bold red] At least one filter (--name, --kind, or --status) must be provided."
        )
        raise typer.Exit(1)

    async def _prune() -> None:
        log_level = "DEBUG" if debug else "INFO"
        async with AsyncSession(loglevel=log_level) as session:
            response = await session.destroy_with(prefix=name, kind=kind, status=status)
            console.print(
                f"[bold green]Successfully pruned {len(response)} sessions.[/bold green]"
            )

    asyncio.run(_prune())
