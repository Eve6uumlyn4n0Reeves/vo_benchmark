from datetime import datetime
from src.api.schemas.response import TaskResponse
from src.models.types import TaskStatus
from src.api.services.task import task_service


def test_sse_event_status_serialization():
    # 创建任务
    task = task_service.create_task(description="unit-test")

    # 运行中
    updated = task_service.update_task(task.task_id, status=TaskStatus.RUNNING, progress=0.5, message="running")
    # TaskResponse 使用 use_enum_values=True，所以 status 输出为字符串
    assert updated.status == "running"

    # SSE 发布时转换为字符串的逻辑在 task_service 中已实现
    # 此处仅确认 TaskResponse 的约束 progress in [0,1]
    assert 0.0 <= updated.progress <= 1.0

    # 完成
    updated2 = task_service.update_task(task.task_id, status=TaskStatus.COMPLETED, progress=1.0, message="done")
    assert updated2.status == "completed"
    assert updated2.progress == 1.0


def test_task_response_progress_bounds():
    # TaskResponse 本身限制 progress ∈ [0,1]
    # 注意：TaskResponse 使用 use_enum_values=True，所以 status 会被序列化为字符串
    now = datetime.now()
    tr = TaskResponse(
        task_id="t",
        status=TaskStatus.PENDING,
        message="m",
        progress=0.0,
        current_step=None,
        total_steps=None,
        experiment_id=None,
        created_at=now,
        updated_at=now,
        completed_at=None,
        error_details=None
    )
    assert tr.progress == 0.0
    assert tr.status == "pending"  # 枚举被序列化为字符串值

