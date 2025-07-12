"""Test Skaha Client API."""
# ruff: noqa: SLF001

import ssl
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import Mock, patch

import httpx
import pytest
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID
from pydantic import SecretStr, ValidationError

from skaha.client import SkahaClient
from skaha.models.registry import ContainerRegistry


def test_client_has_session_attribute():
    """Test if it SkahaClient object contains requests.Session attribute."""
    client = SkahaClient(token="test_token")
    assert hasattr(client, "client")
    assert isinstance(client.client, httpx.Client)


def test_client_session():
    """Test SkahaClient object's session attribute contains ther right headers."""
    headers = [
        "x-skaha-server",
        "content-type",
        "accept",
        "user-agent",
        "date",
        "x-skaha-registry-auth",
    ]
    registry = ContainerRegistry(username="test", secret="test")
    skaha = SkahaClient(registry=registry, token="test_token", loglevel=30)
    assert any(header in skaha.client.headers for header in headers)


def test_bad_server_no_schema():
    """Test server URL without schema."""
    with pytest.raises(ValidationError):
        SkahaClient(url="ws-uv.canfar.net")


def test_default_certificate():
    """Test validation with default certificate value."""
    try:
        SkahaClient()
    except ValidationError as err:
        raise AssertionError from err
    assert True


def test_bad_certificate():
    """Test bad certificate."""
    with pytest.raises(FileNotFoundError):
        SkahaClient(certificate="abcdefd")


def test_bad_certificate_path():
    """Test bad certificate."""
    with pytest.raises(FileNotFoundError):
        SkahaClient(certificate="/gibberish/path")  # nosec: B108


def test_token_setup():
    """Test token setup."""
    token: str = "abcdef"
    skaha = SkahaClient(token=token)
    assert skaha.token.get_secret_value() == token
    assert skaha.client.headers["Authorization"] == f"Bearer {token}"


def _create_test_certificate(
    path: Path, expired: bool = False, not_yet_valid: bool = False
) -> None:
    """Create a test certificate for testing purposes.

    Args:
        path: Path where to save the certificate
        expired: Whether to create an expired certificate
        not_yet_valid: Whether to create a certificate that's not yet valid
    """
    # Generate private key
    private_key = rsa.generate_private_key(
        public_exponent=65537, key_size=2048, backend=default_backend()
    )

    # Create certificate
    subject = issuer = x509.Name(
        [
            x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Test"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, "Test"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Test"),
            x509.NameAttribute(NameOID.COMMON_NAME, "test.example.com"),
        ]
    )

    now = datetime.now(timezone.utc)
    if expired:
        not_valid_before = now - timedelta(days=365)
        not_valid_after = now - timedelta(days=1)
    elif not_yet_valid:
        not_valid_before = now + timedelta(days=1)
        not_valid_after = now + timedelta(days=365)
    else:
        not_valid_before = now - timedelta(days=1)
        not_valid_after = now + timedelta(days=365)

    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(private_key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(not_valid_before)
        .not_valid_after(not_valid_after)
        .add_extension(
            x509.SubjectAlternativeName(
                [
                    x509.DNSName("test.example.com"),
                ]
            ),
            critical=False,
        )
        .sign(private_key, hashes.SHA256(), default_backend())
    )

    # Write certificate and private key to file
    with path.open("wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))
        f.write(
            private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption(),
            )
        )


