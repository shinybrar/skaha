"""Comprehensive tests for the X509 authentication module."""

from __future__ import annotations

import datetime
import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

from skaha.auth.x509 import gather, inspect


class TestX509Module:
    """Test cases for the X509 authentication module."""

    @pytest.fixture
    def mock_cert_content(self) -> str:
        """Create a mock X509 certificate content for testing."""
        # Generate a private key
        private_key = rsa.generate_private_key(
            public_exponent=65537, key_size=2048, backend=default_backend()
        )

        # Create a self-signed certificate
        subject = issuer = x509.Name(
            [
                x509.NameAttribute(NameOID.COUNTRY_NAME, "CA"),
                x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "BC"),
                x509.NameAttribute(NameOID.LOCALITY_NAME, "Victoria"),
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Test Org"),
                x509.NameAttribute(NameOID.COMMON_NAME, "testuser"),
            ]
        )

        # Certificate valid for 1 hour from now
        now = datetime.datetime.now(datetime.timezone.utc)
        cert = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(issuer)
            .public_key(private_key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(now)
            .not_valid_after(now + datetime.timedelta(hours=1))
            .add_extension(
                x509.SubjectAlternativeName(
                    [
                        x509.DNSName("localhost"),
                    ]
                ),
                critical=False,
            )
            .sign(private_key, hashes.SHA256(), default_backend())
        )

        # Return PEM-encoded certificate
        return cert.public_bytes(serialization.Encoding.PEM).decode("utf-8")

    @pytest.fixture
    def temp_cert_file(self, mock_cert_content: str) -> Path:
        """Create a temporary certificate file for testing."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".pem", delete=False) as f:
            f.write(mock_cert_content)
            temp_path = Path(f.name)

        yield temp_path

        # Cleanup
        if temp_path.exists():
            temp_path.unlink()

    def test_gather_with_username_and_defaults(self) -> None:
        """Test gather function with username provided and default parameters."""
        mock_cert_content = (
            "-----BEGIN CERTIFICATE-----\nMOCK_CERT\n-----END CERTIFICATE-----"
        )

        with (
            patch("skaha.auth.x509.Subject") as mock_subject,
            patch("skaha.auth.x509.get_cert") as mock_get_cert,
            patch("skaha.auth.x509.inspect") as mock_inspect,
            patch("pathlib.Path.mkdir") as mock_mkdir,
            patch("pathlib.Path.write_text") as mock_write_text,
            patch("pathlib.Path.chmod") as mock_chmod,
        ):
            # Setup mocks
            mock_get_cert.return_value = mock_cert_content
            mock_inspect.return_value = {
                "path": "/home/user/.ssl/cadcproxy.pem",
                "expiry": time.time() + 3600,
            }

            # Call function
            result = gather(username="testuser", days_valid=10)

            # Verify calls
            mock_subject.assert_called_once_with(username="testuser")
            mock_get_cert.assert_called_once_with(
                subject=mock_subject.return_value, days_valid=10
            )
            mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)
            mock_write_text.assert_called_once_with(mock_cert_content)
            mock_chmod.assert_called_once_with(0o600)

            # Verify result
            assert "path" in result
            assert "expiry" in result

    def test_gather_without_username_prompts_input(self) -> None:
        """Test gather function prompts for username when not provided."""
        mock_cert_content = (
            "-----BEGIN CERTIFICATE-----\nMOCK_CERT\n-----END CERTIFICATE-----"
        )

        with (
            patch("builtins.input", return_value="prompted_user") as mock_input,
            patch("skaha.auth.x509.Subject") as mock_subject,
            patch("skaha.auth.x509.get_cert") as mock_get_cert,
            patch("skaha.auth.x509.inspect") as mock_inspect,
            patch("pathlib.Path.mkdir"),
            patch("pathlib.Path.write_text"),
            patch("pathlib.Path.chmod"),
        ):
            # Setup mocks
            mock_get_cert.return_value = mock_cert_content
            mock_inspect.return_value = {
                "path": "/home/user/.ssl/cadcproxy.pem",
                "expiry": time.time() + 3600,
            }

            # Call function without username
            gather()

            # Verify input was called
            mock_input.assert_called_once_with("Username: ")
            mock_subject.assert_called_once_with(username="prompted_user")

    def test_gather_with_custom_cert_path(self) -> None:
        """Test gather function with custom certificate path."""
        mock_cert_content = (
            "-----BEGIN CERTIFICATE-----\nMOCK_CERT\n-----END CERTIFICATE-----"
        )
        custom_path = Path("/custom/path/cert.pem")

        with (
            patch("skaha.auth.x509.Subject"),
            patch("skaha.auth.x509.get_cert") as mock_get_cert,
            patch("skaha.auth.x509.inspect") as mock_inspect,
            patch("pathlib.Path.mkdir"),
            patch("pathlib.Path.write_text"),
            patch("pathlib.Path.chmod"),
        ):
            # Setup mocks
            mock_get_cert.return_value = mock_cert_content
            mock_inspect.return_value = {
                "path": str(custom_path.absolute()),
                "expiry": time.time() + 3600,
            }

            # Call function with custom path
            gather(username="testuser", cert_path=custom_path)

            # Verify custom path was used
            mock_inspect.assert_called_once_with(custom_path)

    def test_gather_handles_get_cert_failure(self) -> None:
        """Test gather function handles get_cert failure properly."""
        with (
            patch("skaha.auth.x509.Subject"),
            patch("skaha.auth.x509.get_cert", side_effect=Exception("Auth failed")),
            pytest.raises(
                ValueError, match="Failed to obtain X509 certificate: Auth failed"
            ),
        ):
            gather(username="testuser")

    def test_gather_handles_file_write_failure(self) -> None:
        """Test gather function handles file write failure properly."""
        mock_cert_content = (
            "-----BEGIN CERTIFICATE-----\nMOCK_CERT\n-----END CERTIFICATE-----"
        )

        with (
            patch("skaha.auth.x509.Subject"),
            patch("skaha.auth.x509.get_cert", return_value=mock_cert_content),
            patch("pathlib.Path.mkdir"),
            patch(
                "pathlib.Path.write_text",
                side_effect=PermissionError("Permission denied"),
            ),
            pytest.raises(
                ValueError, match="Failed to obtain X509 certificate: Permission denied"
            ),
        ):
            gather(username="testuser")

    def test_inspect_with_valid_certificate(self, temp_cert_file: Path) -> None:
        """Test inspect function with a valid certificate file."""
        result = inspect(temp_cert_file)

        assert "path" in result
        assert "expiry" in result
        assert result["path"] == temp_cert_file.absolute().as_posix()
        assert isinstance(result["expiry"], float)
        assert result["expiry"] > time.time()  # Should be in the future

    def test_inspect_with_default_path(self) -> None:
        """Test inspect function with default certificate path."""
        mock_cert_content = (
            "-----BEGIN CERTIFICATE-----\nMOCK_CERT\n-----END CERTIFICATE-----"
        )

        with (
            patch("pathlib.Path.exists", return_value=True),
            patch("pathlib.Path.is_file", return_value=True),
            patch("pathlib.Path.read_text", return_value=mock_cert_content),
            patch("skaha.auth.x509.x509.load_pem_x509_certificate") as mock_load_cert,
        ):
            # Create a mock certificate with expiry
            mock_cert = Mock()
            mock_cert.not_valid_after_utc.timestamp.return_value = time.time() + 3600
            mock_load_cert.return_value = mock_cert

            result = inspect()

            assert "path" in result
            assert "expiry" in result
            # Should use default path
            expected_path = Path.home() / ".ssl" / "cadcproxy.pem"
            assert result["path"] == expected_path.absolute().as_posix()

    def test_inspect_file_does_not_exist(self) -> None:
        """Test inspect function when certificate file doesn't exist."""
        non_existent_path = Path("/nonexistent/cert.pem")

        with pytest.raises(ValueError, match="Failed to inspect certificate"):
            inspect(non_existent_path)

    def test_inspect_path_is_not_file(self) -> None:
        """Test inspect function when path exists but is not a file."""
        with tempfile.TemporaryDirectory() as temp_dir:
            dir_path = Path(temp_dir)

            with pytest.raises(ValueError, match="Failed to inspect certificate"):
                inspect(dir_path)

    def test_inspect_invalid_certificate_content(self) -> None:
        """Test inspect function with invalid certificate content."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".pem", delete=False) as f:
            f.write("INVALID CERTIFICATE CONTENT")
            temp_path = Path(f.name)

        try:
            with pytest.raises(ValueError, match="Failed to inspect certificate"):
                inspect(temp_path)
        finally:
            temp_path.unlink()

    def test_inspect_certificate_encoding_handling(self) -> None:
        """Test inspect function properly handles certificate encoding."""
        mock_cert_content = (
            "-----BEGIN CERTIFICATE-----\nMOCK_CERT\n-----END CERTIFICATE-----"
        )

        with (
            patch("pathlib.Path.exists", return_value=True),
            patch("pathlib.Path.is_file", return_value=True),
            patch("pathlib.Path.read_text") as mock_read_text,
            patch("skaha.auth.x509.x509.load_pem_x509_certificate") as mock_load_cert,
        ):
            mock_read_text.return_value = mock_cert_content
            mock_cert = Mock()
            mock_cert.not_valid_after_utc.timestamp.return_value = time.time() + 3600
            mock_load_cert.return_value = mock_cert

            inspect(Path("/test/cert.pem"))

            # Verify encoding is specified
            mock_read_text.assert_called_once_with(encoding="utf-8")
            # Verify content is encoded to bytes for cryptography
            mock_load_cert.assert_called_once_with(
                mock_cert_content.encode("utf-8"), default_backend()
            )

    def test_gather_creates_directory_structure(self) -> None:
        """Test that gather creates the necessary directory structure."""
        mock_cert_content = (
            "-----BEGIN CERTIFICATE-----\nMOCK_CERT\n-----END CERTIFICATE-----"
        )
        custom_path = Path("/deep/nested/path/cert.pem")

        with (
            patch("skaha.auth.x509.Subject"),
            patch("skaha.auth.x509.get_cert", return_value=mock_cert_content),
            patch("skaha.auth.x509.inspect") as mock_inspect,
            patch("pathlib.Path.mkdir") as mock_mkdir,
            patch("pathlib.Path.write_text"),
            patch("pathlib.Path.chmod"),
        ):
            mock_inspect.return_value = {
                "path": str(custom_path),
                "expiry": time.time() + 3600,
            }

            gather(username="testuser", cert_path=custom_path)

            # Verify parent directory creation
            mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)

    def test_gather_sets_secure_file_permissions(self) -> None:
        """Test that gather sets secure file permissions (600)."""
        mock_cert_content = (
            "-----BEGIN CERTIFICATE-----\nMOCK_CERT\n-----END CERTIFICATE-----"
        )

        with (
            patch("skaha.auth.x509.Subject"),
            patch("skaha.auth.x509.get_cert", return_value=mock_cert_content),
            patch("skaha.auth.x509.inspect") as mock_inspect,
            patch("pathlib.Path.mkdir"),
            patch("pathlib.Path.write_text"),
            patch("pathlib.Path.chmod") as mock_chmod,
        ):
            mock_inspect.return_value = {
                "path": "/test/cert.pem",
                "expiry": time.time() + 3600,
            }

            gather(username="testuser")

            # Verify secure permissions are set
            mock_chmod.assert_called_once_with(0o600)
