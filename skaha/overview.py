"""Skaha Overview."""

from defusedxml import ElementTree
from httpx import Response
from pydantic import model_validator
from typing_extensions import Self

from skaha.client import SkahaClient
from skaha.utils import logs

log = logs.get_logger(__name__)


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
        response: Response = self.client.get("availability")  # type: ignore # noqa
        response.raise_for_status()
        # Parse the XML string
        root = ElementTree.fromstring(response.text)  # type: ignore
        available = root.find(
            ".//{http://www.ivoa.net/xml/VOSIAvailability/v1.0}available"
        ).text  # type: ignore
        note = root.find(
            ".//{http://www.ivoa.net/xml/VOSIAvailability/v1.0}note"
        ).text  # type: ignore
        log.info(note)
        if available == "true":
            return True
        return False