class TestCertificateValidation:
    """Test certificate validation functionality."""

    def test_certificate_validation_with_token_skips_validation(self, tmp_path):
        """Test certificate validation skipped when token provided (line 148)."""
        # Create a valid certificate file for this test
        cert_path = tmp_path / "valid.pem"
        _create_test_certificate(cert_path)

        # Even with a valid certificate, when token is provided, it should use the token
        client = SkahaClient(token=SecretStr("test-token"), certificate=cert_path)
        assert client.token is not None
        assert client.certificate == cert_path

        # Verify that the client uses token authentication
        headers = client._get_headers()
        assert "Authorization" in headers
        assert headers["Authorization"] == "Bearer test-token"

    def test_certificate_file_not_exists(self, tmp_path):
        """Test certificate validation when file doesn't exist (lines 154-155)."""
        cert_path = tmp_path / "nonexistent.pem"

        # The resolve(strict=True) call happens first, so we get a FileNotFoundError
        with pytest.raises(FileNotFoundError):
            SkahaClient(certificate=cert_path)

    def test_certificate_not_readable(self, tmp_path):
        """Test certificate validation when file is not readable."""
        cert_path = tmp_path / "test.pem"
        # Create a valid certificate file first
        _create_test_certificate(cert_path)

        with (
            patch("skaha.client.access", return_value=False),
            pytest.raises(PermissionError, match="cert file .* is not readable"),
        ):
            SkahaClient(certificate=cert_path)

    def test_certificate_expired(self, tmp_path):
        """Test certificate validation with expired certificate (lines 166-168)."""
        cert_path = tmp_path / "expired.pem"
        _create_test_certificate(cert_path, expired=True)

        with pytest.raises(ValueError, match="cert .* expired"):
            SkahaClient(certificate=cert_path)

    def test_certificate_not_yet_valid(self, tmp_path):
        """Test certificate validation with not-yet-valid cert (lines 169-171)."""
        cert_path = tmp_path / "future.pem"
        _create_test_certificate(cert_path, not_yet_valid=True)

        with pytest.raises(ValueError, match="cert .* not valid yet"):
            SkahaClient(certificate=cert_path)

    def test_certificate_valid(self, tmp_path):
        """Test certificate validation with valid certificate (line 172)."""
        cert_path = tmp_path / "valid.pem"
        _create_test_certificate(cert_path)

        # Should not raise an error
        client = SkahaClient(certificate=cert_path)
        assert client.certificate == cert_path


class TestExpiryProperty:
    """Test the expiry property for different authentication modes."""

    def test_expiry_with_user_token(self):
        """Test expiry returns None when user provides token (lines 209-211)."""
        client = SkahaClient(token=SecretStr("test-token"))
        assert client.expiry is None

    def test_expiry_with_user_certificate(self, tmp_path):
        """Test expiry returns None when user provides certificate (lines 209-211)."""
        cert_path = tmp_path / "test.pem"
        _create_test_certificate(cert_path)

        client = SkahaClient(certificate=cert_path)
        assert client.expiry is None

    @patch("skaha.client.SkahaClient._check_certificate")
    def test_expiry_oidc_mode(self, mock_check_cert):
        """Test expiry returns OIDC access token expiry (lines 214-217)."""
        mock_check_cert.return_value = None

        # Create mock auth with OIDC mode
        mock_auth = Mock()
        mock_auth.mode = "oidc"
        mock_auth.oidc.expiry.access = 1234567890

        client = SkahaClient()
        client.auth = mock_auth

        assert client.expiry == 1234567890

    @patch("skaha.client.SkahaClient._check_certificate")
    def test_expiry_x509_mode(self, mock_check_cert):
        """Test expiry returns X509 expiry (lines 218-221)."""
        mock_check_cert.return_value = None

        # Create mock auth with X509 mode
        mock_auth = Mock()
        mock_auth.mode = "x509"
        mock_auth.x509.expiry = 9876543210

        client = SkahaClient()
        client.auth = mock_auth

        assert client.expiry == 9876543210

    @patch("skaha.client.SkahaClient._check_certificate")
    def test_expiry_default_mode(self, mock_check_cert):
        """Test expiry returns default expiry (lines 222-225)."""
        mock_check_cert.return_value = None

        # Create mock auth with default mode
        mock_auth = Mock()
        mock_auth.mode = "default"
        mock_auth.default.expiry = 5555555555

        client = SkahaClient()
        client.auth = mock_auth

        assert client.expiry == 5555555555

    @patch("skaha.client.SkahaClient._check_certificate")
    def test_expiry_unknown_mode(self, mock_check_cert):
        """Test expiry returns None for unknown auth mode (lines 226-227)."""
        mock_check_cert.return_value = None

        # Create mock auth with unknown mode
        mock_auth = Mock()
        mock_auth.mode = "unknown"

        client = SkahaClient()
        client.auth = mock_auth

        assert client.expiry is None


