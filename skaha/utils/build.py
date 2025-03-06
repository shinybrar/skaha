"""Utility functions for building parameters skaha client."""

from typing import Any, Dict, List, Optional, Tuple

from skaha.models import KINDS, STATUS, VIEW, CreateSpec, FetchSpec
from skaha.utils import convert


def fetch_parameters(
    kind: Optional[KINDS] = None,
    status: Optional[STATUS] = None,
    view: Optional[VIEW] = None,
) -> Dict[str, Any]:
    """Build parameters for fetching sessions."""
    values: Dict[str, Any] = {}
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
    gpu: Optional[int] = None,
    cmd: Optional[str] = None,
    args: Optional[str] = None,
    env: Optional[Dict[str, Any]] = None,
    replicas: int = 1,
) -> List[List[Tuple[str, Any]]]:
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
    data: Dict[str, Any] = specification.model_dump(exclude_none=True, by_alias=True)
    payload: List[Tuple[str, Any]] = []
    payloads: List[List[Tuple[str, Any]]] = []
    if "env" not in data:
        data["env"] = {}
    for replica in range(replicas):
        data["name"] = name + "-" + str(replica + 1)
        data["env"]["REPLICA_ID"] = str(replica + 1)
        data["env"]["REPLICA_COUNT"] = str(replicas)
        payload = convert.dict_to_tuples(data)
        payloads.append(payload)
    return payloads
