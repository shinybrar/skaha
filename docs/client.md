# Skaha Client

The `skaha.client` module provides a client for the Skaha server. The client is based of the
`httpx` library and provides a simple interface to the Skaha server. The client configures the
authorization headers for user authentication and container registry access.

::: skaha.client.SkahaClient
    handler: python
    selection:
      members:
        - __init__
        - _check_server
        - _check_certificate
        - __attrs_post_init__
    rendering:
      show_root_heading: true
      show_source: true
      heading_level: 2
