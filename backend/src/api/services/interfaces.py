"""
Interfaces for task queue/storage and event bus.
These protocols allow swapping implementations (in‑memory by default;
Redis or other backends can be added without touching business code).
"""
from __future__ import annotations

from typing import Protocol, Optional, Dict, Any, List, Generator
from queue import Queue
from src.api.schemas.response import TaskResponse
from src.models.types import TaskStatus


class IEventBus(Protocol):
    def publish(self, event: Dict[str, Any]) -> None:
        """Broadcast an event to all subscribers."""
        ...

    def subscribe(self) -> Queue:
        """Create and register a new subscriber queue."""
        ...

    def unsubscribe(self, q: Queue) -> None:
        """Unregister a subscriber queue."""
        ...


class ITaskBackend(Protocol):
    """Task storage/queue backend interface (no external deps required)."""

    def create_task(self, description: str, experiment_id: Optional[str] = None) -> TaskResponse:
        ...

    def update_task(self, task_id: str, **kwargs) -> TaskResponse:
        ...

    def get_task(self, task_id: str) -> Optional[TaskResponse]:
        ...

    def cancel_task(self, task_id: str) -> bool:
        ...

    def list_tasks(self, status: Optional[TaskStatus] = None) -> List[TaskResponse]:
        ...

    def get_active_tasks(self) -> List[TaskResponse]:
        ...

    def cleanup_completed_tasks(self, max_age_hours: int = 24) -> int:
        ...

    def get_task_history(self, experiment_id: str, hours: int = 24) -> List[Dict[str, Any]]:
        ...

    def get_task_logs(self, task_id: str) -> List[str]:
        """获取任务日志"""
        ...

    def append_task_log(self, task_id: str, log_line: str) -> None:
        """添加任务日志"""
        ...


# Helper type for SSE generators
SSEGenerator = Generator[str, None, None]

