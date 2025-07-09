# Skaha

!!! note ""

    A lightweight python interface to the CANFAR Science Platform.

!!! example "Example"

    ```python
    from skaha.session import Session

    session = Session()
    session_id = session.create(
        name="test",
        image="images.canfar.net/skaha/base-notebook:latest",
        cores=2,
        ram=8,
        gpu=1,
        kind="headless",
        cmd="env",
        env={"KEY": "VALUE"},
        replicas=3,
    )
    ```

## What's New

!!! info "New in v1.6+"

    ### **🚀 Asynchronous Sessions**
    Skaha now supports asynchronous sessions using the `AsyncSession` class while maintaining 1-to-1 compatibility with the `Session` class.

    ```python
    from skaha.session import AsyncSession

    asession = AsyncSession()
    response = await asession.create(
        name="test",
        image="images.canfar.net/skaha/base-notebook:latest",
        cores=2,
        ram=8,
        gpu=1,
        kind="headless",
        cmd="env",
        env={"KEY": "VALUE"},
        replicas=3,
    )
    ```

    ### **🗄️ Backend Upgrades**

    - 📡 Skaha now uses the `httpx` library for making HTTP requests instead of `requests`. This adds asynchronous support and also to circumvent the `requests` dependence on `urllib3` which was causing SSL issues on MacOS. See [this issue](https://github.com/urllib3/urllib3/issues/3020) for more details.
    - 🔑 Skaha now supports tokens for authentication. As a result, the constraints for providing a valid certificate filepath have been relaxed and are only enforced when the certificate is used for authentication.
    - 🏎️💨 Added `loglevel` and `concurrency` support to manage the new explosion in functionality!s

    ### **🧾 Logs to `stdout`**

    The `[Session|AsyncSession].logs` method now prints colored output to `stdout` instead of returning them as a string with `verbose=True` flag.

    ```python
    from skaha.session import AsyncSession

    asession = AsyncSession()
    await asession.logs(ids=["some-uuid"], verbose=True)
    ```

    ### **🪰 Firefly Support**
    Skaha now supports launching `firefly` session on the CANFAR Science Platform.

    ```python
    session.create(
        name="firefly",
        image="images.canfar.net/skaha/firefly:latest",
    )
    ```

!!! Info "New in v1.4+"

    ### **🔐 Private Images**

    Starting October 2024, to create a session with a private container image from the [CANFAR Harbor Registry](https://images.canfar.net/), you will need to provide your harbor `username` and the `CLI Secret` through a `ContainerRegistry` object.

    ```python
    from skaha.models import ContainerRegistry
    from skaha.session import Session

    registry = ContainerRegistry(username="username", secret="sUp3rS3cr3t")
    session = Session(registry=registry)
    ```

    Alernatively, if you have environment variables, `SKAHA_REGISTRY_USERNAME` and `SKAHA_REGISTRY_SECRET`, you can create a `ContainerRegistry` object without providing the `username` and `secret`.

    ```python
    from skaha.models import ContainerRegistry

    registry = ContainerRegistry()
    ```

    ### **💣 Destroy Sessions**
    ```python
    from skaha.session import Session

    session = Session()
    session.destroy_with(prefix="test", kind="headless", status="Running")
    session.destroy_with(prefix="test", kind="headless", status="Pending")
    ```

[Get Started :material-coffee:](get-started.md){: .md-button .md-button--primary }
[Go to GitHub :fontawesome-brands-github:](https://github.com/shinybrar/skaha){: .md-button .md-button--primary }
[Changelog :material-vector-polyline-remove:](changelog.md){: .md-button .md-button--primary }
