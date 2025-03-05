"""Get available resources from the skaha server."""

from typing import Any, Dict

from httpx import Response

from skaha.client import SkahaClient


class Context(SkahaClient):
    """Skaha Context.

    Args:
        SkahaClient (skaha.client.SkahaClient): Configured Skaha Client.
    """

    def resources(self) -> Dict[str, Any]:
        """Get available resources from the skaha server.

        Returns:
            A dictionary of available resources.

        Examples:
            >>> from skaha.context import Context
            >>> context = Context()
            >>> context.resources()
            {'cores': {
              'default': 1,
              'defaultRequest': 1,
              'defaultLimit': 16,
              'defaultHeadless': 1,
              'options': [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16]
              },
             'memoryGB': {
              'default': 2,
              'defaultRequest': 4,
              'defaultLimit': 192,
              'defaultHeadless': 4,
              'options': [1,2,4...192]
             },
            'gpus': {
             'options': [1,2, ... 28]
             }
            }
        """
        response: Response = self.client.get(url="context")
        response.raise_for_status()
        return response.json()
