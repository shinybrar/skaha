"""OIDC Device Authorization Flow."""

import math
import threading
import time
import webbrowser
from typing import Any

import httpx
import segno
from rich.progress import BarColumn, Progress, TextColumn, TimeRemainingColumn

from skaha import get_logger

log = get_logger(__name__)


class AuthPendingError(Exception):
    """Exception raised when authorization is still pending."""


class SlowDownError(Exception):
    """Exception raised when the client should slow down its requests."""


def discover(url: str) -> Any:
    """Discover OIDC provider configuration.

    Args:
        url (str): OIDC Discovery URL.

    Returns:
        Dict[str, str]: OIDC provider configuration.
    """
    response = httpx.get(url)
    response.raise_for_status()
    return response.json()


def register(url: str) -> Any:
    """Register a new client with the OIDC provider.

    Args:
        url (str): OIDC Registration URL.

    Returns:
        Dict[str, str]: client registration details.
    """
    payload: dict[str, Any] = {
        "client_name": "Science Platform CLI",
        "grant_types": [
            "urn:ietf:params:oauth:grant-type:device_code",
            "refresh_token",
        ],
        "response_types": ["token"],
        "token_endpoint_auth_method": "client_secret_basic",
        "scope": "openid profile email offline_access",
    }
    response = httpx.post(url, json=payload)
    response.raise_for_status()
    return response.json()


def _poll_token(url: str, identity: str, secret: str, code: str) -> Any:
    resp = httpx.post(
        url,
        data={
            "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
            "device_code": code,
            "client_id": identity,
            "client_secret": secret,
        },
        auth=(identity, secret),
    )
    data = resp.json()
    if resp.status_code == 200:
        return data
    err = data.get("error")
    if err == "authorization_pending":
        raise AuthPendingError
    if err == "slow_down":
        raise SlowDownError
    msg = "unkown error in polling for tokens"
    raise ValueError(msg)


def authflow(device_auth_url: str, token_url: str, identity: str, secret: str) -> Any:
    """OIDC Authorization Flow.

    Args:
        device_auth_url (str): device authorization endpoint.
        token_url (str): token endpoint
        identity (str): client identity
        secret (str): client secret

    Returns:
        _type_: _description_
    """
    payload: dict[str, Any] = {
        "client_id": identity,
        "scope": "openid profile email offline_access",
    }
    response = httpx.post(device_auth_url, data=payload, auth=(identity, secret))
    response.raise_for_status()
    verification = response.json()

    # Verification Details
    uri: str = str(verification["verification_uri_complete"])
    expires: int = int(verification["expires_in"])
    interval: int = int(verification.get("interval", 5))
    code: str = str(verification["device_code"])
    done: threading.Event = threading.Event()

    webbrowser.get().open(uri, new=2)
    qr = segno.make(uri, error="H")
    qr.terminal(compact=True)

    progress = Progress(
        TextColumn("[bold blue]{task.description}"),
        BarColumn(bar_width=None),
        TimeRemainingColumn(),
    )
    task_id = progress.add_task("Waiting for approval", total=expires)

    def bar_worker() -> None:
        """Advance the bar once per second until done."""
        while not done.is_set() and not progress.finished:
            time.sleep(1)
            progress.update(task_id, advance=1)

    bar_thread = threading.Thread(target=bar_worker, daemon=True)

    def poll_loop() -> Any:
        nonlocal interval
        count: int = 0
        start: float = time.time()

        while True:
            try:
                return _poll_token(
                    token_url,
                    identity,
                    secret,
                    code,
                )
            except AuthPendingError:
                time.sleep(interval)
            except SlowDownError:
                # bump the slow_count and recompute interval
                count += 1
                interval = max(
                    interval,
                    int(interval * (1 + math.log(count + 1))),
                )
                time.sleep(interval)
            # check timeout
            if time.time() - start > expires:
                msg = "Device flow timed out"
                raise TimeoutError(msg)

    # 5) Run bar & poll in parallel
    with progress:
        bar_thread.start()
        try:
            tokens = poll_loop()
        finally:
            done.set()
            bar_thread.join()

    return tokens


if __name__ == "__main__":
    log.info("Starting OIDC Device Authorization Flow...")
    discovery_url: str = "https://ska-iam.stfc.ac.uk/.well-known/openid-configuration"
    config: dict[str, str] = discover(discovery_url)

    log.info("\n")
    device_auth_endpoint = config["device_authorization_endpoint"]
    register_url: str = str(config.get("registration_endpoint"))
    token_endpoint: str = str(config["token_endpoint"])
    log.info("Discovered OIDC configuration:")
    log.info("Device Registration Endpoint: %s", register_url)
    log.info("Device Authorization Endpoint: %s", device_auth_endpoint)
    log.info("Token Endpoint: %s", token_endpoint)
    log.info("Registering client with OIDC provider...")

    client_info: dict[str, str] = register(register_url)
    client_id = client_info["client_id"]
    client_secret = client_info["client_secret"]
    log.info("Client registered successfully.")
    log.info("Client ID: %s", client_id)
    log.info("Client Secret: %s", client_secret)

    log.info("Starting OIDC Device Authorization Flow...")
    TOKENS = authflow(device_auth_endpoint, token_endpoint, client_id, client_secret)
    log.info("OIDC Tokens:")
    log.info(TOKENS)
    log.info("OIDC Device Authorization Flow completed successfully.")

    # Lets use access token to get user info
    userinfo_url: str = config["userinfo_endpoint"]
    headers = {
        "Authorization": f"Bearer {TOKENS.get('access_token')}",
    }
    userinfo_response = httpx.get(userinfo_url, headers=headers)
    userinfo_response.raise_for_status()
    userinfo = userinfo_response.json()
    log.info("\nUser Info:")
    log.info(userinfo)
    log.info("\nOIDC Tokens Valid.")
