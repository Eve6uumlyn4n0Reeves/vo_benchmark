import os
import pytest


def test_inmemory_fallback_when_redis_unavailable(monkeypatch):
    monkeypatch.setenv("EVENT_BUS", "redis")

    # Force import error for redis module
    import builtins

    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "redis":
            raise ImportError("redis not installed")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    from importlib import reload
    import src.api.services.events as events

    reload(events)

    # After reload, event_bus should be an instance of InMemoryEventBus
    from src.api.services.inmemory_impl import InMemoryEventBus

    assert isinstance(events.event_bus, InMemoryEventBus)

