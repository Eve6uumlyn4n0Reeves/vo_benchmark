"""
In‑memory implementations for event bus and task backend.
These are the defaults for single‑process deployments and offline use.
"""
from __future__ import annotations

import threading
from queue import Queue, Empty
from typing import Any, Dict, Generator, List, Optional
import time
import uuid
import logging
from datetime import datetime

from src.api.services.interfaces import IEventBus, ITaskBackend
from src.api.schemas.response import TaskResponse
from src.models.types import TaskStatus

logger = logging.getLogger(__name__)


class InMemoryEventBus(IEventBus):
    def __init__(self) -> None:
        self._subscribers: List[Queue] = []
        self._lock = threading.RLock()

    def publish(self, event: Dict[str, Any]) -> None:
        with self._lock:
            for q in list(self._subscribers):
                try:
                    q.put_nowait(event)
                except Exception as e:
                    logger.warning("Event publish failed, dropping a subscriber: %s", e)
                    try:
                        self._subscribers.remove(q)
                    except ValueError:
                        pass

    def subscribe(self) -> Queue:
        q: Queue = Queue(maxsize=100)
        with self._lock:
            self._subscribers.append(q)
        return q

    def unsubscribe(self, q: Queue) -> None:
        with self._lock:
            try:
                self._subscribers.remove(q)
            except ValueError:
                pass

    def sse_stream(self, queue: Queue, heartbeat_interval: float = 15.0) -> Generator[str, None, None]:
        last_heartbeat = time.time()
        try:
            while True:
                try:
                    event = queue.get(timeout=1.0)
                    yield self._format_sse(event)
                except Empty:
                    pass
                except Exception as e:
                    logger.debug("SSE loop non‑critical exception: %s", e)
                now = time.time()
                if now - last_heartbeat >= heartbeat_interval:
                    yield "event: heartbeat\n" + self._data_line({"ts": int(now)}) + "\n\n"
                    last_heartbeat = now
        finally:
            pass

    @staticmethod
    def _format_sse(event: Dict[str, Any]) -> str:
        event_type = event.get("type", "message")
        lines = [f"event: {event_type}", InMemoryEventBus._data_line(event.get("data", {}))]
        if "id" in event:
            lines.insert(0, f"id: {event['id']}")
        return "\n".join(lines) + "\n\n"

    @staticmethod
    def _data_line(data: Any) -> str:
        import json

        return "data: " + json.dumps(data, ensure_ascii=False)


