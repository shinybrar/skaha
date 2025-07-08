"""Login command for Science Platform CLI."""

from __future__ import annotations

import asyncio
from typing import Annotated

import typer
from pydantic import AnyHttpUrl, AnyUrl
from rich.console import Console
from rich.prompt import Confirm

from skaha import get_logger, set_log_level
from skaha.auth import oidc, x509
from skaha.models.auth import (
    OIDC,
    X509,
)
from skaha.models.config import Configuration
from skaha.models.http import Server
from skaha.utils.discover import servers

console = Console()
log = get_logger(__name__)


auth = typer.Typer(
    name="auth",
    help="Authentication Commands",
    no_args_is_help=True,
    rich_help_panel="Authentication",
)


@auth.command("login")
def login(
    force: Annotated[
        bool,
        typer.Option(
            "--force",
            help="Force re-authentication",
        ),
    ] = False,
    debug: Annotated[
        bool,
        typer.Option(
            "--debug",
            help="Enable debug logging",
        ),
    ] = False,
    dead: Annotated[
        bool,
        typer.Option(
            "--dead",
            help="Include dead servers in discovery",
        ),
    ] = False,
    dev: Annotated[
        bool,
        typer.Option(
            "--dev",
            help="Include dev servers in discovery",
        ),
    ] = False,
    details: Annotated[
        bool,
        typer.Option(
            "--details",
            help="Include server details in discovery",
        ),
    ] = False,
    discovery_url: Annotated[
        str,
        typer.Option(
            "--discovery-url",
            "-d",
            help="OIDC Discovery URL",
        ),
    ] = "https://ska-iam.stfc.ac.uk/.well-known/openid-configuration",
) -> None:
    """Login to Science Platform.

    This command will guide you through the authentication process,
    automatically discovering the upstream server and choosing the
    appropriate authentication method based on the server's configuration.
    """
    if debug:
        set_log_level("DEBUG")

    try:
        console.print("[bold blue]Starting Science Platform Login[/bold blue]")
        config = Configuration.assemble()
        console.print("[green]✓[/green] Found existing configuration")
    except (FileNotFoundError, OSError, ValueError):
        msg = "No configuration found, using defaults."
        console.print(f"[yellow dim]{msg}.[/yellow dim]")
        config = Configuration()

    try:
        if not force and (config.auth.valid() and not config.auth.expired()):
            console.print("[green]✓[/green] Credentials valid")
            selected = getattr(config.auth, str(config.auth.mode)).server
            console.print(
                f"[green]✓[/green] Authenticated with {selected.name} @ {selected.url}"
            )
            console.print("[dim] Use --force to re-authenticate.[dim]")
            return

        # Run discovery and get selected server
        selected = asyncio.run(servers(dev=dev, dead=dead, details=details))
        log.debug("Selected server: %s", selected)
        server: Server = Server(
            name=f"{selected.registry}-{selected.name}",
            uri=AnyUrl(selected.uri),
            url=AnyHttpUrl(selected.url),
            version="v0",
        )

        config.url = server.url
        config.version = server.version
        config.uri = server.uri
        config.name = server.name

        # Step 7-8: Choose authentication method based on registry
        if selected.registry.upper() == "CADC":
            console.print("[bold blue]X509 Certificate Authentication[/bold blue]")
            config.auth.mode = "x509"
            config.auth.x509.server = server
            config.auth.x509 = x509.authenticate(config.auth.x509)
        else:
            console.print(
                f"[bold blue]OIDC Authentication for {selected.url}[/bold blue]"
            )
            config.auth.mode = "oidc"
            config.auth.oidc.server = server
            config.auth.oidc.endpoints.discovery = discovery_url
            config.auth.oidc = asyncio.run(oidc.authenticate(config.auth.oidc))

        console.print("[green]✓[/green] Saving configuration")
        config.save()
        console.print("[bold green]Login completed successfully![/bold green]")

    except Exception as error:
        console.print(f"[bold red]Login failed: {error}[/bold red]")
        raise typer.Exit(1) from error


@auth.command("logout")
def logout(
    confirm: Annotated[
        bool,
        typer.Option(
            "--yes",
            "-y",
            help="Skip confirmation prompt",
            rich_help_panel="Confirmation",
        ),
    ] = False,
) -> None:
    """Logout of Science Platform."""
    if not confirm:
        should_logout = Confirm.ask(
            "This will remove all stored authentication credentials. Continue?"
        )
        if not should_logout:
            console.print("[yellow]Logout cancelled[/yellow]")
            raise typer.Exit(0)

    try:
        config = Configuration.assemble()
        config.name = None
        config.uri = None
        config.url = None
        config.version = None
        # Clear authentication details
        config.auth.mode = "x509"
        config.auth.x509 = X509()  # type: ignore [call-arg]
        config.auth.oidc = OIDC()  # type: ignore [call-arg]
        # Save updated configuration
        config.save()
        console.print("[green]✓[/green] Authentication credentials cleared")
    except (FileNotFoundError, OSError, ValueError):
        console.print("[yellow]No configuration found to clear[/yellow]")
    except Exception as error:
        console.print(f"[bold red]Error during logout: {error}[/bold red]")
        raise typer.Exit(1) from error


if __name__ == "__main__":
    auth()