class TestSSLContextAndClientKwargs:
    """Test SSL context creation and client kwargs generation."""

    @patch("skaha.client.SkahaClient._check_certificate")
    def test_get_client_kwargs_with_certificate(self, mock_check_cert, tmp_path):
        """Test client kwargs with certificate authentication (lines 269-272)."""
        mock_check_cert.return_value = None
        cert_path = tmp_path / "test.pem"
        _create_test_certificate(cert_path)

        client = SkahaClient(certificate=cert_path)
        kwargs = client._get_client_kwargs(is_async=False)

        assert "verify" in kwargs
        assert isinstance(kwargs["verify"], ssl.SSLContext)

    @patch("skaha.client.SkahaClient._check_certificate")
    def test_get_client_kwargs_default_mode(self, mock_check_cert, tmp_path):
        """Test client kwargs with default authentication mode (lines 273-279)."""
        mock_check_cert.return_value = None
        cert_path = tmp_path / "test.pem"
        _create_test_certificate(cert_path)

        # Create mock auth with default mode
        mock_auth = Mock()
        mock_auth.mode = "default"
        mock_auth.default.path = cert_path

        client = SkahaClient()
        client.auth = mock_auth

        kwargs = client._get_client_kwargs(is_async=False)

        assert "verify" in kwargs
        assert isinstance(kwargs["verify"], ssl.SSLContext)

    @patch("skaha.client.SkahaClient._check_certificate")
    def test_get_ssl_context_file_not_exists(self, mock_check_cert, tmp_path):
        """Test SSL context creation when cert file doesn't exist (lines 336-338)."""
        mock_check_cert.return_value = None
        cert_path = tmp_path / "nonexistent.pem"

        client = SkahaClient()

        with pytest.raises(FileNotFoundError, match="Certificate path .* does not"):
            client._get_ssl_context(cert_path)

    @patch("skaha.client.SkahaClient._check_certificate")
    def test_get_ssl_context_valid_certificate(self, mock_check_cert, tmp_path):
        """Test SSL context creation with valid certificate."""
        mock_check_cert.return_value = None
        cert_path = tmp_path / "test.pem"
        _create_test_certificate(cert_path)

        client = SkahaClient()
        ssl_context = client._get_ssl_context(cert_path)

        assert isinstance(ssl_context, ssl.SSLContext)
        assert ssl_context.minimum_version == ssl.TLSVersion.TLSv1_2


class TestHeaderGeneration:
    """Test HTTP header generation for different authentication modes."""

    @patch("skaha.client.SkahaClient._check_certificate")
    def test_get_headers_oidc_no_token_error(self, mock_check_cert):
        """Test header generation error when OIDC has no token (lines 406-408)."""
        mock_check_cert.return_value = None

        # Create mock auth with OIDC mode but no token
        mock_auth = Mock()
        mock_auth.mode = "oidc"
        mock_auth.oidc.token.access = None

        client = SkahaClient()
        client.auth = mock_auth

        with pytest.raises(ValueError, match="OIDC mode selected but no access token"):
            client._get_headers()

    @patch("skaha.client.SkahaClient._check_certificate")
    def test_get_headers_x509_mode(self, mock_check_cert):
        """Test header generation for X509 mode (lines 409-414)."""
        mock_check_cert.return_value = None

        # Create mock auth with X509 mode
        mock_auth = Mock()
        mock_auth.mode = "x509"

        client = SkahaClient()
        client.auth = mock_auth

        headers = client._get_headers()
        assert headers["X-Skaha-Authentication-Type"] == "certificate"

    @patch("skaha.client.SkahaClient._check_certificate")
    def test_get_headers_default_mode(self, mock_check_cert):
        """Test header generation for default mode (lines 409-414)."""
        mock_check_cert.return_value = None

        # Create mock auth with default mode
        mock_auth = Mock()
        mock_auth.mode = "default"

        client = SkahaClient()
        client.auth = mock_auth

        headers = client._get_headers()
        assert headers["X-Skaha-Authentication-Type"] == "certificate"

    @patch("skaha.client.SkahaClient._check_certificate")
    def test_get_headers_with_certificate(self, mock_check_cert, tmp_path):
        """Test header generation with user-provided certificate (lines 409-414)."""
        mock_check_cert.return_value = None
        cert_path = tmp_path / "test.pem"
        _create_test_certificate(cert_path)

        client = SkahaClient(certificate=cert_path)
        headers = client._get_headers()

        assert headers["X-Skaha-Authentication-Type"] == "certificate"

    @patch("skaha.client.SkahaClient._check_certificate")
    def test_get_headers_with_registry(self, mock_check_cert):
        """Test header generation with registry authentication (lines 416-422)."""
        mock_check_cert.return_value = None

        registry = ContainerRegistry(username="test", secret="test")
        client = SkahaClient(registry=registry, token=SecretStr("test-token"))

        headers = client._get_headers()
        assert "X-Skaha-Registry-Auth" in headers


