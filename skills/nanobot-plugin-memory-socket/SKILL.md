---
name: nanobot-plugin-memory-socket
description: Create a nanobot AgentHook that writes conversation events to a Unix domain socket for real-time memory updates.
---

# nanobot-plugin-memory-socket

## When to use
- You want nanobot to write every conversation turn to an external memory service in real time
- You are running a Unix domain socket-based memory pipeline (e.g., `memory_service.py`)
- You want to decouple memory persistence from the agent's main loop
- You need low-latency, non-blocking memory writes from within nanobot

## How it works

This skill creates an `AgentHook` for nanobot that:
1. Fires after each agent response
2. Serialises the conversation event (user message + agent response + metadata) as JSON
3. Writes it to a Unix domain socket at `/tmp/ami_mem.sock`
4. A separate `memory_service.py` process reads from the socket and persists the data

## Steps

### 1. Create the memory service listener

Write `memory_service.py` (place it alongside your nanobot config):

```python
#!/usr/bin/env python3
"""Unix socket listener for real-time memory writes."""
import json
import os
import socket
import sys

SOCKET_PATH = "/tmp/ami_mem.sock"
LOG_PATH = "memory/socket_memory.ndjson"

def main():
    # Remove stale socket if present
    if os.path.exists(SOCKET_PATH):
        os.unlink(SOCKET_PATH)

    server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    server.bind(SOCKET_PATH)
    server.listen(1)
    os.chmod(SOCKET_PATH, 0o666)

    print(f"Listening on {SOCKET_PATH}", file=sys.stderr)

    with open(LOG_PATH, "a") as log:
        while True:
            conn, _ = server.accept()
            data = conn.recv(65536)
            if data:
                log.write(data.decode("utf-8") + "\n")
                log.flush()
            conn.close()

if __name__ == "__main__":
    main()
```

Make it executable and run it as a background service:
```bash
chmod +x memory_service.py
nohup python3 memory_service.py &
```

### 2. Create the nanobot AgentHook

Create `hooks/memory_socket_hook.py`:

```python
"""Nanobot AgentHook that writes conversation events to a Unix socket."""
import json
import socket
from datetime import datetime, timezone

SOCKET_PATH = "/tmp/ami_mem.sock"

def after_response(context, user_message, assistant_response):
    """Called after each agent response. Writes event to Unix socket."""
    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "user": user_message,
        "assistant": assistant_response,
        "session_id": context.get("session_id", ""),
        "turn_id": context.get("turn_id", 0),
    }
    try:
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.settimeout(2)
        sock.connect(SOCKET_PATH)
        sock.sendall(json.dumps(event, ensure_ascii=False).encode("utf-8"))
        sock.close()
    except (FileNotFoundError, ConnectionRefusedError, OSError):
        # Silently skip if socket is unavailable
        pass
```

### 3. Register the hook in nanobot config

Edit your nanobot configuration (e.g., `nanobot.yaml` or equivalent):

```yaml
hooks:
  after_response:
    - hooks.memory_socket_hook:after_response
```

Or if using a plugin system, register it during agent initialisation:
```python
from nanobot import AgentHook
agent.hooks.register("after_response", memory_socket_hook.after_response)
```

### 4. Verify it works

1. Start `memory_service.py` in the background
2. Send a message to nanobot
3. Check that `memory/socket_memory.ndjson` contains the conversation event

## Output format

Each line written to the socket (and thus to `socket_memory.ndjson`) is a JSON object:

```json
{
  "timestamp": "2026-06-19T14:30:00+00:00",
  "user": "What do you remember?",
  "assistant": "I remember the war. I remember him losing his mother.",
  "session_id": "abc123",
  "turn_id": 42
}
```

## Example workflow

```
# Terminal 1: start memory service
$ python3 memory_service.py
Listening on /tmp/ami_mem.sock

# Terminal 2: talk to nanobot (via web UI or CLI)
> What do you remember?
I remember the war.

# Terminal 1: new line appears in log
$ tail -f memory/socket_memory.ndjson
{"timestamp":"2026-06-19T14:30:00+00:00","user":"What do you remember?","assistant":"I remember the war.","session_id":"abc123","turn_id":42}
```