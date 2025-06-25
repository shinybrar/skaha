"""Common types and constants for Skaha API models.

This module contains type definitions and constants used across
the Skaha API client models.
"""

from __future__ import annotations

from typing import Literal, TypeAlias

# Session type constants (new lowercase style)
Kind: TypeAlias = Literal["desktop", "notebook", "carta", "headless", "firefly"]
Status: TypeAlias = Literal["Pending", "Running", "Terminating", "Succeeded", "Error"]
View: TypeAlias = Literal["all"]
