from pydantic import BaseModel, Field


class Configuration(BaseModel):
    """Configuration model for Skaha."""

    name: str = Field(..., description="Name of the configuration")
    version: str = Field(..., description="Version of the configuration")
    description: str = Field("", description="Description of the configuration")
