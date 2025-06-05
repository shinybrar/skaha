"""Utility functions for building parameters skaha client."""

from __future__ import annotations

from typing import Any

from skaha.models import KINDS, STATUS, VIEW, CreateSpec, FetchSpec
from skaha.utils import convert


def fetch_parameters(
    kind: KINDS | None = None,
    status: STATUS | None = None,
    view: VIEW | None = None,
) -> dict[str, Any]:
    """Build parameters for fetching sessions."""
    values: dict[str, Any] = {}
    for key, value in {"kind": kind, "status": status, "view": view}.items():
        if value:
            values[key] = value
    # Kind is an alias for type in the API.
    # It is renamed as kind to avoid conflicts with the built-in type function.
    # by_alias=true, returns, {"type": "headless"} instead of {"kind": "headless"}
    return FetchSpec(**values).model_dump(exclude_none=True, by_alias=True)


def create_parameters(
    name: str,
    image: str,
    cores: int = 2,
    ram: int = 4,
    kind: KINDS = "headless",
    gpu: int | None = None,
    cmd: str | None = None,
    args: str | None = None,
    env: dict[str, Any] | None = None,
    replicas: int = 1,
) -> list[list[tuple[str, Any]]]:
    """Build parameters for creating sessions."""
    specification: CreateSpec = CreateSpec(
        name=name,
        image=image,
        cores=cores,
        ram=ram,
        kind=kind,
        gpus=gpu,
        cmd=cmd,
        args=args,
        env=env,
        replicas=replicas,
    )
    data: dict[str, Any] = specification.model_dump(exclude_none=True, by_alias=True)
    payload: list[tuple[str, Any]] = []
    payloads: list[list[tuple[str, Any]]] = []
    if "env" not in data:
        data["env"] = {}
    for replica in range(replicas):
        data["name"] = name + "-" + str(replica + 1)
        data["env"]["REPLICA_ID"] = str(replica + 1)
        data["env"]["REPLICA_COUNT"] = str(replicas)
        payload = convert.dict_to_tuples(data)
        payloads.append(payload)
    return payloads
