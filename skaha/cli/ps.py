"""CLI command to list Skaha sessions."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Annotated

import typer
from rich import box
from rich.console import Console
from rich.table import Table
import humanize

from skaha.models.session import FetchResponse
from skaha.session import AsyncSession

console = Console()

ps = typer.Typer(
    name="ps",
    help="List sessions.",
    no_args_is_help=False,
)

@ps.callback(invoke_without_command=True)
def list_sessions(
    everything: Annotated[
        bool,
        typer.Option(
            "--all", "-a", help="Show all sessions (default shows just running)."
        ),
    ] = False,
    quiet : Annotated[
        bool,
        typer.Option(
            "--quiet", "-q", help="Only show session IDs."
        ),
    ] = False,
    kind: Annotated[
        str | None,
        typer.Option(
            "--kind", "-k", help="Filter by session kind."
        ),
    ] = None,
    status: Annotated[
        str | None,
        typer.Option(
            "--status", "-s", help="Filter by session status."
        ),
    ] = None,
    debug: Annotated[
        bool,
        typer.Option(
            "--debug",
            help="Enable debug logging.",
        ),
    ] = False,
) -> None:
    """List sessions."""

    async def _list_sessions() -> None:
        log_level = "DEBUG" if debug else "INFO"
        async with AsyncSession(loglevel=log_level) as session:
            sessions: list[FetchResponse] = []
            sessions = [
                FetchResponse.model_validate(item) for item in await session.fetch(kind=kind, status=status)
            ]

        if quiet:
            for instance in sessions:
                console.print(instance.id)
            return

        table = Table(title="Skaha Sessions", box=box.SIMPLE)
        table.add_column("SESSION ID", style="cyan")
        table.add_column("NAME", style="magenta")
        table.add_column("KIND", style="green")
        table.add_column("STATUS", style="green")
        table.add_column("IMAGE", style="blue")
        table.add_column("CREATED", style="yellow")

        running = 0
        for instance in sessions:
            if not everything and instance.status not in ["Pending", "Running"]:
                continue
            running += 1
            uptime = datetime.now(timezone.utc) - instance.startTime
            # Convert uptime to human readable format using strftime
            created = humanize.naturaldelta(uptime)


            uptime = str(uptime).split(".", maxsplit=1)[0]  # Remove microseconds

            table.add_row(
                instance.id,
                instance.name,
                instance.type,
                instance.status,
                instance.image,
                created,
            )

        if running == 0 and not everything:
            console.print("[yellow]No pending or running sessions found.[/yellow]")
            console.print("[dim]Use [italic]--all[/italic] to show all sessions.[/dim]")
        else:
            console.print(table)

    asyncio.run(_list_sessions())
