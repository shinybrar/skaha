"""Tests for the JWT utilities module."""

import base64
import json

import pytest

from skaha.utils.jwt import expiry


def test_expiry_with_valid_jwt():
    """Test expiry function with a valid JWT token."""
    # Create a mock JWT token with expiry
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {"exp": 1234567890, "sub": "user123"}

    # Encode the parts
    header_encoded = (
        base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip("=")
    )
    payload_encoded = (
        base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
    )
    signature = "fake_signature"

    token = f"{header_encoded}.{payload_encoded}.{signature}"

    result = expiry(token)
    assert result == 1234567890.0


def test_expiry_with_exp_in_header():
    """Test expiry function when exp is in header (edge case)."""
    # Create a mock JWT token with expiry in header
    header = {"alg": "HS256", "typ": "JWT", "exp": 9876543210}
    payload = {"sub": "user123"}

    # Encode the parts
    header_encoded = (
        base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip("=")
    )
    payload_encoded = (
        base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
    )
    signature = "fake_signature"

    token = f"{header_encoded}.{payload_encoded}.{signature}"

    result = expiry(token)
    assert result == 9876543210.0


def test_expiry_with_no_exp_field():
    """Test expiry function with JWT token that has no exp field."""
    # Create a mock JWT token without expiry
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {"sub": "user123", "iat": 1234567890}

    # Encode the parts
    header_encoded = (
        base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip("=")
    )
    payload_encoded = (
        base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
    )
    signature = "fake_signature"

    token = f"{header_encoded}.{payload_encoded}.{signature}"

    with pytest.raises(ValueError, match="Failed to decode JWT token"):
        expiry(token)


def test_expiry_with_invalid_json():
    """Test expiry function with invalid JSON in JWT token."""
    # Create a token with invalid JSON
    header_encoded = base64.urlsafe_b64encode(b"invalid_json").decode().rstrip("=")
    payload_encoded = base64.urlsafe_b64encode(b"also_invalid").decode().rstrip("=")
    signature = "fake_signature"

    token = f"{header_encoded}.{payload_encoded}.{signature}"

    with pytest.raises(ValueError, match="Failed to decode JWT token"):
        expiry(token)


def test_expiry_with_invalid_base64():
    """Test expiry function with invalid base64 encoding."""
    # Create a token with invalid base64
    token = "invalid.base64.token"

    with pytest.raises(ValueError, match="Failed to decode JWT token"):
        expiry(token)


def test_expiry_with_malformed_token():
    """Test expiry function with malformed token structure."""
    # Token with only one part
    token = "single_part"

    with pytest.raises(ValueError, match="Failed to decode JWT token"):
        expiry(token)


def test_expiry_padding_function():
    """Test that the internal padding function works correctly."""
    # This tests the padding logic indirectly through the main function
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {"exp": 1234567890}

    # Create base64 without padding to test padding logic
    header_json = json.dumps(header)
    payload_json = json.dumps(payload)

    # Encode without padding
    header_encoded = base64.urlsafe_b64encode(header_json.encode()).decode().rstrip("=")
    payload_encoded = (
        base64.urlsafe_b64encode(payload_json.encode()).decode().rstrip("=")
    )
    signature = "sig"

    token = f"{header_encoded}.{payload_encoded}.{signature}"

    result = expiry(token)
    assert result == 1234567890.0
