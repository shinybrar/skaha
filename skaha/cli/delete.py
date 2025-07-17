"""CLI command to delete Skaha sessions."""

from __future__ import annotations

import asyncio
from typing import Annotated

import typer
from rich.console import Console
from rich.prompt import Confirm

from skaha.hooks.typer.aliases import AliasGroup
from skaha.session import AsyncSession

console = Console()

delete = typer.Typer(
    name="delete",
    help="Delete one or more sessions.",
    no_args_is_help=True,
    cls=AliasGroup,
)


@delete.callback(invoke_without_command=True)
def delete_sessions(
    session_ids: Annotated[
        list[str],
        typer.Argument(help="One or more session IDs to delete."),
    ],
    force: Annotated[
        bool,
        typer.Option(
            "--force",
            "-f",
            help="Force deletion without confirmation.",
        ),
    ] = False,
    debug: Annotated[
        bool,
        typer.Option(
            "--debug",
            help="Enable debug logging.",
        ),
    ] = False,
) -> None:
    """Delete one or more Skaha sessions."""
    if not force:
        should_delete = Confirm.ask(
            f"Are you sure you want to delete {len(session_ids)} session(s)?"
        )
        if not should_delete:
            console.print("[yellow]Deletion cancelled.[/yellow]")
            raise typer.Exit()

    async def _delete() -> None:
        log_level = "DEBUG" if debug else "INFO"
        async with AsyncSession(loglevel=log_level) as session:
            try:
                deleted_ids = await session.delete(ids=session_ids)
                if deleted_ids:
                    console.print(
                        f"[bold green]Successfully deleted {len(deleted_ids)} session(s):[/bold green]"
                    )
                    for session_id in deleted_ids:
                        console.print(f"  - {session_id}")
                else:
                    console.print("[bold red]Failed to delete session(s).[/bold red]")
                    raise typer.Exit(1)
            except Exception as e:
                console.print(f"[bold red]Error during deletion: {e}[/bold red]")
                raise typer.Exit(1)

    asyncio.run(_delete())
