# Testing

This document provides comprehensive information about testing in the Skaha project.

## Overview

Skaha uses [pytest](https://pytest.org/) as its testing framework. The test suite includes unit tests, integration tests, and end-to-end tests that verify the functionality of the Skaha client library.

## Prerequisites

To run tests for Skaha, you need:

1. **Valid CANFAR Account**: Access to the CANFAR Science Platform
2. **X.509 Certificate**: For authentication with CANFAR services
3. **Python Environment**: Set up with uv

For certificate generation, refer to the [get started](get-started.md) section.

## Running Tests

### Basic Test Execution

Run all tests:
```bash
uv run pytest
```

Run tests with verbose output:
```bash
uv run pytest -v
```

Run tests with coverage report:
```bash
uv run pytest --cov
```

### Test Categories

Skaha tests are organized with markers to help you run specific subsets:

#### Slow Tests

Some tests are marked as "slow" because they involve:
- Network operations with CANFAR services
- Waiting for session state changes
- Authentication timeouts
- Long-running operations

**Skip slow tests for faster development:**
```bash
uv run pytest -m "not slow"
```

**Run only slow tests:**
```bash
uv run pytest -m "slow"
```

#### Integration Tests

Tests that interact with external services:
```bash
uv run pytest -m "integration"
```

#### Unit Tests

Fast, isolated tests:
```bash
uv run pytest -m "unit"
```

### Test Organization

Tests are organized in the `tests/` directory:

```
tests/
├── test_auth_oidc.py          # OIDC authentication tests
├── test_auth_x509.py          # X.509 certificate tests
├── test_async_session.py      # Async session management tests (contains slow tests)
├── test_client.py             # HTTP client tests
├── test_config_*.py           # Configuration tests
├── test_images.py             # Container image tests
├── test_overview.py           # Platform overview tests
├── test_session.py            # Session management tests (contains slow tests)
└── test_utils_*.py            # Utility function tests
```

## Slow Tests Details

The following tests are marked as slow and may take several minutes to complete:

### Session Tests (`test_session.py`)
- `test_session_stats`: Retrieves platform statistics (~12.7s)
- `test_session_logs`: Waits for session completion and retrieves logs (~62.9s)

### Async Session Tests (`test_async_session.py`)
- `test_get_succeeded`: Waits for session to reach succeeded state (~63.4s)
- `test_get_session_stats`: Retrieves platform statistics (~7.0s)

### Authentication Tests (`test_auth_oidc.py`)
- `test_poll_with_backoff_timeout`: Tests authentication timeout behavior (~15.0s)

## Development Workflow

For efficient development, follow this testing workflow:

1. **During Development**: Run fast tests only
   ```bash
   uv run pytest -m "not slow"
   ```

2. **Before Committing**: Run the full test suite
   ```bash
   uv run pytest
   ```

3. **Debugging Specific Issues**: Run individual test files
   ```bash
   uv run pytest tests/test_session.py
   ```

## Test Configuration

Test configuration is defined in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
markers = [
    "integration: marks tests as integration tests",
    "unit: marks tests as unit tests", 
    "slow: marks tests as slow (deselect with '-m \"not slow\"')",
    "order: marks tests that need to run in a specific order",
]
```

## Continuous Integration

In CI environments, all tests (including slow ones) are executed to ensure complete validation. The CI pipeline:

1. Sets up authentication with CANFAR
2. Runs the complete test suite
3. Generates coverage reports
4. Cleans up authentication artifacts

## Writing Tests

When contributing new tests:

1. **Mark slow tests**: Add `@pytest.mark.slow` to tests that take >5 seconds
2. **Use appropriate markers**: Mark tests as `unit`, `integration`, etc.
3. **Follow naming conventions**: Test files should start with `test_`
4. **Add docstrings**: Document what each test verifies

Example of a slow test:
```python
import pytest

@pytest.mark.slow
def test_long_running_operation():
    """Test that involves waiting or network operations."""
    # Test implementation
    pass
```

## Troubleshooting

### Authentication Issues
- Ensure your X.509 certificate is valid and not expired
- Check that you have access to the CANFAR Science Platform
- Verify your certificate is in the correct location (`~/.ssl/`)

### Slow Test Timeouts
- Slow tests have built-in timeouts (typically 60 seconds)
- If tests consistently timeout, check your network connection
- Platform availability may affect test execution times

### Test Failures
- Check if the CANFAR Science Platform is accessible
- Verify your authentication credentials
- Review test logs for specific error messages
