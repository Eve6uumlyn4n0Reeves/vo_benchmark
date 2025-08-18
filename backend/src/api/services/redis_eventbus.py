"""
Redis-based EventBus implementation compatible with IEventBus.
- Optional: used when EVENT_BUS=redis and REDIS_URL is configured
- Falls back to in-memory if Redis is unavailable (caller decides which to import)

Notes:
- Uses pub/sub channel 'events'
- Subscriber creates a background thread to forward messages into a local Queue
- Designed for Windows-friendly operation
"""
from __future__ import annotations

from typing import Any, Dict, List
from queue import Queue
import json
import threading
import logging
import os

logger = logging.getLogger(__name__)

try:
    import redis  # type: ignore
except Exception:
    redis = None  # type: ignore


class RedisEventBus:
    def __init__(self, channel: str = "events", url: str | None = None) -> None:
        if redis is None:
            raise RuntimeError("redis-py is not installed. Please install redis>=5.0.0")
        self._channel = channel
        self._url = url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self._redis = redis.from_url(self._url, decode_responses=True)
        self._subscribers: List[Queue] = []
        self._lock = threading.RLock()

    def publish(self, event: Dict[str, Any]) -> None:
        try:
            self._redis.publish(self._channel, json.dumps(event, ensure_ascii=False))
        except Exception as e:
            logger.warning("RedisEventBus publish failed: %s", e)

    def subscribe(self) -> Queue:
        q: Queue = Queue(maxsize=100)
        with self._lock:
            self._subscribers.append(q)
        threading.Thread(target=self._subscriber_loop, args=(q,), daemon=True).start()
        return q

    def unsubscribe(self, q: Queue) -> None:
        with self._lock:
            try:
                self._subscribers.remove(q)
            except ValueError:
                pass

    def _subscriber_loop(self, q: Queue) -> None:
        try:
            pubsub = self._redis.pubsub()
            pubsub.subscribe(self._channel)
            for msg in pubsub.listen():
                if msg and msg.get("type") == "message":
                    try:
                        payload = json.loads(msg.get("data", "{}"))
                    except Exception:
                        payload = {"type": "message", "data": {"raw": msg.get("data")}}
                    try:
                        q.put(payload, timeout=1.0)
                    except Exception:
                        pass
        except Exception as e:
            logger.warning("RedisEventBus subscriber loop terminated: %s", e)

