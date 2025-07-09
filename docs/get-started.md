# Get Started

## Before you Begin

Before you can use the Skaha Python package, you need a valid account with access to the CANFAR Science Platform. To request access, [please request an account with the Canadian Astronomy Data Centre (CADC)](https://www.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/en/auth/request.html).

## Quick Start

!!! note "Skaha Requirements"

    - Python 3.9+
    - Science Platform Account

!!! code "Installation"

    ```bash
    pip3 install skaha
    ```

## Authentication

Skaha supports multiple authentication methods to interact with the CANFAR Science Platform. The authentication system automatically handles SSL contexts, headers, and credential management.

### Authentication Modes

!!! tip "Automatic Configuration"
    Starting with v1.7, Skaha features an enhanced authentication system that automatically configures the appropriate authentication method based on your configuration.

#### X.509 Certificate Authentication

The most common authentication method uses X.509 security certificates. Certificates come in the form of `.pem` files.

!!! info "Default Certificate Location"
    By default, Skaha looks for certificates at `$HOME/.ssl/cadcproxy.pem`.

**Generate a Certificate:**

```bash
cadc-get-cert -u username
Password: *******

DONE. 10 day certificate saved in /home/username/.ssl/cadcproxy.pem
```

**Using Default Certificate:**

```python
from skaha.session import Session

# Uses default certificate location
session = Session()
```

**Using Custom Certificate:**

```python
from pathlib import Path
from skaha.session import Session

session = Session(certificate=Path("/path/to/certificate.pem"))
```

#### OIDC Token Authentication

For OIDC (OpenID Connect) authentication, configure your authentication settings:

```python
from skaha.session import Session

# Uses configured OIDC authentication
# (requires auth.mode = "oidc" in configuration)
session = Session()
```

#### Bearer Token Authentication

You can use bearer tokens for direct authentication:

```python
from pydantic import SecretStr
from skaha.session import Session

session = Session(token=SecretStr("your-bearer-token"))
```

!!! warning "Token Security"
    Always use `SecretStr` for tokens to prevent accidental logging of sensitive credentials.

### Authentication Priority

The authentication system follows this priority order:

1. **User-provided token** (highest priority)
2. **User-provided certificate**
3. **Configured authentication mode** (oidc, x509, default)
4. **Default certificate** (fallback)

### Checking Authentication Status

You can check the authentication expiry and mode:

```python
import time
from skaha.client import SkahaClient

client = SkahaClient()

# Check authentication mode
print(f"Authentication mode: {client.auth.mode}")

# Check expiry (if available)
if client.expiry:
    time_left = client.expiry - time.time()
    print(f"Authentication expires in {time_left:.0f} seconds")
else:
    print("No expiry tracking available")
```

## Container Registry Access

In order to access private container images from the CANFAR Harbor Registry, you need to provide a `username` and the `CLI Secret` through a `ContainerRegistry` object.

```python
from skaha.models import ContainerRegistry
from skaha.session import Session

registry = ContainerRegistry(username="username", password="sUp3rS3cr3t")
session = Session(registry=registry)
```

Passing the `ContainerRegistry` object passes the base64 encoded `username:secret` to the Skaha server for authentication under the `X-Skaha-Registry-Auth` header.
