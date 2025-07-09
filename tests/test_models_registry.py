"""Comprehensive tests for the registry models module."""

import base64
import pytest
from pydantic import ValidationError

from skaha.models.registry import (
    IVOARegistrySearch,
    IVOARegistry,
    Server,
    ServerResults,
    ContainerRegistry,
)


class TestIVOARegistrySearch:
    """Test IVOARegistrySearch class."""

    def test_default_values(self) -> None:
        """Test default values for IVOARegistrySearch."""
        search = IVOARegistrySearch()
        
        # Check default registries
        assert "https://spsrc27.iaa.csic.es/reg/resource-caps" in search.registries
        assert search.registries["https://spsrc27.iaa.csic.es/reg/resource-caps"] == "SRCnet"
        assert "https://ws.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/reg/resource-caps" in search.registries
        assert search.registries["https://ws.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/reg/resource-caps"] == "CADC"
        
        # Check default names
        assert "ivo://canfar.net/src/skaha" in search.names
        assert search.names["ivo://canfar.net/src/skaha"] == "Canada"
        assert "ivo://cadc.nrc.ca/skaha" in search.names
        assert search.names["ivo://cadc.nrc.ca/skaha"] == "CANFAR"
        
        # Check default omit list
        assert ("CADC", "ivo://canfar.net/src/skaha") in search.omit
        
        # Check default excluded terms
        assert "dev" in search.excluded
        assert "test" in search.excluded
        assert "staging" in search.excluded

    def test_with_custom_values(self) -> None:
        """Test IVOARegistrySearch with custom values."""
        custom_registries = {"https://custom.registry.com": "Custom"}
        custom_names = {"ivo://custom.com/service": "Custom Service"}
        custom_omit = [("Custom", "ivo://custom.com/service")]
        custom_excluded = ("custom", "exclude")
        
        search = IVOARegistrySearch(
            registries=custom_registries,
            names=custom_names,
            omit=custom_omit,
            excluded=custom_excluded,
        )
        
        assert search.registries == custom_registries
        assert search.names == custom_names
        assert search.omit == custom_omit
        assert search.excluded == custom_excluded

    def test_all_default_registry_entries(self) -> None:
        """Test that all expected default registry entries are present."""
        search = IVOARegistrySearch()
        
        expected_names = {
            "ivo://canfar.net/src/skaha": "Canada",
            "ivo://swesrc.chalmers.se/skaha": "Sweden",
            "ivo://canfar.cam.uksrc.org/skaha": "UK-CAM",
            "ivo://canfar.ral.uksrc.org/skaha": "UK-RAL",
            "ivo://src.skach.org/skaha": "Swiss",
            "ivo://espsrc.iaa.csic.es/skaha": "Spain",
            "ivo://canfar.itsrc.oact.inaf.it/skaha": "Italy",
            "ivo://shion-sp.mtk.nao.ac.jp/skaha": "Japan",
            "ivo://canfar.krsrc.kr/skaha": "Korea",
            "ivo://canfar.ska.zverse.space/skaha": "China",
            "ivo://cadc.nrc.ca/skaha": "CANFAR",
        }
        
        for uri, name in expected_names.items():
            assert uri in search.names
            assert search.names[uri] == name


class TestIVOARegistry:
    """Test IVOARegistry class."""

    def test_default_values(self) -> None:
        """Test default values for IVOARegistry."""
        registry = IVOARegistry(name="Test Registry", content="<xml>content</xml>")
        
        assert registry.name == "Test Registry"
        assert registry.content == "<xml>content</xml>"
        assert registry.success is True
        assert registry.error is None

    def test_with_error(self) -> None:
        """Test IVOARegistry with error."""
        registry = IVOARegistry(
            name="Failed Registry",
            content="",
            success=False,
            error="Connection failed",
        )
        
        assert registry.name == "Failed Registry"
        assert registry.content == ""
        assert registry.success is False
        assert registry.error == "Connection failed"

    def test_required_fields(self) -> None:
        """Test that required fields are enforced."""
        # Missing name should raise ValidationError
        with pytest.raises(ValidationError):
            IVOARegistry(content="content")
        
        # Missing content should raise ValidationError
        with pytest.raises(ValidationError):
            IVOARegistry(name="name")


