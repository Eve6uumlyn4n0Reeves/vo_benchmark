"""
API Middleware Package

Unified middleware setup for the Flask application, including:
- Request ID injection
- Timing and payload size headers
- Optional simple rate limiting (in-memory)
- Content-Type validation for JSON endpoints
- Centralized error handling (via error_handler module)

Author:
    VO-Benchmark Team

Version:
    1.1.0
"""

from __future__ import annotations

import logging
import time
import uuid
from functools import wraps
from typing import Callable, Any, Optional, Tuple

from flask import Flask, request, g, current_app, jsonify

from .error_handler import error_handler, setup_error_handling, input_validator

logger = logging.getLogger(__name__)


def setup_middleware(app: Flask) -> None:
    """Register all runtime middlewares on the Flask app.

    This preserves previous behavior provided by the legacy module-level
    middleware (now consolidated here), ensuring backward compatibility
    for headers expected by the frontend (x-response-time, x-payload-size,
    x-compressed) and request tracing (x-request-id).
    """
    setup_request_id_middleware(app)
    setup_timing_middleware(app)
    setup_rate_limiting_middleware(app)
    setup_content_type_middleware(app)


def setup_request_id_middleware(app: Flask) -> None:
    """Assign a unique request ID and echo it in responses."""

    @app.before_request
    def add_request_id():
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        g.request_id = request_id
        logger.info(f"请求开始 [{g.request_id}]: {request.method} {request.url}")

    @app.after_request
    def add_request_id_to_response(response):
        if hasattr(g, "request_id"):
            response.headers["X-Request-ID"] = g.request_id
            logger.info(f"请求结束 [{g.request_id}]: {response.status_code}")
        return response


def setup_timing_middleware(app: Flask) -> None:
    """Record request duration and payload size; mark compression flag."""

    @app.before_request
    def start_timer():
        g.start_time = time.time()

    @app.after_request
    def add_timing_header(response):
        if hasattr(g, "start_time"):
            duration = time.time() - g.start_time
            response.headers["X-Response-Time"] = f"{duration:.3f}s"

            # 对于流式/直通响应（如 send_file），不要触碰 response 数据
            if getattr(response, "direct_passthrough", False):
                payload_size = None
            else:
                try:
                    data = response.get_data()
                    payload_size = len(data) if data else 0
                except Exception:
                    payload_size = None
            response.headers["X-Payload-Size"] = str(payload_size) if payload_size is not None else "streaming"

            # 检查是否压缩（仅依据头部）
            is_compressed = 'gzip' in response.headers.get('Content-Encoding', '') or \
                            'br' in response.headers.get('Content-Encoding', '')
            response.headers["X-Compressed"] = "true" if is_compressed else "false"

            # Slow request logging threshold (seconds)
            if duration > app.config.get("SLOW_REQUEST_THRESHOLD", 1.0):
                req_id = getattr(g, "request_id", "unknown")
                logger.warning(
                    f"慢请求 [{req_id}]: {request.method} {request.url} - {duration:.3f}s, payload: {payload_size} bytes"
                )

            # Large payload logging (> 5MB)
            if payload_size is not None and payload_size > 5 * 1024 * 1024:
                req_id = getattr(g, "request_id", "unknown")
                logger.warning(
                    f"大响应 [{req_id}]: {request.method} {request.url} - {payload_size} bytes, compressed: {is_compressed}"
                )

        return response


def setup_rate_limiting_middleware(app: Flask) -> None:
    """Very simple in-memory rate limiter (per IP, per minute)."""

    request_counts: dict[str, list[int]] = {}

    @app.before_request
    def check_rate_limit():
        if not app.config.get("ENABLE_RATE_LIMITING", False):
            return

        client_ip = request.environ.get("HTTP_X_FORWARDED_FOR", request.remote_addr)
        current_ts = int(time.time())
        window_start = current_ts - 60

        if client_ip in request_counts:
            request_counts[client_ip] = [ts for ts in request_counts[client_ip] if ts > window_start]
        else:
            request_counts[client_ip] = []

        max_requests = int(app.config.get("RATE_LIMIT_PER_MINUTE", 60))
        if len(request_counts[client_ip]) >= max_requests:
            logger.warning(f"速率限制触发: {client_ip} - {len(request_counts[client_ip])} 请求/分钟")
            return (
                jsonify({
                    "error": "Rate limit exceeded",
                    "message": f"Maximum {max_requests} requests per minute allowed",
                }),
                429,
            )

        request_counts[client_ip].append(current_ts)


def setup_content_type_middleware(app: Flask) -> None:
    """Validate JSON Content-Type for write operations (POST/PUT/PATCH)."""

    @app.before_request
    def validate_content_type():
        if request.method in ["POST", "PUT", "PATCH"]:
            if (not request.is_json and request.content_length and request.content_length > 0):
                # Allow file uploads
                if not request.content_type or not request.content_type.startswith("multipart/form-data"):
                    return (
                        jsonify({
                            "error": "Invalid content type",
                            "message": "Content-Type must be application/json for JSON requests",
                        }),
                        400,
                    )


# Re-export error handling symbols for convenience
__all__ = [
    "error_handler",
    "setup_error_handling",
    "input_validator",
    "setup_middleware",
    "setup_request_id_middleware",
    "setup_timing_middleware",
    "setup_rate_limiting_middleware",
    "setup_content_type_middleware",
]
