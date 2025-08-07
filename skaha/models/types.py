"""Common types and constants for Skaha API models.

This module contains type definitions and constants used across
the Skaha API client models.
"""

from __future__ import annotations

from typing import Literal, TypeAlias

Kind: TypeAlias = Literal[
    "desktop", "notebook", "carta", "headless", "firefly", "desktop-app", "contributed"
]
"""Session type constants (new lowercase style)."""

Status: TypeAlias = Literal[
    "Pending", "Running", "Terminating", "Succeeded", "Error", "Failed"
]
"""Session status constants."""

View: TypeAlias = Literal["all"]
"""Session view constants."""

Mode: TypeAlias = Literal["x509", "oidc", "token", "default"]
"""Authentication mode constants."""
