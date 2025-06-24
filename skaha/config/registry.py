"""Skaha Server Configuration and Discovery Script - Pydantic Optimized Version."""

from __future__ import annotations

from pydantic import BaseModel, Field


class RegistrySearchConfig(BaseModel):
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
            "ivo://swesrc.chalmers.se/skaha": "Sweden",
            "ivo://canfar.cam.uksrc.org/skaha": "UK-CAM",
            "ivo://canfar.ral.uksrc.org/skaha": "UK-RAL",
            "ivo://src.skach.org/skaha": "Swiss",
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


class SkahaServer(BaseModel):
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


class SkahaServerResults(BaseModel):
    """Model for complete discovery results."""

    endpoints: list[SkahaServer] = Field(default_factory=list)
    total_time: float = 0.0
    registry_fetch_time: float = 0.0
    endpoint_check_time: float = 0.0
    found: int = 0
    checked: int = 0
    successful: int = 0

    def add(self, endpoint: SkahaServer) -> None:
        """Add an endpoint to results."""
        self.endpoints.append(endpoint)
        if endpoint.status == 200:
            self.successful += 1

    def get_by_registry(self) -> dict[str, list[SkahaServer]]:
        """Group endpoints by registry."""
        results: dict[str, list[SkahaServer]] = {}
        for endpoint in self.endpoints:
            if endpoint.registry not in results:
                results[endpoint.registry] = []
            results[endpoint.registry].append(endpoint)
        return results
