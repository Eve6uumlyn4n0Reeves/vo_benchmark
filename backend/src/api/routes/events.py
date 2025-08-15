from __future__ import annotations

from flask import Blueprint, Response, stream_with_context, request
from typing import Any
from src.api.services.events import event_bus

bp = Blueprint("events", __name__, url_prefix="/api/v1/events")


@bp.route("/", methods=["GET"])
def subscribe_events() -> Any:
    """Server-Sent Events 订阅端点

    用于实时获取实验、任务等事件更新。前端可使用 EventSource 订阅：
      const es = new EventSource('/api/v1/events/');
    """
    # 每个连接创建独立队列
    q = event_bus.subscribe()

    def stream():
        try:
            yield from event_bus.sse_stream(q)
        finally:
            event_bus.unsubscribe(q)

    headers = {
        "Content-Type": "text/event-stream",
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        # 允许 CORS（与全局 CORS 配置配合）
        "X-Accel-Buffering": "no",
    }
    return Response(stream_with_context(stream()), headers=headers)
