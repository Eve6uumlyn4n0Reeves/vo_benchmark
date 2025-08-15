#
# 功能: 定义API中间件。
#
import time
import uuid
from functools import wraps
from flask import Flask, request, g, current_app, jsonify
from typing import Callable, Any
import logging

logger = logging.getLogger(__name__)


def setup_middleware(app: Flask) -> None:
    """设置所有中间件"""
    setup_request_id_middleware(app)
    setup_timing_middleware(app)
    setup_rate_limiting_middleware(app)
    setup_content_type_middleware(app)


def setup_request_id_middleware(app: Flask) -> None:
    """设置请求ID中间件，为每个请求生成唯一ID"""

    @app.before_request
    def add_request_id():
        """为每个请求添加唯一ID"""
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        g.request_id = request_id

        # 添加到日志上下文
        if hasattr(g, "request_id"):
            logger.info(f"请求开始 [{g.request_id}]: {request.method} {request.url}")

    @app.after_request
    def add_request_id_to_response(response):
        """将请求ID添加到响应头"""
        if hasattr(g, "request_id"):
            response.headers["X-Request-ID"] = g.request_id
            logger.info(f"请求结束 [{g.request_id}]: {response.status_code}")
        return response


def setup_timing_middleware(app: Flask) -> None:
    """设置请求计时中间件"""

    @app.before_request
    def start_timer():
        """记录请求开始时间"""
        g.start_time = time.time()

    @app.after_request
    def add_timing_header(response):
        """添加响应时间头和性能监控信息"""
        if hasattr(g, "start_time"):
            duration = time.time() - g.start_time
            response.headers["X-Response-Time"] = f"{duration:.3f}s"

            # 添加payload大小信息
            payload_size = len(response.get_data()) if response.get_data() else 0
            response.headers["X-Payload-Size"] = str(payload_size)

            # 检查是否压缩
            is_compressed = 'gzip' in response.headers.get('Content-Encoding', '') or \
                          'br' in response.headers.get('Content-Encoding', '')
            response.headers["X-Compressed"] = "true" if is_compressed else "false"

            # 记录慢请求和大响应
            if duration > app.config.get("SLOW_REQUEST_THRESHOLD", 1.0):
                request_id = getattr(g, "request_id", "unknown")
                logger.warning(
                    f"慢请求 [{request_id}]: {request.method} {request.url} - {duration:.3f}s, payload: {payload_size} bytes"
                )

            # 记录大响应
            if payload_size > 5 * 1024 * 1024:  # > 5MB
                request_id = getattr(g, "request_id", "unknown")
                logger.warning(
                    f"大响应 [{request_id}]: {request.method} {request.url} - {payload_size} bytes, compressed: {is_compressed}"
                )

        return response


def setup_rate_limiting_middleware(app: Flask) -> None:
    """设置简单的速率限制中间件"""

    # 简单的内存存储，生产环境应使用Redis
    request_counts = {}

    @app.before_request
    def check_rate_limit():
        """检查速率限制"""
        if not app.config.get("ENABLE_RATE_LIMITING", False):
            return

        client_ip = request.environ.get("HTTP_X_FORWARDED_FOR", request.remote_addr)
        current_time = int(time.time())
        window_start = current_time - 60  # 1分钟窗口

        # 清理过期记录
        if client_ip in request_counts:
            request_counts[client_ip] = [
                timestamp
                for timestamp in request_counts[client_ip]
                if timestamp > window_start
            ]
        else:
            request_counts[client_ip] = []

        # 检查请求数量
        max_requests = app.config.get("RATE_LIMIT_PER_MINUTE", 60)
        if len(request_counts[client_ip]) >= max_requests:
            logger.warning(
                f"速率限制触发: {client_ip} - {len(request_counts[client_ip])} 请求/分钟"
            )
            return (
                jsonify(
                    {
                        "error": "Rate limit exceeded",
                        "message": f"Maximum {max_requests} requests per minute allowed",
                    }
                ),
                429,
            )

        # 记录当前请求
        request_counts[client_ip].append(current_time)


def setup_content_type_middleware(app: Flask) -> None:
    """设置内容类型验证中间件"""

    @app.before_request
    def validate_content_type():
        """验证POST/PUT请求的内容类型"""
        if request.method in ["POST", "PUT", "PATCH"]:
            if (
                not request.is_json
                and request.content_length
                and request.content_length > 0
            ):
                # 检查是否是文件上传
                if not request.content_type or not request.content_type.startswith(
                    "multipart/form-data"
                ):
                    return (
                        jsonify(
                            {
                                "error": "Invalid content type",
                                "message": "Content-Type must be application/json for JSON requests",
                            }
                        ),
                        400,
                    )


def require_json(f: Callable) -> Callable:
    """装饰器：要求请求必须是JSON格式"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not request.is_json:
            return (
                jsonify(
                    {"error": "Invalid content type", "message": "Request must be JSON"}
                ),
                400,
            )
        return f(*args, **kwargs)

    return decorated_function


def validate_request_size(max_size: int = None):
    """装饰器：验证请求大小"""

    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            max_content_length = max_size or current_app.config.get(
                "MAX_CONTENT_LENGTH", 16 * 1024 * 1024
            )

            if request.content_length and request.content_length > max_content_length:
                return (
                    jsonify(
                        {
                            "error": "Request too large",
                            "message": f"Request size exceeds maximum allowed size of {max_content_length} bytes",
                        }
                    ),
                    413,
                )

            return f(*args, **kwargs)

        return decorated_function

    return decorator


def log_request_details(f: Callable) -> Callable:
    """装饰器：记录详细的请求信息"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        request_id = getattr(g, "request_id", "unknown")

        # 记录请求详情
        logger.info(
            f"请求详情 [{request_id}]: "
            f"方法={request.method}, "
            f"路径={request.path}, "
            f"参数={dict(request.args)}, "
            f"IP={request.remote_addr}"
        )

        # 记录请求体（仅用于调试，生产环境应谨慎）
        if current_app.debug and request.is_json:
            logger.debug(f"请求体 [{request_id}]: {request.get_json()}")

        try:
            result = f(*args, **kwargs)
            logger.info(f"请求成功 [{request_id}]")
            return result
        except Exception as e:
            logger.error(f"请求失败 [{request_id}]: {str(e)}")
            raise

    return decorated_function


def cache_response(timeout: int = 300):
    """装饰器：缓存响应（简单实现，生产环境应使用Redis）"""

    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # 简单的内存缓存实现
            # 生产环境应使用Redis或其他缓存系统
            cache_key = f"{request.method}:{request.full_path}"

            # 这里只是示例，实际实现需要更复杂的缓存逻辑
            return f(*args, **kwargs)

        return decorated_function

    return decorator
