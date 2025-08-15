from pathlib import Path
from datetime import datetime
from src.api.services.experiment import ExperimentService
from src.api.schemas.request import CreateExperimentRequest
from src.models.types import TaskStatus


def make_request(tmp_path: Path) -> CreateExperimentRequest:
    p = tmp_path / "tum_root" / "seq1" / "rgb"
    p.mkdir(parents=True, exist_ok=True)
    # 最少两张
    (p / "1.0.png").write_bytes(b"\x89PNG\r\n\x1a\n")
    (p / "1.033.png").write_bytes(b"\x89PNG\r\n\x1a\n")

    return CreateExperimentRequest(
        name="ut-exp",
        dataset_path=str(tmp_path / "tum_root"),
        output_dir=str(tmp_path / "out"),
        feature_types=["ORB"],
        ransac_types=["STANDARD"],
        sequences=["seq1"],
        num_runs=1,
        parallel_jobs=1,
        random_seed=0,
        save_frame_data=False,
        save_descriptors=False,
        compute_pr_curves=False,
        analyze_ransac=False,
        ransac_success_threshold=0.5,
        max_features=500,
        feature_params={},
        ransac_threshold=1.0,
        ransac_confidence=0.999,
        ransac_max_iters=1000
    )


def test_experiment_lifecycle_minimal(tmp_path: Path):
    svc = ExperimentService()
    req = make_request(tmp_path)

    task = svc.create_experiment(req)
    assert task.task_id

    # 由于后台线程执行，简单等待片刻或直接查询列表与删除流程
    # 这里不做长时间等待，只验证接口可调用
    listing = svc.list_experiments()
    assert isinstance(listing, dict)

    # 调用 get_experiment 将返回真实状态（可能仍在运行或已完成）
    exp_id = task.experiment_id
    exp = svc.get_experiment(exp_id)
    assert exp.experiment_id == exp_id
    assert exp.status in {TaskStatus.PENDING, TaskStatus.RUNNING, TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED}

    # 删除（异步可能未完成，但接口应具备幂等删除能力）
    svc.delete_experiment(exp_id)

