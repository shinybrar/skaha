"""Skaha Logging Utility."""

import logging
from typing import List, Optional

from rich.console import Console
from rich.text import Text


def get_logger(
    name: str = __name__, level: int = logging.INFO, filename: Optional[str] = None
) -> logging.Logger:
    """Logging utility.

    Args:
        name (str): Name of the logger. Defaults to __name__.
        level (int): Logging Level. Defaults to logging.INFO.
        filename (Optional[str], optional): Log file name. Defaults to None.

    Returns:
        logging.Logger: Logger object.

    """
    # create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # create console handler and set level to debug
    streamer = logging.StreamHandler()
    streamer.setLevel(level)

    # create formatter
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # add formatter to ch
    streamer.setFormatter(formatter)

    # add ch to logger
    logger.addHandler(streamer)

    # create file handler
    if filename:
        filer = logging.FileHandler(filename)
        filer.setLevel(level)

        # add formatter to filer
        filer.setFormatter(formatter)

        # add filer to logger
        logger.addHandler(filer)

    logger.propagate = False

    return logger


def stdout(logs: str) -> None:
    """Prints log messages with colors based on severity.

    Args:
        logs (str): The log messages as a single string.
    """
    console = Console()
    lines: List[str] = logs.strip().split("\n")

    for line in lines:
        # Default style is white.
        style: str = "white"

        # Set style based on log level indicator.
        if line.startswith("[W"):
            style = "yellow"
        elif line.startswith("[I"):
            style = "green"
        # Check for error/warning keywords in messages from other apps.
        if "ERROR" in line:
            style = "bold red"
        elif "WARNING" in line and not line.startswith("[W"):
            style = "orange1"

        # Create a Rich Text object with the chosen style.
        text = Text(line, style=style)
        console.print(text)
