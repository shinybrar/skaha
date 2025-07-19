# Authentication Contexts

`skaha` is designed to connect to multiple Science Platform servers around the world. To manage these connections seamlessly, it uses a system called **Authentication Contexts**.

## What is an Auth Context?

- Think of an authentication context (*context* for short) as a saved profile. Each context is a self-contained configuration that links your credentials, e.g. an OIDC token or an X.509 PEM certificate to a specific server like the Canadian Astronomy Data Centre.

- When you use `skaha`, one context is always set as **active**. All commands and API calls will be directed to the server specified in that active context.

- This system makes it easy to switch between different servers without having to re-enter your credentials every time.

---

## Logging In (`skaha auth login`)

When you want to connect to a new server, you use the `login` command. This command is the primary way to create and activate a new authentication context.

```bash
skaha auth login
```

Running this command will:

1.  **Discover Servers:** It will first search for available Science Platform servers.
2.  **Guide You:** It will prompt you to select a server.
3.  **Authenticate:** It will guide you through the authentication process required by that specific server (either OIDC or X.509 certificate).
4.  **Save the Context:** Upon successful authentication, it will save a new context to your configuration file, located at `~/.config/skaha/config.yaml`.

This new context will automatically be set as the active one.

---

## Managing Your Contexts

Once you have logged into one or more servers, you can easily manage your saved contexts directly from the command line.

### Listing Contexts (`skaha auth list`)

To see a clean, readable summary of all your saved contexts, use the `list` command.

```bash
skaha auth list
```

This will display a table of your contexts, clearly indicating which one is active.

**Example Output:**

```
                Available Authentication Contexts                
         ╷         ╷           ╷                                 
  Active │ Name    │ Auth Mode │ Server URL                      
╶────────┼─────────┼───────────┼────────────────────────────────╴
    ✅   │ default │   x509    │ https://ws-uv.canfar.net/skaha 
```

### Switching the Active Context (`skaha auth switch`)

Instead of manually editing the configuration file, the safest way to switch between contexts is with the `switch` command.

```bash
skaha auth switch <CONTEXT>
```

For example, to switch to the Swedish server from the example above:

```bash
skaha auth switch SRCNet-Sweden
```

All subsequent `skaha` commands and API calls will now be sent to the `SRCNet-Sweden` server.

### Removing a Context (`skaha auth rm`)

You can remove a specific context that you no longer need with the `rm` command.

```bash
skaha auth rm <CONTEXT>
```

!!! warning "Safety Feature"
    You cannot remove a context that is currently active. To remove it, you must first switch to a different context.

---

## Purging All Credentials (`skaha auth purge`)

To securely remove **all** your saved credentials and contexts from your machine, use the `purge` command.

```bash
skaha auth purge
```

This command will:

1.  **Ask for Confirmation:** It will prompt you to confirm that you want to remove all credentials.
2.  **Delete the Configuration:** Upon confirmation, it will completely and securely delete the `~/.config/skaha/config.yaml` file from your system.

You can use the `--yes` flag to skip the confirmation prompt:

```bash
skaha auth purge --yes
```
