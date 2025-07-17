"""CLI command to create Skaha sessions."""

from __future__ import annotations

import asyncio
from typing import Annotated, Any, get_args

import click
import typer
from rich.console import Console

from skaha.models.types import Kind
from skaha.session import AsyncSession
from skaha.utils import funny

CHOICES: list[str] = list(get_args(Kind))
METAVAR = "|".join(CHOICES)

console = Console()

create = typer.Typer(
    name="create",
    help="Create a new Skaha session.",
    no_args_is_help=True,
)


@create.callback(invoke_without_command=True)
def creation(
    kind: Annotated[
        str,
        typer.Argument(
            ...,
            click_type=click.Choice(CHOICES, case_sensitive=True),
            metavar=METAVAR,
            help="Session Kind.",
        ),
    ],
    image: Annotated[
        str,
        typer.Argument(help="Container Image."),
    ],
    command: Annotated[
        list[str] | None,
        typer.Argument(help="Runtime Command + Arguments."),
    ] = None,
    name: Annotated[
        str, typer.Option("--name", "-n", help="Name of the session.")
    ] = funny.name(),
    cores: Annotated[
        int, typer.Option("--cores", "-c", help="Number of CPU cores.")
    ] = 1,
    ram: Annotated[int, typer.Option("--ram", "-r", help="Amount of RAM in GB.")] = 2,
    gpu: Annotated[
        int | None, typer.Option("--gpu", "-g", help="Number of GPUs.")
    ] = None,
    env: Annotated[
        list[str] | None,
        typer.Option(
            "--env", "-e", help="Penvironment variables (e.g., --env KEY=VALUE)."
        ),
    ] = None,
    replicas: Annotated[
        int, typer.Option("--replicas", help="Number of replicas to create.")
    ] = 1,
    debug: Annotated[
        bool,
        typer.Option(
            "--debug",
            help="Enable debug logging.",
        ),
    ] = False,
) -> None:
    """Create a new Skaha session."""
    cmd_str = command[0] if command else None
    args_str = " ".join(command[1:]) if command and len(command) > 1 else None

    env_vars: dict[str, Any] = {}
    if env:
        for item in env:
            if "=" not in item:
                console.print(
                    f"[bold red] Invalid environment variable format: {item}[/bold red]"
                )
                raise typer.Exit(1)
            key, value = item.split("=", 1)
            env_vars[key] = value

    async def _create() -> None:
        log_level = "DEBUG" if debug else "INFO"
        async with AsyncSession(loglevel=log_level) as session:
            console.print(f"[bold blue]Creating {kind} session '{name}'...[/bold blue]")
            try:
                session_ids = await session.create(
                    name=name,
                    image=image,
                    cores=cores,
                    ram=ram,
                    kind=kind,
                    gpu=gpu,
                    cmd=cmd_str,
                    args=args_str,
                    env=env_vars if env_vars else None,
                    replicas=replicas,
                )
                if session_ids:
                    if len(session_ids) > 1:
                        console.print(
                            f"[bold green]Successfully created {len(session_ids)} "
                            f"sessions named '{name}':[/bold green]"
                        )
                        for session_id in session_ids:
                            console.print(f"  - {session_id}")
                    else:
                        console.print(
                            f"[bold green]Successfully created session "
                            f"'{name}' (ID: {session_ids[0]})[/bold green]"
                        )
                else:
                    console.print("[bold red]Failed to create session(s).[/bold red] ")
                    raise typer.Exit(1)
            except Exception as e:
                console.print(f"[bold red]Something went wrong: {e}[/bold red]")
                raise typer.Exit(1)

    asyncio.run(_create())