class TestServer:
    """Test Server class."""

    def test_required_fields(self) -> None:
        """Test Server with required fields."""
        server = Server(
            registry="CADC",
            uri="ivo://cadc.nrc.ca/skaha",
            url="https://ws-uv.canfar.net/skaha",
        )
        
        assert server.registry == "CADC"
        assert server.uri == "ivo://cadc.nrc.ca/skaha"
        assert server.url == "https://ws-uv.canfar.net/skaha"
        assert server.status is None
        assert server.name is None

    def test_with_optional_fields(self) -> None:
        """Test Server with optional fields."""
        server = Server(
            registry="SRCnet",
            uri="ivo://swesrc.chalmers.se/skaha",
            url="https://services.swesrc.chalmers.se/skaha",
            status=200,
            name="Sweden",
        )
        
        assert server.registry == "SRCnet"
        assert server.uri == "ivo://swesrc.chalmers.se/skaha"
        assert server.url == "https://services.swesrc.chalmers.se/skaha"
        assert server.status == 200
        assert server.name == "Sweden"

    def test_missing_required_fields(self) -> None:
        """Test that missing required fields raise ValidationError."""
        with pytest.raises(ValidationError):
            Server(uri="ivo://test.com", url="https://test.com")  # Missing registry
        
        with pytest.raises(ValidationError):
            Server(registry="Test", url="https://test.com")  # Missing uri
        
        with pytest.raises(ValidationError):
            Server(registry="Test", uri="ivo://test.com")  # Missing url


class TestServerResults:
    """Test ServerResults class."""

    def test_default_values(self) -> None:
        """Test default values for ServerResults."""
        results = ServerResults()
        
        assert results.endpoints == []
        assert results.total_time == 0.0
        assert results.registry_fetch_time == 0.0
        assert results.endpoint_check_time == 0.0
        assert results.found == 0
        assert results.checked == 0
        assert results.successful == 0

    def test_with_custom_values(self) -> None:
        """Test ServerResults with custom values."""
        endpoints = [
            Server(registry="CADC", uri="ivo://cadc.nrc.ca/skaha", url="https://ws-uv.canfar.net/skaha")
        ]
        
        results = ServerResults(
            endpoints=endpoints,
            total_time=5.5,
            registry_fetch_time=2.0,
            endpoint_check_time=3.5,
            found=10,
            checked=8,
            successful=6,
        )
        
        assert len(results.endpoints) == 1
        assert results.total_time == 5.5
        assert results.registry_fetch_time == 2.0
        assert results.endpoint_check_time == 3.5
        assert results.found == 10
        assert results.checked == 8
        assert results.successful == 6

    def test_add_method(self) -> None:
        """Test add method."""
        results = ServerResults()
        
        # Add successful endpoint
        successful_server = Server(
            registry="CADC",
            uri="ivo://cadc.nrc.ca/skaha",
            url="https://ws-uv.canfar.net/skaha",
            status=200,
        )
        results.add(successful_server)
        
        assert len(results.endpoints) == 1
        assert results.successful == 1
        
        # Add failed endpoint
        failed_server = Server(
            registry="Failed",
            uri="ivo://failed.com/skaha",
            url="https://failed.com/skaha",
            status=500,
        )
        results.add(failed_server)
        
        assert len(results.endpoints) == 2
        assert results.successful == 1  # Still 1, only 200 status counts

    def test_get_by_registry_method(self) -> None:
        """Test get_by_registry method."""
        results = ServerResults()
        
        cadc_server1 = Server(registry="CADC", uri="ivo://cadc1.com", url="https://cadc1.com")
        cadc_server2 = Server(registry="CADC", uri="ivo://cadc2.com", url="https://cadc2.com")
        srcnet_server = Server(registry="SRCnet", uri="ivo://srcnet.com", url="https://srcnet.com")
        
        results.add(cadc_server1)
        results.add(cadc_server2)
        results.add(srcnet_server)
        
        grouped = results.get_by_registry()
        
        assert "CADC" in grouped
        assert "SRCnet" in grouped
        assert len(grouped["CADC"]) == 2
        assert len(grouped["SRCnet"]) == 1
        assert grouped["CADC"][0] == cadc_server1
        assert grouped["CADC"][1] == cadc_server2
        assert grouped["SRCnet"][0] == srcnet_server


