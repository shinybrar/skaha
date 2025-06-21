"""Skaha Server Configuration and Discovery Script - Pydantic Optimized Version."""

from __future__ import annotations

import asyncio
import sys
import time

import httpx
import questionary
from pydantic import BaseModel, Field
from rich.console import Console
from typing_extensions import Self


class SearchConfig(BaseModel):
    """Configuration model for server discovery settings."""

    registries: dict[str, str] = Field(
        default={
            "https://spsrc27.iaa.csic.es/reg/resource-caps": "SRCnet",
            "https://ws.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/reg/resource-caps": "CADC",
        }
    )

    names: dict[str, str] = Field(
        default={
            "ivo://canfar.net/src/skaha": "Canada",
            "ivo://canfar.cam.uksrc.org/skaha": "UK-Cambridge",
            "ivo://canfar.ral.uksrc.org/skaha": "UK-RAL",
            "ivo://src.skach.org/skaha": "Switzerland",
            "ivo://espsrc.iaa.csic.es/skaha": "Spain",
            "ivo://canfar.itsrc.oact.inaf.it/skaha": "Italy",
            "ivo://shion-sp.mtk.nao.ac.jp/skaha": "Japan",
            "ivo://canfar.krsrc.kr/skaha": "Korea",
            "ivo://canfar.ska.zverse.space/skaha": "China",
            "ivo://cadc.nrc.ca/skaha": "CANFAR",
        }
    )

    omit: list[tuple[str, str]] = Field(
        default=[("CADC", "ivo://canfar.net/src/skaha")]
    )

    excluded: tuple[str, ...] = Field(
        default=("dev", "development", "test", "demo", "stage", "staging")
    )


class ServerInfo(BaseModel):
    """Model to store Skaha Server endpoint information."""

    registry: str
    uri: str
    url: str
    status: int | None = None
    name: str | None = None


class RegistryInfo(BaseModel):
    """Model for registry contents."""

    name: str
    content: str
    success: bool = True
    error: str | None = None


class DiscoveryResults(BaseModel):
    """Model for complete discovery results."""

    endpoints: list[ServerInfo] = Field(default_factory=list)
    total_time: float = 0.0
    registry_fetch_time: float = 0.0
    endpoint_check_time: float = 0.0
    found: int = 0
    checked: int = 0
    successful: int = 0

    def add(self, endpoint: ServerInfo) -> None:
        """Add an endpoint to results."""
        self.endpoints.append(endpoint)
        if endpoint.status == 200:
            self.successful += 1

    def get_by_registry(self) -> dict[str, list[ServerInfo]]:
        """Group endpoints by registry."""
        results: dict[str, list[ServerInfo]] = {}
        for endpoint in self.endpoints:
            if endpoint.registry not in results:
                results[endpoint.registry] = []
            results[endpoint.registry].append(endpoint)
        return results


class Discover:
    """Optimized server discovery with single HTTP client and Pydantic models."""

    def __init__(
        self, config: SearchConfig, timeout: int = 2, max_connections: int = 100
    ) -> None:
        """Initialize with configuration and connection limits."""
        self.config = config
        self.timeout = timeout

        # Single HTTP client for all operations
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout),
            limits=httpx.Limits(
                max_keepalive_connections=max_connections,
                max_connections=max_connections,
                keepalive_expiry=30.0,
            ),
            http2=True,
            follow_redirects=True,
        )

        self.console = Console()

    async def __aenter__(self) -> Self:
        """Async context manager entry method.

        Returns:
            Discover: The instance of this class.
        """
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> None:
        """Async context manager exit method - cleans up HTTP client.

        Args:
            exc_type: The exception type if an exception was raised in the context.
            exc_val: The exception value if an exception was raised in the context.
            exc_tb: The traceback if an exception was raised in the context.
        """
        await self.client.aclose()

    async def fetch(self, url: str, name: str) -> RegistryInfo:
        """Fetch registry contents.

        Args:
            url (str): Registry URL.
            name (str): Common name for the registry.

        Returns:
            RegistryInfo: Registry information.
        """
        try:
            start_time = time.time()
            response = await self.client.get(url)
            response.raise_for_status()
            elapsed = time.time() - start_time
            self.console.print(f"[dim]Fetched {name} in {elapsed:.2f}s[/dim]")

            return RegistryInfo(name=name, content=response.text, success=True)
        except (httpx.HTTPError, httpx.TimeoutException, httpx.RequestError) as error:
            error_msg = str(error)
            self.console.print(f"[red]Failed to fetch {name}: {error_msg}[/red]")
            return RegistryInfo(name=name, content="", success=False, error=error_msg)

    async def extract(
        self, registry: RegistryInfo, dev: bool = False
    ) -> list[ServerInfo]:
        """Extract skaha/capabilities endpoints from registry content asynchronously."""
        if not registry.success or not registry.content:
            return []

        endpoints: list[ServerInfo] = []

        for entry in registry.content.splitlines():
            line = entry.strip()
            if line.startswith("#") or not line or "=" not in line:
                continue

            uri, url = line.split("=", 1)
            uri, url = uri.strip(), url.strip()

            if url.endswith("/skaha/capabilities") and uri.endswith("/skaha"):
                url = url.replace("/capabilities", "")

                # Apply exclusion filters
                if not dev and any(
                    word in uri.lower() or word in url.lower()
                    for word in self.config.excluded
                ):
                    continue

                # Apply omit filters
                if (registry.name, uri) in self.config.omit:
                    continue

                endpoint = ServerInfo(
                    registry=registry.name,
                    uri=uri,
                    url=url,
                    name=self.config.names.get(uri),
                )
                endpoints.append(endpoint)

        return endpoints

    async def check(self, endpoint: ServerInfo) -> ServerInfo:
        """Check endpoint status using HEAD request."""
        try:
            response = await self.client.head(endpoint.url)
            endpoint.status = response.status_code
        except (httpx.HTTPError, httpx.TimeoutException):
            endpoint.status = None
        return endpoint

    async def servers(self, dev: bool = False) -> DiscoveryResults:
        """Discover all servers with maximum parallelization."""
        results = DiscoveryResults()
        start_time = time.time()

        # Step 1: Fetch all registries in parallel
        registry_start = time.time()
        registry_tasks = [
            self.fetch(url, name) for url, name in self.config.registries.items()
        ]
        registry_results = await asyncio.gather(*registry_tasks)
        results.registry_fetch_time = time.time() - registry_start

        # Step 2: Extract all endpoints from all registries
        all_endpoints: list[ServerInfo] = []
        for registry_result in registry_results:
            endpoints = await self.extract(registry_result, dev)
            all_endpoints.extend(endpoints)

        results.found = len(all_endpoints)

        if not all_endpoints:
            results.total_time = time.time() - start_time
            return results

        # Step 3: Check all endpoints in parallel using single client
        check_start = time.time()
        checked_endpoints = await asyncio.gather(
            *[self.check(endpoint) for endpoint in all_endpoints]
        )
        results.endpoint_check_time = time.time() - check_start

        # Step 4: Add all endpoints to results
        for endpoint in checked_endpoints:
            results.add(endpoint)

        results.checked = len(checked_endpoints)
        results.total_time = time.time() - start_time

        self.console.print(
            f"[bold green]Discovery completed in {results.total_time:.2f}s "
            f"({results.successful}/{results.checked} active)[/bold green]"
        )

        return results


