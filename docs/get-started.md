# Get Started

## Before you Begin

Before you can use the Skaha python package, you need a valid CANFAR account and access to the CANFAR Science Platform. To request access, [please request an account with the Canadian Astronomy Data Centre (CADC)](https://www.cadc-ccda.hia-iha.nrc-cnrc.gc.ca/en/auth/request.html).

## Quick Start

!!! note "Skaha Requirements"

    - Python 3.9+
    - CANFAR Science Platform Account

!!! code "Installation"

    ```bash
    pip3 install skaha
    ```

## Authentication

### X509 Authentication

Skaha can use X509 security certificate for interactions with the CANFAR Science Platform. The certificate comes in the form of a `.pem` file which is saved in your home directory by default under the path `~/.ssl/cadcproxy.pem`.

!!! info "X509 Certificate"
    You need to have a valid certificate in order to use the CANFAR Science Platform.

!!! question "Generate a certificate"
    As part of the skaha package installation, a command line tool named `cadc-get-cert` is also installed. This tool simplifies the process of generating a certificate by executing the following command:

    ```bash
    cadc-get-cert -u username
    Password: *******

    DONE. 10 day certificate saved in /home/username/.ssl/cadcproxy.pem
    ```

By default, `skaha` **only** looks at the location `$HOME/.ssl/cadcproxy.pem` for the X509 authentication certificate. When using the `skaha` python package, you can specify the location of your certificate when creating a new session.

```python
from skaha.session import Session

session = Session(certificate="/path/to/certificate.pem")
```

### Token Authentication

Starting with v1.6, Skaha supports token authentication. You can use a token instead of a certificate for authentication. The token can be passed as a string or as a file path.

```python
from skaha.session import Session

session = Session(token="your_token")
```

!!! note "Beta Feature"
    Token authentication is a beta feature intended for testing purposes. It is not recommended for production use. As CADC migrates to token-based authentication, this feature will be updated to support with better documentation and examples for end-users.

## Container Registry Access

In order to access private container images from the CANFAR Harbor Registry, you need to provide a `username` and the `CLI Secret` through a `ContainerRegistry` object.

```python
from skaha.models import ContainerRegistry
from skaha.session import Session

registry = ContainerRegistry(username="username", password="sUp3rS3cr3t")
session = Session(registry=registry)
```

Passing the `ContainerRegistry` object passes the base64 encoded `username:secret` to the Skaha server for authentication under the `X-Skaha-Registry-Auth` header.