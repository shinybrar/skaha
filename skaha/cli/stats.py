"""CLI command to display cluster statistics."""

from __future__ import annotations

import asyncio
from typing import Annotated

import typer
from rich import box
from rich.console import Console
from rich.table import Table

from skaha.session import AsyncSession

console = Console()

stats = typer.Typer(
    name="stats",
    help="Display cluster-wide statistics.",
    no_args_is_help=False,
)


@stats.callback(invoke_without_command=True)
def get_stats(
    debug: Annotated[
        bool,
        typer.Option(
            "--debug",
            help="Enable debug logging.",
        ),
    ] = False,
) -> None:
    """Display cluster-wide usage and status statistics."""

    async def _get_stats() -> None:
        log_level = "DEBUG" if debug else "INFO"
        try:
            async with AsyncSession(loglevel=log_level) as session:
                stats_data = await session.stats()
        except Exception as e:
            console.print(f"[bold red]Error:[/bold red] Could not fetch stats. {e}")
            raise typer.Exit(1)

        # Main table
        main_table = Table(
            title="Skaha Cluster Usage Statistics",
            box=box.SIMPLE,
            show_header=True,
            header_style="bold blue",
        )
        main_table.add_column("Instances", justify="center")
        main_table.add_column("CPU", justify="center")
        main_table.add_column("RAM", justify="center")

        # Nested table for Instances
        instances = stats_data.get("instances", {})
        instances_table = Table(box=box.MINIMAL, show_header=False)
        instances_table.add_column("Kind", justify="left")
        instances_table.add_column("Count", justify="left")
        for key, value in instances.items():
            style = "bold" if key == "total" else ""
            instances_table.add_row(key.capitalize(), str(value), style=style)

        # Nested table for Cores
        cores = stats_data.get("cores", {})
        cores_table = Table(box=box.MINIMAL, show_header=False)
        cores_table.add_column("Metric", justify="left")
        cores_table.add_column("Value", justify="left")
        cores_table.add_row("Requested", f"{cores.get('requestedCPUCores', 'N/A')}")
        cores_table.add_row("Available", f"{cores.get('cpuCoresAvailable', 'N/A')}")

        # Nested table for RAM
        ram = stats_data.get("ram", {})
        ram_table = Table(box=box.MINIMAL, show_header=False)
        ram_table.add_column("Metric", justify="left")
        ram_table.add_column("Value", justify="left")
        ram_table.add_row("Requested", f"{ram.get('requestedRAM', 'N/A')}")
        ram_table.add_row("Available", f"{ram.get('ramAvailable', 'N/A')}")

        # Add the first row with nested tables
        main_table.add_row(instances_table, cores_table, ram_table)

        # Add the second row with max session size
        max_cpu = cores.get("maxCPUCores", {}).get("cpuCores", "N/A")
        max_ram = ram.get("maxRAM", {}).get("ram", "N/A")
        console.print(main_table)
        console.print(f"[bold]Maximum Requests:[/bold] {max_cpu} Cores, {max_ram} RAM")
        console.print("[dim]Based on best-case scenario, and may not be achievable.[/dim]")

    asyncio.run(_get_stats())