async def display(
    results: DiscoveryResults,
    dead: bool = False,
    details: bool = False,
) -> ServerInfo:
    """Display discovery results and require interactive selection.

    Args:
        results: Discovery results containing endpoint information
        dead: Whether to show inactive endpoints. (default: False)
        details: Whether to display detailed URI and URL information (default: False)

    Returns:
        ServerInfo: The selected server info

    Raises:
        SystemExit: If no endpoints are available for selection
    """
    console = Console()

    vivos: list[ServerInfo] = []
    morte: list[ServerInfo] = []

    for endpoint in results.endpoints:
        if endpoint.status == 200:
            vivos.append(endpoint)
        else:
            morte.append(endpoint)

    # Check if endpoints are available
    if not vivos and not (dead and morte):
        console.print("\n[bold red]No servers available.[/bold red]")
        sys.exit(1)

    # Create choices for questionary with equal length formatting
    choices: list[questionary.Choice] = []
    available: list[ServerInfo] = vivos
    if dead:
        available.extend(morte)

    # Calculate maximum widths for alignment
    max_name_width = max(len(endpoint.name or "Unknown") for endpoint in available)
    max_registry_width = max(len(endpoint.registry) for endpoint in available)

    max_uri_width = 0
    if details:
        max_uri_width = max(len(endpoint.uri) for endpoint in available)

    for endpoint in available:
        # Determine status indicator
        indicator = "🔴" if endpoint.status is None else "🟢"

        # Format name and registry with padding for alignment
        name = (endpoint.name or "Unknown").ljust(max_name_width)
        registry = endpoint.registry.ljust(max_registry_width)

        # Create choice text with consistent spacing
        choice = f"{indicator} {name} {registry}"

        # Add detailed info if requested with alignment
        if details:
            uri = endpoint.uri.ljust(max_uri_width)
            choice += f" {uri} {endpoint.url}"

        choices.append(questionary.Choice(title=choice, value=endpoint))

    # Use questionary to select an endpoint
    try:
        selection: ServerInfo | None = await questionary.select(
            "Select a Skaha Server:",
            choices=choices,
            style=questionary.Style(
                [
                    ("question", "bold"),
                    ("answer", "fg:#ff9d00 bold"),
                    ("pointer", "fg:#ff9d00 bold"),
                    ("highlighted", "fg:#ff9d00 bold"),
                    ("selected", "fg:#cc5454"),
                    ("separator", "fg:#cc5454"),
                    ("instruction", ""),
                    ("text", ""),
                    ("disabled", "fg:#858585 italic"),
                ]
            ),
        ).ask_async()
    except KeyboardInterrupt:
        sys.exit(0)
    else:
        if selection is None:
            # User cancelled with Ctrl+C
            sys.exit(0)
        return selection


async def find(
    dev: bool = False,
    dead: bool = False,
    details: bool = False,
    timeout: int = 2,
) -> ServerInfo:
    """Find and select a Skaha Server.

    Args:
        dev: Include development servers. Defaults to False.
        dead: Show only inactive endpoints (status=None). Defaults to False.
        details: Show detailed URI and URL information. Defaults to False.
        timeout: HTTP request timeout. Defaults to 2.

    Returns:
        ServerInfo: The selected server info.
    """
    config = SearchConfig()

    async with Discover(config, timeout=timeout, max_connections=100) as discovery:
        results = await discovery.servers(dev=dev)
        return await display(results, dead=dead, details=details)


if __name__ == "__main__":
    # Test with active endpoints and details
    server = asyncio.run(find())
