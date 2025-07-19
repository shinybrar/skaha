"""CLI command to get information for Skaha sessions."""

from __future__ import annotations

import asyncio
from typing import Annotated

import humanize
import typer
from rich import box
from rich.console import Console
from rich.table import Table

from skaha.models.session import FetchResponse
from skaha.session import AsyncSession

console = Console()

info = typer.Typer(
    name="info",
    help="Get detailed information about sessions.",
    no_args_is_help=True,
)


@info.callback(invoke_without_command=True)
def get_info(
    session_ids: Annotated[
        list[str],
        typer.Argument(help="One or more session IDs."),
    ],
    debug: Annotated[
        bool,
        typer.Option(
            "--debug",
            help="Enable debug logging.",
        ),
    ] = False,
) -> None:
    """Get detailed information about one or more sessions."""

    async def _get_info() -> None:
        log_level = "DEBUG" if debug else "INFO"
        async with AsyncSession(loglevel=log_level) as session:
            sessions_info = await session.info(ids=session_ids)
        if not sessions_info:
            console.print(
                "[yellow]No information found for the specified session(s).[/yellow]"
            )
            return

        field_map = {
            "id": "ID",
            "name": "Name",
            "status": "Status",
            "type": "Type",
            "image": "Image",
            "userid": "User ID",
            "startTime": "Start Time",
            "expiryTime": "Expiry Time",
            "requestedRAM": "RAM (Req)",
            "requestedCPUCores": "CPU (Req)",
            "requestedGPUCores": "GPU (Req)",
            "ramInUse": "RAM (Used)",
            "cpuCoresInUse": "CPU (Used)",
            "gpuRAMInUse": "GPU RAM (Used)",
            "gpuUtilization": "GPU Utilization",
            "connectURL": "Connect URL",
            "runAsUID": "UID",
            "runAsGID": "GID",
            "supplementalGroups": "Groups",
            "appid": "App ID",
        }

        table = Table(
            title="Skaha Session Information",
            box=box.SIMPLE,
            show_header=True,
            header_style="bold magenta",
        )

        for header in field_map.values():
            table.add_column(header, overflow="fold")

        for session_info_dict in sessions_info:
            session_info = FetchResponse.model_validate(session_info_dict)
            row = []
            for field in field_map:
                value = getattr(session_info, field)
                if field in ["startTime", "expiryTime"]:
                    display_value = humanize.naturaltime(value)
                else:
                    display_value = str(value)
                row.append(display_value)
            table.add_row(*row)

        console.print(table)

    asyncio.run(_get_info())
