"""Skaha Image Management."""

from typing import Any, Dict, List, Optional

from httpx import Response

from skaha.client import SkahaClient
from skaha.utils.logs import get_logger

log = get_logger(__name__)


class Images(SkahaClient):
    """Skaha Image Management.

    Args:
        SkahaClient (skaha.client.SkahaClient): Configured Skaha Client.

    Returns:
        Images: Skaha Image Management Object.
    """

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
        response: Response = self.client.get("image", params=data)  # type: ignore # noqa
        response.raise_for_status()
        payload: Dict[str, Any] = response.json()
        reply: List[str] = []
        for image in payload:
            reply.append(image["id"])  # type: ignore
        return reply
