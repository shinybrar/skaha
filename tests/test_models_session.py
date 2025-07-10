"""Comprehensive tests for the session models module."""

import warnings
from typing import TYPE_CHECKING, Any

import pytest
from pydantic import ValidationError

from skaha.models.session import CreateRequest, FetchRequest, FetchResponse

if TYPE_CHECKING:
    from skaha.models.types import Kind, Status


class TestCreateSpec:
    """Test CreateSpec class."""

    def test_required_fields(self) -> None:
        """Test CreateSpec with required fields only."""
        spec = CreateRequest(
            name="test-session",
            image="images.canfar.net/skaha/terminal:1.1.1",
            kind="headless",
        )

        assert spec.name == "test-session"
        assert spec.image == "images.canfar.net/skaha/terminal:1.1.1"
        assert spec.kind == "headless"
        assert spec.cores == 1  # default
        assert spec.ram == 4  # default
        assert spec.replicas == 1  # default
        assert spec.gpus is None
        assert spec.cmd is None
        assert spec.args is None
        assert spec.env is None

    def test_with_all_fields(self) -> None:
        """Test CreateSpec with all fields."""
        env_vars = {"FOO": "BAR", "DEBUG": "true"}

        spec = CreateRequest(
            name="full-session",
            image="custom/image:latest",
            kind="headless",
            cores=8,
            ram=16,
            gpus=2,
            cmd="python",
            args="script.py --verbose",
            env=env_vars,
            replicas=3,
        )

        assert spec.name == "full-session"
        assert spec.image == "custom/image:latest"
        assert spec.kind == "headless"
        assert spec.cores == 8
        assert spec.ram == 16
        assert spec.gpus == 2
        assert spec.cmd == "python"
        assert spec.args == "script.py --verbose"
        assert spec.env == env_vars
        assert spec.replicas == 3

    def test_cores_validation(self) -> None:
        """Test cores field validation."""
        # Valid values
        spec = CreateRequest(name="test", image="test:latest", kind="headless", cores=1)
        assert spec.cores == 1

        spec = CreateRequest(
            name="test", image="test:latest", kind="headless", cores=256
        )
        assert spec.cores == 256

        # Invalid values
        with pytest.raises(ValidationError):
            CreateRequest(name="test", image="test:latest", kind="headless", cores=0)

        with pytest.raises(ValidationError):
            CreateRequest(name="test", image="test:latest", kind="headless", cores=257)

    def test_ram_validation(self) -> None:
        """Test RAM field validation."""
        # Valid values
        spec = CreateRequest(name="test", image="test:latest", kind="headless", ram=1)
        assert spec.ram == 1

        spec = CreateRequest(name="test", image="test:latest", kind="headless", ram=512)
        assert spec.ram == 512

        # Invalid values
        with pytest.raises(ValidationError):
            CreateRequest(name="test", image="test:latest", kind="headless", ram=0)

        with pytest.raises(ValidationError):
            CreateRequest(name="test", image="test:latest", kind="headless", ram=513)

    def test_gpus_validation(self) -> None:
        """Test GPUs field validation."""
        # Valid values
        spec = CreateRequest(name="test", image="test:latest", kind="headless", gpus=1)
        assert spec.gpus == 1

        spec = CreateRequest(name="test", image="test:latest", kind="headless", gpus=28)
        assert spec.gpus == 28

        # Invalid values
        with pytest.raises(ValidationError):
            CreateRequest(name="test", image="test:latest", kind="headless", gpus=0)

        with pytest.raises(ValidationError):
            CreateRequest(name="test", image="test:latest", kind="headless", gpus=29)

    def test_replicas_validation(self) -> None:
        """Test replicas field validation."""
        # Valid values
        spec = CreateRequest(
            name="test", image="test:latest", kind="headless", replicas=1
        )
        assert spec.replicas == 1

        spec = CreateRequest(
            name="test", image="test:latest", kind="headless", replicas=512
        )
        assert spec.replicas == 512

        # Invalid values
        with pytest.raises(ValidationError):
            CreateRequest(name="test", image="test:latest", kind="headless", replicas=0)

        with pytest.raises(ValidationError):
            CreateRequest(
                name="test", image="test:latest", kind="headless", replicas=513
            )

    def test_kind_validation(self) -> None:
        """Test kind field validation."""
        # Valid kinds
        valid_kinds = ["desktop", "notebook", "carta", "headless", "firefly"]
        for kind in valid_kinds:
            spec = CreateRequest(name="test", image="test:latest", kind=kind)
            assert spec.kind == kind

        # Invalid kind
        with pytest.raises(ValidationError):
            CreateRequest(name="test", image="test:latest", kind="invalid")

    def test_headless_validation_success(self) -> None:
        """Test that cmd, args, env are allowed for headless sessions."""
        spec = CreateRequest(
            name="test",
            image="test:latest",
            kind="headless",
            cmd="python",
            args="script.py",
            env={"VAR": "value"},
        )

        assert spec.cmd == "python"
        assert spec.args == "script.py"
        assert spec.env == {"VAR": "value"}

    def test_non_headless_validation_failure(self) -> None:
        """Test that cmd, args, env are not allowed for non-headless sessions."""
        non_headless_kinds = ["desktop", "notebook", "carta", "firefly"]

        for kind in non_headless_kinds:
            # Test cmd restriction
            with pytest.raises(
                ValidationError, match="cmd, args, env only allowed for headless"
            ):
                CreateRequest(name="test", image="test:latest", kind=kind, cmd="python")

            # Test args restriction
            with pytest.raises(
                ValidationError, match="cmd, args, env only allowed for headless"
            ):
                CreateRequest(
                    name="test", image="test:latest", kind=kind, args="--verbose"
                )

            # Test env restriction
            with pytest.raises(
                ValidationError, match="cmd, args, env only allowed for headless"
            ):
                CreateRequest(
                    name="test", image="test:latest", kind=kind, env={"VAR": "value"}
                )

    def test_firefly_desktop_warnings(self) -> None:
        """Test warnings for firefly and desktop sessions."""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            # Test firefly with ignored parameters
            CreateRequest(
                name="test",
                image="test:latest",
                kind="firefly",
                cores=8,  # Should be ignored
                ram=16,  # Should be ignored
            )

            # Should have warnings about ignored parameters
            assert len(w) > 0
            assert "ignored for firefly sessions" in str(w[0].message)

    def test_firefly_desktop_replicas_validation(self) -> None:
        """Test that firefly and desktop sessions cannot have multiple replicas."""
        for kind in ["firefly", "desktop"]:
            with pytest.raises(
                ValidationError, match=f"multiple replicas invalid for {kind}"
            ):
                CreateRequest(
                    name="test",
                    image="test:latest",
                    kind=kind,
                    replicas=2,
                )

    def test_serialization_alias(self) -> None:
        """Test that kind field uses 'type' as serialization alias."""
        spec = CreateRequest(name="test", image="test:latest", kind="headless")

        # Test model dump with by_alias=True uses 'type' instead of 'kind'
        data = spec.model_dump(by_alias=True)
        assert "type" in data
        assert "kind" not in data
        assert data["type"] == "headless"

    def test_replicas_excluded_from_serialization(self) -> None:
        """Test that replicas field is excluded from serialization."""
        spec = CreateRequest(
            name="test", image="test:latest", kind="headless", replicas=5
        )

        data = spec.model_dump()
        assert "replicas" not in data

        # But should be accessible directly
        assert spec.replicas == 5

    def test_populate_by_name(self) -> None:
        """Test that model can be populated by field name or alias."""
        # Using field name 'kind' (serialization_alias doesn't affect input)
        data = {"name": "test", "image": "test:latest", "kind": "notebook"}
        spec = CreateRequest.model_validate(data)
        assert spec.kind == "notebook"

        # Test that the model config allows populate_by_name
        assert spec.model_config["populate_by_name"] is True