class InMemoryTaskBackend(ITaskBackend):
    def __init__(self) -> None:
        self._tasks: Dict[str, TaskResponse] = {}
        self._task_logs: Dict[str, List[str]] = {}  # task_id -> list of log lines
        self._lock = threading.RLock()

    def create_task(self, description: str, experiment_id: Optional[str] = None) -> TaskResponse:
        with self._lock:
            task_id = str(uuid.uuid4())
            now = datetime.now()
            task = TaskResponse(
                task_id=task_id,
                status=TaskStatus.PENDING,
                message=description,
                progress=0.0,
                current_step=None,
                total_steps=None,
                experiment_id=experiment_id,
                created_at=now,
                updated_at=now,
                completed_at=None,
                error_details=None,
                estimated_remaining_time=None,
            )
            self._tasks[task_id] = task
            # Initialize empty log list for this task
            self._task_logs[task_id] = []
            return task

    def update_task(self, task_id: str, **kwargs) -> TaskResponse:
        with self._lock:
            if task_id not in self._tasks:
                raise KeyError(f"task not found: {task_id}")
            task = self._tasks[task_id]
            # Pydantic v2 prefers model_dump; keep fallback for v1
            if hasattr(task, "model_dump"):
                data = task.model_dump()
            else:
                data = task.dict()
            data.update(kwargs)
            data["updated_at"] = datetime.now()
            if kwargs.get("status") in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
                data["completed_at"] = datetime.now()
            updated = TaskResponse(**data)
            self._tasks[task_id] = updated
            return updated

    def get_task(self, task_id: str) -> Optional[TaskResponse]:
        with self._lock:
            return self._tasks.get(task_id)

    def cancel_task(self, task_id: str) -> bool:
        with self._lock:
            task = self._tasks.get(task_id)
            if not task:
                raise KeyError(f"task not found: {task_id}")
            if task.status not in [TaskStatus.PENDING, TaskStatus.RUNNING]:
                return False
            self.update_task(task_id, status=TaskStatus.CANCELLED, message="任务已被用户取消")
            return True

    def list_tasks(self, status: Optional[TaskStatus] = None) -> List[TaskResponse]:
        with self._lock:
            tasks = list(self._tasks.values())
            if status is not None:
                tasks = [t for t in tasks if t.status == status]
            tasks.sort(key=lambda t: t.created_at, reverse=True)
            return tasks

    def get_active_tasks(self) -> List[TaskResponse]:
        return self.list_tasks(TaskStatus.PENDING) + self.list_tasks(TaskStatus.RUNNING)

    def cleanup_completed_tasks(self, max_age_hours: int = 24) -> int:
        with self._lock:
            now = datetime.now()
            to_remove: List[str] = []
            for task_id, task in self._tasks.items():
                if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED] and task.completed_at and (now - task.completed_at).total_seconds() > max_age_hours * 3600:
                    to_remove.append(task_id)
            for tid in to_remove:
                del self._tasks[tid]
            return len(to_remove)

    def get_task_history(self, experiment_id: str, hours: int = 24) -> List[Dict[str, Any]]:
        with self._lock:
            now = datetime.now()
            cutoff = now.timestamp() - hours * 3600
            history: List[Dict[str, Any]] = []
            for task_id, task in self._tasks.items():
                if task.experiment_id == experiment_id and task.created_at.timestamp() >= cutoff:
                    rec = {
                        "task_id": task_id,
                        "status": task.status.value if hasattr(task.status, "value") else str(task.status),
                        "progress": task.progress,
                        "message": task.message,
                        "current_step": task.current_step,
                        "total_steps": task.total_steps,
                        "created_at": task.created_at.isoformat(),
                        "updated_at": task.updated_at.isoformat(),
                        "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                        "timestamp": task.updated_at.isoformat(),
                        "error_details": task.error_details,
                        "tasks": [
                            {
                                "task_id": task.task_id,
                                "status": task.status.value if hasattr(task.status, "value") else str(task.status),
                                "progress": task.progress,
                                "message": task.message,
                                "current_step": task.current_step,
                                "total_steps": task.total_steps,
                                "created_at": task.created_at.isoformat(),
                                "updated_at": task.updated_at.isoformat(),
                                "completed_at": task.completed_at.isoformat() if task.completed_at else None,
                            }
                        ],
                        "system_metrics": {
                            "cpu_usage": 0.0,
                            "memory_usage": 0.0,
                            "disk_usage": 0.0,
                            "active_tasks": len(self.get_active_tasks()),
                        },
                        "total_tasks": 1,
                        "completed_tasks": 1 if task.status in [TaskStatus.COMPLETED] else 0,
                        "failed_tasks": 1 if task.status in [TaskStatus.FAILED] else 0,
                        "average_processing_speed": (task.progress / max((task.completed_at - task.created_at).total_seconds(), 1e-6)) if task.completed_at else 0.0,
                        "total_processing_time": (task.completed_at - task.created_at).total_seconds() if task.completed_at else (datetime.now() - task.created_at).total_seconds(),
                        "started_at": task.created_at.isoformat(),
                        "estimated_completion": None,
                    }
                    history.append(rec)
            history.sort(key=lambda x: x["timestamp"], reverse=True)
            return history

    def get_task_logs(self, task_id: str) -> List[str]:
        """获取任务日志"""
        with self._lock:
            return self._task_logs.get(task_id, []).copy()

    def append_task_log(self, task_id: str, log_line: str) -> None:
        """添加任务日志"""
        with self._lock:
            if task_id not in self._task_logs:
                self._task_logs[task_id] = []
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            formatted_log = f"[{timestamp}] {log_line}"
            self._task_logs[task_id].append(formatted_log)

            # Keep only last 1000 log lines to prevent memory issues
            if len(self._task_logs[task_id]) > 1000:
                self._task_logs[task_id] = self._task_logs[task_id][-1000:]

