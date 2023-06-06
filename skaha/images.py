"""Skaha Image Management."""
from typing import Any, Dict, List, Optional

from pydantic import root_validator
from requests.models import Response

from skaha.client import SkahaClient
from skaha.utils.logs import get_logger

log = get_logger(__name__)


class Images(SkahaClient):
    """Skaha Image Management."""

    @root_validator
    def set_server(cls, values: Dict[str, Any]):
        """Sets the server path after validation."""
        values["server"] = f"{values['server']}/{values['version']}/image"
        values["server"] = values["server"] + "/image"
        return values

    def fetch(self, kind: Optional[str] = None) -> List[str]:
        """Get images from Skaha Server.

        Args:
            kind (Optional[str], optional): Type of image. Defaults to None.

        Returns:
            List[str]: A list of images on the skaha server.

        Examples:
            >>> from skaha.images import Images
            >>> images = Images()
            >>> images.fetch(kind="headless")
            ['images.canfar.net/chimefrb/sample:latest',
             ...
             'images.canfar.net/skaha/terminal:1.1.1']
        """
        data: Dict[str, str] = {}
        # If kind is not None, add it to the data dictionary
        if kind:
            data["type"] = kind
        response: Response = self.session.get(url=self.server, params=data)  # type: ignore # noqa
        response.raise_for_status()
        response = response.json()
        reply: List[str] = []
        for image in response:
            reply.append(image["id"])  # type: ignore
        return reply
