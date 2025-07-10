"""X509 Certificate Management Module.

This module provides functionality to obtain and inspect X509 PEM certificates
using the cadcutils.net.auth library as the backbone for X509 authentication.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from cadcutils.net.auth import Subject, get_cert  # type: ignore[import-untyped]
from cryptography import x509
from cryptography.hazmat.backends import default_backend

if TYPE_CHECKING:
    from skaha.models import auth


def gather(
    username: str | None = None,
    days_valid: int = 10,
    cert_path: Path | None = None,
) -> dict[str, Any]:
    """Gather user credentials and obtain X509 certificate.

    This function uses cadcutils.net.auth.get_cert as the backbone to obtain
    X509 certificates, similar to how the cadc-get-cert CLI tool works.

    Args:
        username (str, optional): Username for authentication. Will prompt if None.
            Defaults to None.
        days_valid (int): Number of days the certificate should be valid.
            Defaults to 10.
        cert_path (Path, optional): Path to save certificate.
            Defaults to ~/.ssl/cadcproxy.pem.

    Returns:
        dict[str, Any]: Dictionary with certificate info for skaha.config.auth.X509:
            - path (str): Path to PEM certificate file
            - expiry (float): Certificate expiry ctime

    Raises:
        ValueError: If certificate retrieval fails.

    Examples:
        >>> info = gather(username="myuser", days_valid=10)
        >>> print(f"Certificate saved to {info['path']}")
    """
    # Get credentials if not provided
    if not username:
        username = input("Username: ")

    # Set default path
    if cert_path is None:
        cert_path = Path.home() / ".ssl" / "cadcproxy.pem"

    try:
        # Create subject for authentication
        subject = Subject(username=username)

        # Use cadcutils.net.auth.get_cert to obtain the certificate
        cert_content = get_cert(
            subject=subject,
            days_valid=days_valid,
        )

        # Ensure the directory exists
        cert_path.parent.mkdir(parents=True, exist_ok=True)

        # Write certificate to file with secure permissions
        cert_path.write_text(cert_content)
        cert_path.chmod(0o600)  # Read/write for owner only

        # Get certificate info for return
        return inspect(cert_path)

    except Exception as e:
        msg = f"Failed to obtain X509 certificate: {e}"
        raise ValueError(msg) from e


def inspect(path: Path | None = None) -> dict[str, Any]:
    """Inspect X509 certificate and return info for skaha.config.auth.X509.

    Args:
        path (Path, optional): Path to certificate file.
            Defaults to ~/.ssl/cadcproxy.pem.

    Returns:
        dict[str, Any]: Dictionary with certificate info for skaha.config.auth.X509:
            - path (str): Path to PEM certificate file
            - expiry (float | None): Certificate expiry ctime

    Raises:
        ValueError: If certificate cannot be read or parsed.

    Examples:
        >>> info = inspect()
        >>> print(f"Certificate for {info['username']} expires at {info['expiry']}")
    """
    # Set default path
    if path is None:
        path = Path.home() / ".ssl" / "cadcproxy.pem"

    try:
        # Check if file exists and is readable
        assert path.exists(), f"{path} does not exist"
        assert path.is_file(), f"{path} is not a file"

        # Load and parse the certificate
        data = path.read_text(encoding="utf-8").encode("utf-8")
        cert = x509.load_pem_x509_certificate(data, default_backend())

        # Get expiry as Unix timestamp
        expiry = cert.not_valid_after_utc.timestamp()

        return {
            "path": path.absolute().as_posix(),
            "expiry": expiry,
        }

    except Exception as err:
        msg = f"Failed to inspect certificate: {err}"
        raise ValueError(msg) from err


def authenticate(config: auth.X509) -> auth.X509:
    """Authenticate using X509 certificate.

    Args:
        config (auth.X509): X509 configuration.

    Returns:
        auth.X509: X509 configuration.

    Raises:
        ValueError: If certificate cannot be read or parsed.
    """
    try:
        data = gather()
        config.path = data["path"]
        config.expiry = data["expiry"]
    except Exception as err:
        msg = f"Failed to authenticate with X509 certificate: {err}"
        raise ValueError(msg) from err
    else:
        return config