class TestFetchSpec:
    """Test FetchSpec class."""

    def test_default_values(self) -> None:
        """Test default values for FetchSpec."""
        spec = FetchRequest()

        assert spec.kind is None
        assert spec.status is None
        assert spec.view is None

    def test_with_all_values(self) -> None:
        """Test FetchSpec with all values."""
        spec = FetchRequest(
            type="headless",  # Using alias
            status="Running",
            view="all",
        )

        assert spec.kind == "headless"
        assert spec.status == "Running"
        assert spec.view == "all"

    def test_kind_validation(self) -> None:
        """Test kind field validation."""
        # Valid kinds
        valid_kinds = ["desktop", "notebook", "carta", "headless", "firefly"]
        for kind in valid_kinds:
            spec = FetchRequest(type=kind)  # Using alias
            assert spec.kind == kind

        # None is also valid (default)
        spec = FetchRequest()
        assert spec.kind is None

    def test_status_validation(self) -> None:
        """Test status field validation."""
        # Valid statuses
        valid_statuses = ["Pending", "Running", "Terminating", "Succeeded", "Error"]
        for status in valid_statuses:
            spec = FetchRequest(status=status)
            assert spec.status == status

        # None is also valid (default)
        spec = FetchRequest()
        assert spec.status is None

    def test_view_validation(self) -> None:
        """Test view field validation."""
        # Valid view
        spec = FetchRequest(view="all")
        assert spec.view == "all"

        # None is also valid (default)
        spec = FetchRequest()
        assert spec.view is None

    def test_kind_alias(self) -> None:
        """Test that kind field uses 'type' as alias."""
        # Using alias 'type'
        data = {"type": "notebook"}
        spec = FetchRequest.model_validate(data)
        assert spec.kind == "notebook"

        # Using field name 'kind' (with populate_by_name=True)
        data = {"kind": "notebook"}
        spec = FetchRequest.model_validate(data)
        assert spec.kind == "notebook"

    def test_populate_by_name(self) -> None:
        """Test that model can be populated by field name or alias."""
        # Test with all fields using aliases
        data = {"type": "headless", "status": "Running", "view": "all"}
        spec = FetchRequest.model_validate(data)
        assert spec.kind == "headless"
        assert spec.status == "Running"
        assert spec.view == "all"

    def test_model_config(self) -> None:
        """Test model configuration settings."""
        spec = FetchRequest()

        # Test that validate_assignment is enabled
        spec.kind = "notebook"
        assert spec.kind == "notebook"

        # Test that populate_by_name is enabled
        assert "populate_by_name" in spec.model_config
        assert spec.model_config["populate_by_name"] is True


