"""
客户端错误收集API

接收和处理来自前端的错误报告，用于监控和调试。
"""

from flask import Blueprint, request, jsonify
from datetime import datetime
import logging
import json
from typing import Dict, Any

# 创建错误收集专用的logger
error_logger = logging.getLogger("client_errors")
error_logger.setLevel(logging.ERROR)

# 如果没有handler，添加一个
if not error_logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s - CLIENT_ERROR - %(message)s")
    handler.setFormatter(formatter)
    error_logger.addHandler(handler)

bp = Blueprint("errors", __name__)


@bp.route("/errors", methods=["POST"])
def report_client_error():
    """
    接收客户端错误报告

    接收前端发送的错误信息，记录到专门的错误日志中，
    便于监控和调试前端问题。

    Returns:
        JSON响应确认错误已收到
    """
    try:
        error_data = request.get_json()

        if not error_data:
            return jsonify({"error": "No error data provided"}), 400

        # 提取错误信息
        error_info = error_data.get("error", {})
        context = error_data.get("context", {})

        # 构建日志消息
        log_message = {
            "message": error_info.get("message", "Unknown error"),
            "code": error_info.get("code", "UNKNOWN_ERROR"),
            "status": error_info.get("status"),
            "url": error_data.get("url", "Unknown"),
            "userAgent": error_data.get("userAgent", "Unknown"),
            "timestamp": error_data.get("timestamp", datetime.utcnow().isoformat()),
            "requestId": error_data.get("requestId"),
            "context": context,
        }

        # 记录到错误日志
        error_logger.error(json.dumps(log_message, ensure_ascii=False))

        # 可以在这里集成到错误监控服务
        # 例如: Sentry, Rollbar, Bugsnag等
        # sentry_sdk.capture_exception(error_data)

        # 统计错误频率（简单实现）
        _update_error_stats(error_info.get("code", "UNKNOWN_ERROR"))

        return (
            jsonify({"status": "received", "timestamp": datetime.utcnow().isoformat()}),
            200,
        )

    except Exception as e:
        # 处理错误报告本身的错误
        logging.error(f"处理客户端错误报告失败: {e}")
        return (
            jsonify({"error": "Failed to process error report", "message": str(e)}),
            500,
        )


@bp.route("/errors/stats", methods=["GET"])
def get_error_stats():
    """
    获取错误统计信息

    返回最近的错误统计，用于监控面板。

    Returns:
        JSON格式的错误统计信息
    """
    try:
        # 这里可以从缓存或数据库获取统计信息
        # 简单实现：从内存中获取
        stats = _get_error_stats()

        return (
            jsonify({"stats": stats, "timestamp": datetime.utcnow().isoformat()}),
            200,
        )

    except Exception as e:
        logging.error(f"获取错误统计失败: {e}")
        return jsonify({"error": "Failed to get error stats", "message": str(e)}), 500


# 简单的内存错误统计（生产环境应该使用Redis或数据库）
_error_stats: Dict[str, int] = {}


def _update_error_stats(error_code: str) -> None:
    """更新错误统计"""
    _error_stats[error_code] = _error_stats.get(error_code, 0) + 1


def _get_error_stats() -> Dict[str, Any]:
    """获取错误统计"""
    total_errors = sum(_error_stats.values())

    return {
        "total_errors": total_errors,
        "error_counts": dict(_error_stats),
        "most_common": (
            max(_error_stats.items(), key=lambda x: x[1]) if _error_stats else None
        ),
    }


@bp.route("/errors/health", methods=["GET"])
def error_collection_health():
    """
    错误收集服务健康检查

    Returns:
        服务状态信息
    """
    return (
        jsonify(
            {
                "status": "healthy",
                "service": "error_collection",
                "timestamp": datetime.utcnow().isoformat(),
                "total_errors_collected": sum(_error_stats.values()),
            }
        ),
        200,
    )