class TestContextManagers:
    """Test context manager functionality."""

    @patch("skaha.client.SkahaClient._check_certificate")
    def test_sync_context_manager_enter_exit(self, mock_check_cert):
        """Test synchronous context manager entry and exit (lines 439-440, 449-450)."""
        mock_check_cert.return_value = None

        client = SkahaClient(token=SecretStr("test-token"))

        # Test __enter__
        with client as ctx_client:
            assert ctx_client is client

        # __exit__ is called automatically

    @patch("skaha.client.SkahaClient._check_certificate")
    def test_sync_session_context(self, mock_check_cert):
        """Test synchronous session context manager (lines 430-435)."""
        mock_check_cert.return_value = None

        client = SkahaClient(token=SecretStr("test-token"))

        with client._session() as session:
            assert isinstance(session, httpx.Client)

    @patch("skaha.client.SkahaClient._check_certificate")
    def test_close_sync_client(self, mock_check_cert):
        """Test closing synchronous client (lines 454-460)."""
        mock_check_cert.return_value = None

        client = SkahaClient(token=SecretStr("test-token"))

        # Access client to create it
        _ = client.client
        assert client._client is not None

        # Close it
        client._close()
        assert client._client is None

    @patch("skaha.client.SkahaClient._check_certificate")
    def test_close_sync_client_when_none(self, mock_check_cert):
        """Test closing synchronous client when it's None (lines 459-460)."""
        mock_check_cert.return_value = None

        client = SkahaClient(token=SecretStr("test-token"))

        # Don't access client, so it remains None
        assert client._client is None

        # Close should not raise an error
        client._close()
        assert client._client is None

    @patch("skaha.client.SkahaClient._check_certificate")
    async def test_async_context_manager_enter_exit(self, mock_check_cert):
        """Test asynchronous context manager entry and exit (lines 474-475, 484-485)."""
        mock_check_cert.return_value = None

        client = SkahaClient(token=SecretStr("test-token"))

        # Test __aenter__
        async with client as ctx_client:
            assert ctx_client is client

        # __aexit__ is called automatically

    @patch("skaha.client.SkahaClient._check_certificate")
    async def test_async_session_context(self, mock_check_cert):
        """Test asynchronous session context manager (lines 465-470)."""
        mock_check_cert.return_value = None

        client = SkahaClient(token=SecretStr("test-token"))

        async with client._asession() as session:
            assert isinstance(session, httpx.AsyncClient)

    @patch("skaha.client.SkahaClient._check_certificate")
    async def test_aclose_async_client(self, mock_check_cert):
        """Test closing asynchronous client (lines 489-495)."""
        mock_check_cert.return_value = None

        client = SkahaClient(token=SecretStr("test-token"))

        # Access asynclient to create it
        _ = client.asynclient
        assert client._asynclient is not None

        # Close it
        await client._aclose()
        assert client._asynclient is None

    @patch("skaha.client.SkahaClient._check_certificate")
    async def test_aclose_async_client_when_none(self, mock_check_cert):
        """Test closing asynchronous client when it's None (lines 494-495)."""
        mock_check_cert.return_value = None

        client = SkahaClient(token=SecretStr("test-token"))

        # Don't access asynclient, so it remains None
        assert client._asynclient is None

        # Close should not raise an error
        await client._aclose()
        assert client._asynclient is None


def test_non_readible_certfile():
    """Test non-readable certificate file."""
    with tempfile.NamedTemporaryFile(delete=False) as temp:
        temp_path = temp.name
    # Change the permissions
    Path(temp_path).chmod(0o000)
    with pytest.raises(PermissionError):
        SkahaClient(certificate=temp_path)
