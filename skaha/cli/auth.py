"""Login command for Science Platform CLI."""

from __future__ import annotations

import asyncio
from typing import Annotated

import typer
from rich.console import Console
from rich.prompt import Confirm

from skaha import get_logger, set_log_level
from skaha.auth import oidc, x509
from skaha.config.auth import (
    OIDC,
    X509,
    OIDCClientConfig,
    OIDCTokenConfig,
    OIDCURLConfig,
    ServerInfo,
)
from skaha.config.config import Configuration
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
    except (FileNotFoundError, OSError, ValueError):
        config = Configuration()

    try:
        if not force and (config.auth.valid() and not config.auth.expired()):
            console.print("[green]✓[/green] Found existing configuration")
            console.print("[green]✓[/green] Credentials valid")
            server = getattr(config.auth, str(config.auth.mode)).server
            console.print(
                f"[green]✓[/green] Authenticated with {server.name} @ {server.url}"
            )
            console.print("[dim] Use --force to re-authenticate.[dim]")
            return

        # Run discovery and get selected server
        server = asyncio.run(servers(dev=dev, dead=dead, details=details))
        config.client.url = server.url
        config.client.version = "v0"

        # Create server info for auth method
        server_info = ServerInfo(
            name=server.name,
            uri=server.uri,
            url=server.url,
        )

        # Step 7-8: Choose authentication method based on registry
        if server.registry.upper() == "CADC":
            console.print("[bold blue]X509 Certificate Authentication[/bold blue]")
            config.auth.x509 = X509(server=server_info)
            config.auth.x509 = x509.authenticate(config.auth.x509)
            config.auth.mode = "x509"
        else:
            console.print(
                f"[bold blue]OIDC Authentication for {server.url}[/bold blue]"
            )
            config.auth.oidc = OIDC(
                endpoints=OIDCURLConfig(discovery=discovery_url),
                client=OIDCClientConfig(),
                token=OIDCTokenConfig(),
                server=server_info,
            )
            config.auth.oidc = asyncio.run(oidc.authenticate(config.auth.oidc))
            config.auth.mode = "oidc"

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

        # Clear authentication credentials
        config.auth.mode = None
        config.auth.oidc = OIDC(
            endpoints=OIDCURLConfig(),
            client=OIDCClientConfig(),
            token=OIDCTokenConfig(),
            server=ServerInfo(),
        )
        config.auth.x509 = X509(server=ServerInfo())

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