class TestContainerRegistry:
    """Test ContainerRegistry class."""

    def test_default_values(self) -> None:
        """Test default values for ContainerRegistry."""
        registry = ContainerRegistry()
        
        assert registry.url is None
        assert registry.username is None
        assert registry.secret is None

    def test_with_all_values(self) -> None:
        """Test ContainerRegistry with all values."""
        registry = ContainerRegistry(
            url="https://registry.example.com",
            username="testuser",
            secret="testsecret",
        )

        assert str(registry.url) == "https://registry.example.com/"  # pydantic adds trailing slash
        assert registry.username == "testuser"
        assert registry.secret == "testsecret"

    def test_validation_username_without_secret(self) -> None:
        """Test validation fails when username provided without secret."""
        with pytest.raises(ValidationError, match="container registry secret is required"):
            ContainerRegistry(username="testuser")

    def test_validation_secret_without_username(self) -> None:
        """Test validation fails when secret provided without username."""
        with pytest.raises(ValidationError, match="container registry username is required"):
            ContainerRegistry(secret="testsecret")

    def test_validation_both_username_and_secret(self) -> None:
        """Test validation passes when both username and secret provided."""
        registry = ContainerRegistry(username="testuser", secret="testsecret")
        assert registry.username == "testuser"
        assert registry.secret == "testsecret"

    def test_validation_neither_username_nor_secret(self) -> None:
        """Test validation passes when neither username nor secret provided."""
        registry = ContainerRegistry()
        assert registry.username is None
        assert registry.secret is None

    def test_encoded_method(self) -> None:
        """Test encoded method."""
        registry = ContainerRegistry(username="testuser", secret="testsecret")
        
        expected = base64.b64encode(b"testuser:testsecret").decode()
        assert registry.encoded() == expected

    def test_encoded_method_with_special_characters(self) -> None:
        """Test encoded method with special characters."""
        registry = ContainerRegistry(username="user@domain.com", secret="p@ssw0rd!")
        
        expected = base64.b64encode(b"user@domain.com:p@ssw0rd!").decode()
        assert registry.encoded() == expected

    def test_url_validation(self) -> None:
        """Test URL field validation."""
        # Valid URLs
        registry = ContainerRegistry(url="https://registry.example.com")
        assert str(registry.url) == "https://registry.example.com/"  # pydantic adds trailing slash

        registry = ContainerRegistry(url="http://localhost:5000")
        assert str(registry.url) == "http://localhost:5000/"  # pydantic adds trailing slash

        # Invalid URLs
        with pytest.raises(ValidationError):
            ContainerRegistry(url="not-a-valid-url")

        with pytest.raises(ValidationError):
            ContainerRegistry(url="ftp://registry.com")  # Not HTTP/HTTPS

    def test_username_length_validation(self) -> None:
        """Test username length validation."""
        # Valid lengths
        registry = ContainerRegistry(username="a", secret="secret")  # Min length
        assert registry.username == "a"
        
        registry = ContainerRegistry(username="a" * 255, secret="secret")  # Max length
        assert len(registry.username) == 255
        
        # Invalid lengths
        with pytest.raises(ValidationError):
            ContainerRegistry(username="", secret="secret")  # Too short
        
        with pytest.raises(ValidationError):
            ContainerRegistry(username="a" * 256, secret="secret")  # Too long

    def test_secret_length_validation(self) -> None:
        """Test secret length validation."""
        # Valid lengths
        registry = ContainerRegistry(username="user", secret="s")  # Min length
        assert registry.secret == "s"
        
        registry = ContainerRegistry(username="user", secret="s" * 255)  # Max length
        assert len(registry.secret) == 255
        
        # Invalid lengths
        with pytest.raises(ValidationError):
            ContainerRegistry(username="user", secret="")  # Too short
        
        with pytest.raises(ValidationError):
            ContainerRegistry(username="user", secret="s" * 256)  # Too long
