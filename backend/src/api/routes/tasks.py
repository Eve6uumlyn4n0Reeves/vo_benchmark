#
# 功能: 定义 /tasks API 路由。
#
from flask import Blueprint, request, jsonify
from src.api.services.task import task_service
from src.api.exceptions.base import VOBenchmarkException
from src.models.types import TaskStatus
import logging
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)

bp = Blueprint("tasks", __name__, url_prefix="/api/v1/tasks")


def _to_serializable(value):
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, list):
        return [_to_serializable(v) for v in value]
    if isinstance(value, dict):
        return {k: _to_serializable(v) for k, v in value.items()}
    return value


@bp.route("/", methods=["GET"])
def list_tasks():
    """获取任务列表"""
    try:
        # 获取状态过滤参数
        status_param = request.args.get("status")
        status = None
        if status_param:
            try:
                status = TaskStatus(status_param)
            except ValueError:
                return jsonify({"error": f"无效的任务状态: {status_param}"}), 400

        tasks = task_service.list_tasks(status)
        payload = []
        for task in tasks:
            # Ensure consistent serialization with enum values as strings
            raw = None
            md = getattr(task, "model_dump", None)
            if callable(md):
                raw = md()
            if not isinstance(raw, dict):
                dct = getattr(task, "dict", None)
                if callable(dct):
                    raw = dct()
            if not isinstance(raw, dict):
                raw = vars(task) if not isinstance(task, dict) else task
            payload.append(_to_serializable(raw))
        return jsonify(payload), 200

    except VOBenchmarkException as e:
        logger.error(f"获取任务列表业务错误: {e}")
        return jsonify(e.to_dict()), e.status_code
    except Exception as e:
        logger.error(f"获取任务列表内部错误: {e}")
        return jsonify({"error": "内部服务器错误"}), 500


@bp.route("/<string:task_id>", methods=["GET"])
def get_task(task_id: str):
    """获取单个任务状态"""
    try:
        task = task_service.get_task(task_id)
        if task is None:
            return jsonify({"error": "任务未找到"}), 404

        # Ensure consistent serialization with enum values as strings
        raw = None
        md = getattr(task, "model_dump", None)
        if callable(md):
            raw = md()
        if not isinstance(raw, dict):
            dct = getattr(task, "dict", None)
            if callable(dct):
                raw = dct()
        if not isinstance(raw, dict):
            raw = vars(task) if not isinstance(task, dict) else task
        return jsonify(_to_serializable(raw)), 200

    except VOBenchmarkException as e:
        logger.error(f"获取任务状态业务错误: {e}")
        return jsonify(e.to_dict()), e.status_code
    except Exception as e:
        logger.error(f"获取任务状态内部错误: {e}")
        return jsonify({"error": "内部服务器错误"}), 500


@bp.route("/<string:task_id>/cancel", methods=["POST"])
def cancel_task(task_id: str):
    """取消任务"""
    try:
        success = task_service.cancel_task(task_id)
        return jsonify({"success": success}), 200

    except VOBenchmarkException as e:
        logger.error(f"取消任务业务错误: {e}")
        return jsonify(e.to_dict()), e.status_code
    except Exception as e:
        logger.error(f"取消任务内部错误: {e}")
        return jsonify({"error": "内部服务器错误"}), 500


@bp.route("/<string:task_id>/logs", methods=["GET"])
def get_task_logs(task_id: str):
    """获取任务日志"""
    try:
        # 验证任务是否存在
        task = task_service.get_task(task_id)
        if task is None:
            return jsonify({"error": "任务未找到"}), 404

        # 获取真实的任务日志
        logs = task_service.get_task_logs(task_id)

        # 如果没有日志，添加一些基本信息
        if not logs:
            logs = [
                f"[{task.created_at.strftime('%Y-%m-%d %H:%M:%S')}] 任务已创建: {task.message}",
                f"[{task.updated_at.strftime('%Y-%m-%d %H:%M:%S')}] 当前状态: {task.status.value if hasattr(task.status, 'value') else str(task.status)}",
            ]

        return jsonify({"logs": logs}), 200

    except VOBenchmarkException as e:
        logger.error(f"获取任务日志业务错误: {e}")
        return jsonify(e.to_dict()), e.status_code
    except Exception as e:
        logger.error(f"获取任务日志内部错误: {e}")
        return jsonify({"error": "内部服务器错误"}), 500


@bp.route("/<string:task_id>/logs", methods=["POST"])
def append_task_log(task_id: str):
    """添加任务日志（用于演示SSE推送）"""
    try:
        # 验证任务是否存在
        task = task_service.get_task(task_id)
        if task is None:
            return jsonify({"error": "任务未找到"}), 404

        # 获取日志内容
        data = request.get_json()
        if not data or 'log_line' not in data:
            return jsonify({"error": "缺少日志内容"}), 400

        log_line = data['log_line']

        # 添加日志并推送SSE事件
        task_service.append_task_log(task_id, log_line)

        return jsonify({"success": True}), 200

    except VOBenchmarkException as e:
        logger.error(f"添加任务日志业务错误: {e}")
        return jsonify(e.to_dict()), e.status_code
    except Exception as e:
        logger.error(f"添加任务日志内部错误: {e}")
        return jsonify({"error": "内部服务器错误"}), 500
