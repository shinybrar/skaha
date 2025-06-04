from importlib import metadata
from logging import getLogger
from pathlib import Path

import toml

log = getLogger(__name__)

# Root path to the Skaha Project
BASE_PATH: Path = Path(__file__).absolute().parent.parent

try:
    __version__ = metadata.version("skaha")
except metadata.PackageNotFoundError as error:  # pragma: no cover
    log.warning(error)
    pyproject = toml.load(BASE_PATH / "pyproject.toml")
    __version__ = pyproject.get("project", {}).get("version", "unknown")
except FileNotFoundError as error:  # pragma: no cover
    log.warning(error)
    log.warning("unable to find skaha client version")
    __version__ = "unknown"