class TestSessionModelsIntegration:
    """Test integration between session models."""

    def test_create_and_fetch_spec_compatibility(self) -> None:
        """Test that CreateSpec and FetchSpec use compatible types."""
        # Create a session
        create_spec = CreateRequest(
            name="integration-test",
            image="test:latest",
            kind="notebook",
        )

        # Fetch sessions of the same kind
        fetch_spec = FetchRequest(type=create_spec.kind)  # Using alias

        assert fetch_spec.kind == "notebook"
        assert fetch_spec.kind == create_spec.kind

    def test_all_kind_values_work(self) -> None:
        """Test that all Kind values work in both models."""
        valid_kinds = ["desktop", "notebook", "carta", "headless", "firefly"]

        for kind in valid_kinds:
            # Should work in CreateSpec
            create_spec = CreateRequest(name="test", image="test:latest", kind=kind)
            assert create_spec.kind == kind

            # Should work in FetchSpec
            fetch_spec = FetchRequest(type=kind)  # Using alias
            assert fetch_spec.kind == kind

    def test_realistic_session_workflow(self) -> None:
        """Test a realistic session creation and fetching workflow."""
        # Create a headless session with custom parameters
        create_spec = CreateRequest(
            name="data-processing",
            image="python:3.9",
            kind="headless",
            cores=4,
            ram=8,
            cmd="python",
            args="process_data.py",
            env={"DATA_PATH": "/data", "OUTPUT_PATH": "/output"},
        )

        assert create_spec.name == "data-processing"
        assert create_spec.kind == "headless"
        assert create_spec.cores == 4
        assert create_spec.ram == 8

        # Fetch running headless sessions
        fetch_spec = FetchRequest(type="headless", status="Running")  # Using alias

        assert fetch_spec.kind == "headless"
        assert fetch_spec.status == "Running"


