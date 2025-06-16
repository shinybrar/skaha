"""Skaha Server Configuration and Discovery Script - Pydantic Optimized Version."""

from __future__ import annotations

import asyncio
import time

import httpx
from pydantic import BaseModel, Field
from rich.console import Console
from rich.table import Table
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


def display(
    console: Console,
    results: DiscoveryResults,
    dead: bool = False,
    details: bool = False,
) -> None:
    """Display discovery results in a formatted table.

    Presents the discovered Skaha servers in a rich table format with status indicators
    and summary statistics. Active servers are shown with a green circle, while inactive
    servers are shown with a red circle (if the 'dead' parameter is True).

    Args:
        console: Rich console instance for output display
        results: Discovery results containing endpoint information
        dead: Whether to display inactive endpoints (default: False)
        details: Whether to display detailed URI and URL information (default: False)
    """
    table = Table(title="Skaha Servers (All Registries)")
    table.add_column("Origin", style="dim", justify="center")
    if details:
        table.add_column("URI", style="green")
        table.add_column("URL", style="cyan", overflow="fold")
    table.add_column("Status", style="bold", justify="center")
    table.add_column("Name", style="magenta")

    grouped_results = results.get_by_registry()

    for registry in grouped_results:
        endpoints = grouped_results[registry]
        if not endpoints:
            row_data = [registry]
            if details:
                row_data.extend(["-", "-"])
            row_data.extend(["[bold red]No endpoints found[/bold red]", "-"])
            table.add_row(*row_data)
        else:
            for endpoint in endpoints:
                if endpoint.status == 200:
                    row_data = [registry]
                    if details:
                        row_data.extend([endpoint.uri, endpoint.url])
                    row_data.extend(["🟢", endpoint.name or "Unknown"])
                    table.add_row(*row_data)
                elif dead:
                    row_data = [registry]
                    if details:
                        row_data.extend([endpoint.uri, endpoint.url])
                    row_data.extend(["🔴", endpoint.name or "Unknown"])
                    table.add_row(*row_data)

    console.print(table)

    # Display summary statistics
    console.print("\n[bold]Summary:[/bold]")
    console.print(f"• Total registries: {len(grouped_results)}")
    console.print(f"• Total endpoints found: {results.found}")
    console.print(f"• Total endpoints checked: {results.checked}")
    console.print(f"• Active endpoints: {results.successful}")
    console.print(f"• Registry fetch time: {results.registry_fetch_time:.2f}s")
    console.print(f"• Endpoint check time: {results.endpoint_check_time:.2f}s")
    console.print(f"• Total time: {results.total_time:.2f}s")


async def find(
    dev: bool = False,
    dead: bool = False,
    timeout: int = 2,
    details: bool = False,
    connections: int = 100,
    show: bool = True,
    config: SearchConfig | None = None,
) -> DiscoveryResults:
    """Find Skaha Servers.

    Args:
        dev (bool, optional): Include development servers. Defaults to False.
        dead (bool, optional): Include dead servers. Defaults to False.
        timeout (int, optional): HTTP request timeout. Defaults to 2.
        details (bool, optional): Detailed display output. Defaults to False.
        connections (int, optional): Max concurrent connections. Defaults to 100.
        show (bool, optional): Show results. Defaults to True.
        config (ServerConfig | None, optional): Server configuration. Defaults to None.

    Returns:
        Results: Discovery results.
    """
    if config is None:
        config = SearchConfig()

    console = Console()

    async with Discover(
        config, timeout=timeout, max_connections=connections
    ) as discovery:
        results = await discovery.servers(dev=dev)
        if show:
            display(console, results, dead=dead, details=details)
        return results


if __name__ == "__main__":
    asyncio.run(find(dev=False, dead=False, timeout=2, details=False))
