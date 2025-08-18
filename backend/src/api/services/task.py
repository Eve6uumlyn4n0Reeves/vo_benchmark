#
# 功能: 提供任务管理的业务逻辑服务。
#
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
import uuid
import threading
import logging
from src.api.schemas.response import TaskResponse
from src.models.types import TaskStatus, ErrorCode
from src.api.exceptions.base import TaskNotFoundError
from src.api.services.events import event_bus
from src.api.services.event_types import EVENT_TASK_UPDATED, EVENT_TASK_LOG
from src.api.services.inmemory_impl import InMemoryTaskBackend
from src.api.services.interfaces import ITaskBackend

logger = logging.getLogger(__name__)


class TaskService:
    """任务管理服务（基于 ITaskBackend，默认内存实现）"""

    def __init__(self, backend: ITaskBackend | None = None):
        self._backend: ITaskBackend = backend or InMemoryTaskBackend()
        self._lock = threading.RLock()

    def create_task(
        self, description: str, experiment_id: Optional[str] = None
    ) -> TaskResponse:
        """创建新任务（委托给后端实现）"""
        with self._lock:
            return self._backend.create_task(description, experiment_id)

    def update_task(self, task_id: str, **kwargs) -> TaskResponse:
        """更新任务状态（委托给后端实现）"""
        with self._lock:
            try:
                updated_task = self._backend.update_task(task_id, **kwargs)
            except KeyError:
                raise TaskNotFoundError(f"任务未找到: {task_id}")

            # 推送 SSE 事件（任务更新）
            try:
                event_bus.publish(
                    {
                        "type": EVENT_TASK_UPDATED,
                        "data": {
                            "task_id": updated_task.task_id,
                            "status": getattr(updated_task.status, "value", str(updated_task.status)),
                            "progress": updated_task.progress,
                            "message": updated_task.message,
                            "experiment_id": updated_task.experiment_id,
                        },
                    }
                )
            except Exception as e:
                logger.debug("publish task_updated failed: %s", e)

            return updated_task

    def get_task(self, task_id: str) -> Optional[TaskResponse]:
        """获取任务详情（委托给后端实现）"""
        with self._lock:
            return self._backend.get_task(task_id)

    def cancel_task(self, task_id: str) -> bool:
        """取消任务（委托给后端实现）"""
        with self._lock:
            try:
                ok = self._backend.cancel_task(task_id)
                return bool(ok)
            except KeyError:
                raise TaskNotFoundError(f"任务未找到: {task_id}")

    def list_tasks(self, status: Optional[TaskStatus] = None) -> List[TaskResponse]:
        """列出任务（委托给后端实现）"""
        with self._lock:
            tasks = self._backend.list_tasks(status)
            return list(tasks)

    def get_active_tasks(self) -> List[TaskResponse]:
        """获取活跃任务（委托给后端实现）"""
        active = self.list_tasks(TaskStatus.PENDING) + self.list_tasks(TaskStatus.RUNNING)
        return list(active)

    def cleanup_completed_tasks(self, max_age_hours: int = 24) -> int:
        """清理已完成的旧任务（委托给后端实现）"""
        with self._lock:
            count = self._backend.cleanup_completed_tasks(max_age_hours)
            return int(count)

    def get_task_history(
        self, experiment_id: str, hours: int = 24
    ) -> List[Dict[str, Any]]:
        """获取指定实验的任务历史（委托给后端实现）"""
        with self._lock:
            hist = self._backend.get_task_history(experiment_id, hours)
            return list(hist)

    def get_task_logs(self, task_id: str) -> List[str]:
        """获取任务日志（委托给后端实现）"""
        with self._lock:
            return self._backend.get_task_logs(task_id)

    def append_task_log(self, task_id: str, log_line: str) -> None:
        """添加任务日志并通过SSE推送"""
        with self._lock:
            # 存储日志到后端
            self._backend.append_task_log(task_id, log_line)

        try:
            # 推送日志事件
            event_bus.publish(
                {
                    "type": EVENT_TASK_LOG,
                    "data": {
                        "task_id": task_id,
                        "line": log_line,
                        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                    },
                }
            )
        except Exception as e:
            logger.debug("publish task_log failed: %s", e)


# 全局任务服务实例
task_service = TaskService()