class TestFetchResponse:
    """Test FetchResponse class."""

    def test_required_fields_with_sample_data(self) -> None:
        """Test FetchResponse with sample data from API."""
        response = FetchResponse(
            id="fnl2zlu3",
            userid="brars",
            runAsUID="166169204",
            runAsGID="166169204",
            supplementalGroups=[
                34241,
                34337,
                35124,
                36227,
                1902365706,
                1454823273,
                1025424273,
            ],
            appid="<none>",
            image="images.canfar.net/skaha/astroml-notebook:latest",
            type="notebook",
            status="Running",
            name="notebook1",
            startTime="2025-07-09T06:18:03Z",
            expiryTime="2025-07-13T06:18:03Z",
            connectURL="https://workload-uv.canfar.net/session/notebook/fnl2zlu3/lab/tree/arc/home/brars?token=fnl2zlu3",
            requestedRAM="1G",
            requestedCPUCores="1",
            requestedGPUCores="0",
            ramInUse="<none>",
            gpuRAMInUse="<none>",
            cpuCoresInUse="<none>",
            gpuUtilization="<none>",
        )

        # Test basic fields
        assert response.id == "fnl2zlu3"
        assert response.userid == "brars"
        assert response.run_as_uid == "166169204"
        assert response.run_as_gid == "166169204"
        assert response.supplemental_groups == [
            34241,
            34337,
            35124,
            36227,
            1902365706,
            1454823273,
            1025424273,
        ]
        assert response.appid == "<none>"
        assert response.image == "images.canfar.net/skaha/astroml-notebook:latest"
        assert response.type == "notebook"
        assert response.status == "Running"
        assert response.name == "notebook1"

        # Test time fields
        assert response.start_time == "2025-07-09T06:18:03Z"
        assert response.expiry_time == "2025-07-13T06:18:03Z"

        # Test URL field
        assert (
            response.connect_url
            == "https://workload-uv.canfar.net/session/notebook/fnl2zlu3/lab/tree/arc/home/brars?token=fnl2zlu3"
        )

        # Test resource fields
        assert response.requested_ram == "1G"
        assert response.requested_cpu_cores == "1"
        assert response.requested_gpu_cores == "0"
        assert response.ram_in_use == "<none>"
        assert response.gpu_ram_in_use == "<none>"
        assert response.cpu_cores_in_use == "<none>"
        assert response.gpu_utilization == "<none>"

    def test_field_aliases(self) -> None:
        """Test that field aliases work correctly for API compatibility."""
        # Test data using API field names (aliases)
        api_data: dict[str, Any] = {
            "id": "test123",
            "userid": "testuser",
            "runAsUID": "1001",
            "runAsGID": "1001",
            "supplementalGroups": [100, 200],
            "appid": "test-app",
            "image": "test:latest",
            "type": "headless",
            "status": "Pending",
            "name": "test-session",
            "startTime": "2025-01-01T00:00:00Z",
            "expiryTime": "2025-01-02T00:00:00Z",
            "connectURL": "https://example.com/connect",
            "requestedRAM": "2G",
            "requestedCPUCores": "2",
            "requestedGPUCores": "1",
            "ramInUse": "1.5G",
            "gpuRAMInUse": "0.5G",
            "cpuCoresInUse": "1.8",
            "gpuUtilization": "75%",
        }

        response = FetchResponse.model_validate(api_data)

        # Verify that aliases map to Python field names correctly
        assert response.run_as_uid == "1001"
        assert response.run_as_gid == "1001"
        assert response.supplemental_groups == [100, 200]
        assert response.start_time == "2025-01-01T00:00:00Z"
        assert response.expiry_time == "2025-01-02T00:00:00Z"
        assert response.connect_url == "https://example.com/connect"
        assert response.requested_ram == "2G"
        assert response.requested_cpu_cores == "2"
        assert response.requested_gpu_cores == "1"
        assert response.ram_in_use == "1.5G"
        assert response.gpu_ram_in_use == "0.5G"
        assert response.cpu_cores_in_use == "1.8"
        assert response.gpu_utilization == "75%"

    def test_serialization_with_aliases(self) -> None:
        """Test that serialization uses aliases for API compatibility."""
        response = FetchResponse(
            id="test123",
            userid="testuser",
            runAsUID="1001",
            runAsGID="1001",
            supplementalGroups=[100, 200],
            appid="test-app",
            image="test:latest",
            type="headless",
            status="Running",
            name="test-session",
            startTime="2025-01-01T00:00:00Z",
            expiryTime="2025-01-02T00:00:00Z",
            connectURL="https://example.com/connect",
            requestedRAM="2G",
            requestedCPUCores="2",
            requestedGPUCores="1",
            ramInUse="1.5G",
            gpuRAMInUse="0.5G",
            cpuCoresInUse="1.8",
            gpuUtilization="75%",
        )

        # Serialize with aliases (for API compatibility)
        data = response.model_dump(by_alias=True)

        # Check that API field names are used
        assert "runAsUID" in data
        assert "runAsGID" in data
        assert "supplementalGroups" in data
        assert "startTime" in data
        assert "expiryTime" in data
        assert "connectURL" in data
        assert "requestedRAM" in data
        assert "requestedCPUCores" in data
        assert "requestedGPUCores" in data
        assert "ramInUse" in data
        assert "gpuRAMInUse" in data
        assert "cpuCoresInUse" in data
        assert "gpuUtilization" in data

        # Check that Python field names are not used
        assert "run_as_uid" not in data
        assert "run_as_gid" not in data
        assert "supplemental_groups" not in data
        assert "start_time" not in data
        assert "expiry_time" not in data
        assert "connect_url" not in data

    def test_type_validation(self) -> None:
        """Test that type field validates against Kind enum."""
        valid_types: list[Kind] = [
            "desktop",
            "notebook",
            "carta",
            "headless",
            "firefly",
        ]

        for session_type in valid_types:
            response = FetchResponse(
                id="test",
                userid="user",
                runAsUID="1001",
                runAsGID="1001",
                supplementalGroups=[],
                appid="<none>",
                image="test:latest",
                type=session_type,
                status="Running",
                name="test",
                startTime="2025-01-01T00:00:00Z",
                expiryTime="2025-01-02T00:00:00Z",
                connectURL="https://example.com",
                requestedRAM="1G",
                requestedCPUCores="1",
                requestedGPUCores="0",
                ramInUse="<none>",
                gpuRAMInUse="<none>",
                cpuCoresInUse="<none>",
                gpuUtilization="<none>",
            )
            assert response.type == session_type

    def test_status_validation(self) -> None:
        """Test that status field validates against Status enum."""
        valid_statuses: list[Status] = [
            "Pending",
            "Running",
            "Terminating",
            "Succeeded",
            "Error",
        ]

        for status in valid_statuses:
            response = FetchResponse(
                id="test",
                userid="user",
                runAsUID="1001",
                runAsGID="1001",
                supplementalGroups=[],
                appid="<none>",
                image="test:latest",
                type="notebook",
                status=status,
                name="test",
                startTime="2025-01-01T00:00:00Z",
                expiryTime="2025-01-02T00:00:00Z",
                connectURL="https://example.com",
                requestedRAM="1G",
                requestedCPUCores="1",
                requestedGPUCores="0",
                ramInUse="<none>",
                gpuRAMInUse="<none>",
                cpuCoresInUse="<none>",
                gpuUtilization="<none>",
            )
            assert response.status == status

    def test_supplemental_groups_list(self) -> None:
        """Test that supplementalGroups handles various list configurations."""
        # Empty list
        response = FetchResponse(
            id="test",
            userid="user",
            runAsUID="1001",
            runAsGID="1001",
            supplementalGroups=[],
            appid="<none>",
            image="test:latest",
            type="notebook",
            status="Running",
            name="test",
            startTime="2025-01-01T00:00:00Z",
            expiryTime="2025-01-02T00:00:00Z",
            connectURL="https://example.com",
            requestedRAM="1G",
            requestedCPUCores="1",
            requestedGPUCores="0",
            ramInUse="<none>",
            gpuRAMInUse="<none>",
            cpuCoresInUse="<none>",
            gpuUtilization="<none>",
        )
        assert response.supplemental_groups == []

        # Single group
        response = FetchResponse(
            id="test",
            userid="user",
            runAsUID="1001",
            runAsGID="1001",
            supplementalGroups=[1000],
            appid="<none>",
            image="test:latest",
            type="notebook",
            status="Running",
            name="test",
            startTime="2025-01-01T00:00:00Z",
            expiryTime="2025-01-02T00:00:00Z",
            connectURL="https://example.com",
            requestedRAM="1G",
            requestedCPUCores="1",
            requestedGPUCores="0",
            ramInUse="<none>",
            gpuRAMInUse="<none>",
            cpuCoresInUse="<none>",
            gpuUtilization="<none>",
        )
        assert response.supplemental_groups == [1000]

        # Multiple groups (like in the example)
        groups = [34241, 34337, 35124, 36227, 1902365706, 1454823273, 1025424273]
        response = FetchResponse(
            id="test",
            userid="user",
            runAsUID="1001",
            runAsGID="1001",
            supplementalGroups=groups,
            appid="<none>",
            image="test:latest",
            type="notebook",
            status="Running",
            name="test",
            startTime="2025-01-01T00:00:00Z",
            expiryTime="2025-01-02T00:00:00Z",
            connectURL="https://example.com",
            requestedRAM="1G",
            requestedCPUCores="1",
            requestedGPUCores="0",
            ramInUse="<none>",
            gpuRAMInUse="<none>",
            cpuCoresInUse="<none>",
            gpuUtilization="<none>",
        )
        assert response.supplemental_groups == groups

    def test_model_config(self) -> None:
        """Test model configuration settings."""
        response = FetchResponse(
            id="test",
            userid="user",
            runAsUID="1001",
            runAsGID="1001",
            supplementalGroups=[],
            appid="<none>",
            image="test:latest",
            type="notebook",
            status="Running",
            name="test",
            startTime="2025-01-01T00:00:00Z",
            expiryTime="2025-01-02T00:00:00Z",
            connectURL="https://example.com",
            requestedRAM="1G",
            requestedCPUCores="1",
            requestedGPUCores="0",
            ramInUse="<none>",
            gpuRAMInUse="<none>",
            cpuCoresInUse="<none>",
            gpuUtilization="<none>",
        )

        # Test that validate_assignment is enabled
        response.name = "updated-name"
        assert response.name == "updated-name"

        # Test that populate_by_name is enabled
        assert "populate_by_name" in response.model_config
        assert response.model_config["populate_by_name"] is True

    def test_realistic_api_response(self) -> None:
        """Test with realistic API response data."""
        # This simulates what would come from the actual Skaha API
        api_response_data: dict[str, Any] = {
            "id": "abc123def",
            "userid": "scientist",
            "runAsUID": "500123",
            "runAsGID": "500123",
            "supplementalGroups": [1000, 1001, 1002],
            "appid": "jupyter-lab",
            "image": "images.canfar.net/skaha/scipy-notebook:latest",
            "type": "notebook",
            "status": "Running",
            "name": "data-analysis-session",
            "startTime": "2025-07-09T14:30:15Z",
            "expiryTime": "2025-07-13T14:30:15Z",
            "connectURL": "https://ws-uv.canfar.net/session/notebook/abc123def/lab?token=abc123def",
            "requestedRAM": "8G",
            "requestedCPUCores": "4",
            "requestedGPUCores": "1",
            "ramInUse": "6.2G",
            "gpuRAMInUse": "2.1G",
            "cpuCoresInUse": "3.8",
            "gpuUtilization": "85%",
        }

        response = FetchResponse.model_validate(api_response_data)

        # Verify all fields are correctly parsed
        assert response.id == "abc123def"
        assert response.userid == "scientist"
        assert response.run_as_uid == "500123"
        assert response.run_as_gid == "500123"
        assert response.supplemental_groups == [1000, 1001, 1002]
        assert response.appid == "jupyter-lab"
        assert response.image == "images.canfar.net/skaha/scipy-notebook:latest"
        assert response.type == "notebook"
        assert response.status == "Running"
        assert response.name == "data-analysis-session"
        assert response.start_time == "2025-07-09T14:30:15Z"
        assert response.expiry_time == "2025-07-13T14:30:15Z"
        assert (
            response.connect_url
            == "https://ws-uv.canfar.net/session/notebook/abc123def/lab?token=abc123def"
        )
        assert response.requested_ram == "8G"
        assert response.requested_cpu_cores == "4"
        assert response.requested_gpu_cores == "1"
        assert response.ram_in_use == "6.2G"
        assert response.gpu_ram_in_use == "2.1G"
        assert response.cpu_cores_in_use == "3.8"
        assert response.gpu_utilization == "85%"
