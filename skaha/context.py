"""Get available resources from the skaha server."""

from typing import Any, Dict

from pydantic import root_validator
from requests.models import Response

from skaha.client import SkahaClient


class Context(SkahaClient):
    """Get available resources from the skaha server."""

    @root_validator
    def set_server(cls, values: Dict[str, Any]):
        """Sets the server path after validation."""
        values["server"] = f"{values['server']}/{values['version']}/context"
        return values

    def resources(self) -> Dict[str, Any]:
        """Get available resources from the skaha server.

        Returns:
            A dictionary of available resources.

        Examples:
            >>> from skaha.context import Context
            >>> context = Context()
            >>> context.resources()
            {'defaultCores': 2,
             'defaultCoresHeadless': 1,
             'availableCores': [1, 2, 4, 8, 16],
             'defaultRAM': 16,
             'defaultRAMHeadless': 4,
             'availableRAM': [1, 2, 4, 8, 16, 32, 64, 128, 192],
             'availableGPUs': [1,2,3,...],
            }
        """
        response: Response = self.session.get(url=self.server)  # type: ignore
        response.raise_for_status()
        return response.json()
