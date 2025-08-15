"""
Event bus facade that exposes a default in‑memory implementation
but allows future swapping (e.g., Redis Pub/Sub) without changing imports.
Public API kept: `event_bus` and `sse_stream`.
"""
from __future__ import annotations

from queue import Queue
from typing import Generator

from src.api.services.inmemory_impl import InMemoryEventBus

# Default event bus implementation (in‑memory; single process)
event_bus = InMemoryEventBus()

# Expose a function compatible with existing imports
from typing import cast

def sse_stream(queue: Queue, heartbeat_interval: float = 15.0) -> Generator[str, None, None]:
    return cast(Generator[str, None, None], event_bus.sse_stream(queue, heartbeat_interval=heartbeat_interval))
