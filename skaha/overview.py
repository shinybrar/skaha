"""Skaha Overview."""

from typing import TYPE_CHECKING

from defusedxml import ElementTree
from pydantic import model_validator
from typing_extensions import Self

from skaha import get_logger
from skaha.client import SkahaClient

if TYPE_CHECKING:
    from httpx import Response

log = get_logger(__name__)


class Overview(SkahaClient):
    """Overview of the Skaha Server.

    Args:
        SkahaClient (Object): Skaha Client.
    """

    @model_validator(mode="after")
    def _update_base_url(self) -> Self:
        """Update base URL for the server.

        Returns:
            Self: The current object.
        """
        # The overview endpoint is not versioned, so need to remove it
        self.client.base_url = f"{self.server}"
        self.asynclient.base_url = f"{self.server}"
        return self

    def availability(self) -> bool:
        """Check if the server backend is available.

        Returns:
            bool: True if the server is available, False otherwise.
        """
        response: Response = self.client.get("availability")
        # Parse the XML string
        root = ElementTree.fromstring(response.text)  # type: ignore[arg-type]
        available = root.find(
            ".//{http://www.ivoa.net/xml/VOSIAvailability/v1.0}available",
        ).text  # type: ignore[attr-defined]
        note = root.find(
            ".//{http://www.ivoa.net/xml/VOSIAvailability/v1.0}note",
        ).text  # type: ignore[attr-defined]
        log.info(note)
        return available == "true"
