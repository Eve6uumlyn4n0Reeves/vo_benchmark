"""
Event bus facade that exposes a default in‑memory implementation
but allows future swapping (e.g., Redis Pub/Sub) without changing imports.
Public API kept: `event_bus` and `sse_stream`.
"""
from __future__ import annotations

from queue import Queue
from typing import Generator

import os

EVENT_BUS_BACKEND = os.getenv("EVENT_BUS", "inmem").lower()
if EVENT_BUS_BACKEND == "redis":
    try:
        from src.api.services.redis_eventbus import RedisEventBus
        event_bus = RedisEventBus()
    except Exception as e:
        # Fallback to in-memory with warning
        from src.api.services.inmemory_impl import InMemoryEventBus
        import logging as _log
        _log.getLogger(__name__).warning(f"RedisEventBus unavailable ({e}); falling back to InMemoryEventBus")
        event_bus = InMemoryEventBus()
else:
    from src.api.services.inmemory_impl import InMemoryEventBus
    event_bus = InMemoryEventBus()

# Expose a function compatible with existing imports
from typing import cast

def sse_stream(queue: Queue, heartbeat_interval: float = 15.0) -> Generator[str, None, None]:
    return cast(Generator[str, None, None], event_bus.sse_stream(queue, heartbeat_interval=heartbeat_interval))
