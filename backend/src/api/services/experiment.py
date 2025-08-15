#
# 功能: 提供实验管理的业务逻辑服务。
#
from typing import List, Optional
import threading
from pathlib import Path
from datetime import datetime
from src.api.schemas.request import CreateExperimentRequest
from src.api.schemas.response import TaskResponse, ExperimentResponse
from src.models.experiment import ExperimentConfig, ExperimentSummary
from src.models.types import FeatureType, RANSACType, TaskStatus
from src.storage.experiment import ExperimentStorage
from src.storage.filesystem import FileSystemStorage
from src.api.exceptions.base import ExperimentNotFoundError, ValidationError
from src.api.services.task import task_service
from src.utils.output_manager import output_manager
from src.api.services.events import event_bus
import logging

logger = logging.getLogger(__name__)


class ExperimentService:
    """实验管理服务（单例模式）"""

    _instance = None
    _lock = threading.RLock()

    def __new__(cls):
        """单例模式，避免重复初始化"""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        """初始化实验服务（单例模式）"""
        if self._initialized:
            return

        # 初始化存储（统一到配置的 RESULTS_ROOT/experiments 路径）
        # 变更策略：优先使用统一配置管理 get_config().storage.results_root；
        # 若配置异常，则回退到 ./results，避免读写到仓库内置 data 目录。
        cfg_results_root = None
        try:
            from src.config.manager import get_config

            cfg_results_root = get_config().storage.results_root
        except Exception:
            cfg_results_root = None

        chosen_base = (
            Path(cfg_results_root).resolve()
            if cfg_results_root
            else Path("./results").resolve()
        )
        chosen_base.mkdir(parents=True, exist_ok=True)
        logger.info(f"ExperimentService initializing, base={chosen_base}")

        experiments_root = (chosen_base / "experiments").resolve()
        experiments_root.mkdir(parents=True, exist_ok=True)

        # 存储根指向 base（便于使用 key 前缀 'experiments/<id>/...'）
        storage = FileSystemStorage(str(chosen_base))
        self.experiment_storage = ExperimentStorage(storage)
        logger.info(
            f"ExperimentService storage ready: root={getattr(storage,'root_dir',None)}"
        )

        # 输出目录管理器指向 experiments 目录
        output_manager.root_output_dir = experiments_root
        output_manager.ensure_root_directory()
        logger.info(
            f"ExperimentService output root set to {output_manager.root_output_dir}"
        )

        self._initialized = True

    def create_experiment(self, request: CreateExperimentRequest) -> TaskResponse:
        """
        1. 将请求转换为内部的 ExperimentConfig。
        2. 创建一个新任务 (Task)。
        3. 在后台线程中启动 ExperimentManager.run_experiment。
        4. 返回初始的 TaskResponse。
        """
        try:
            # 1. 创建输出目录结构
            dataset_name = Path(request.dataset_path).name
            output_config = output_manager.create_experiment_directory(
                experiment_name=request.name, dataset_name=dataset_name
            )

            # 2. 更新请求中的输出目录为自动生成的目录
            request.output_dir = output_config.root_dir

            # 3. 验证和转换请求数据
            config = self._convert_request_to_config(request)

            # 4. 创建新任务
            experiment_id = output_config.experiment_id
            task = task_service.create_task(
                description=f"运行实验: {request.name}", experiment_id=experiment_id
            )

            # 3. 在后台线程中启动实验
            def run_experiment_async():
                try:
                    task_service.update_task(
                        task.task_id,
                        status=TaskStatus.RUNNING,
                        message="实验正在运行中...",
                    )
                    task_service.append_task_log(task.task_id, f"开始执行实验: {request.name}")
                    # 推送实验开始事件
                    try:
                        event_bus.publish(
                            {
                                "type": "experiment_started",
                                "data": {
                                    "experiment_id": experiment_id,
                                    "name": request.name,
                                },
                            }
                        )
                    except Exception:
                        pass

                    # 调用 ExperimentManager.run_experiment
                    from src.pipeline.manager import ExperimentManager

                    experiment_manager = ExperimentManager(
                        config, self.experiment_storage
                    )

                    def update_progress(progress, message):
                        task_service.update_task(
                            task.task_id, progress=progress, message=message
                        )
                        task_service.append_task_log(task.task_id, f"进度 {progress*100:.1f}%: {message}")
                        # 推送实验进度事件
                        try:
                            event_bus.publish(
                                {
                                    "type": "experiment_progress",
                                    "data": {
                                        "experiment_id": experiment_id,
                                        "name": request.name,
                                        "progress": progress,
                                        "message": message,
                                    },
                                }
                            )
                        except Exception:
                            pass

                    # 执行实验
                    algorithm_metrics = experiment_manager.run_experiment(
                        experiment_id, update_progress
                    )

                    task_service.update_task(
                        task.task_id,
                        status=TaskStatus.COMPLETED,
                        message="实验完成",
                        progress=1.0,
                    )
                    task_service.append_task_log(task.task_id, f"实验成功完成，共处理 {len(algorithm_metrics)} 个算法运行")
                    # 推送实验完成事件
                    try:
                        event_bus.publish(
                            {
                                "type": "experiment_completed",
                                "data": {
                                    "experiment_id": experiment_id,
                                    "name": request.name,
                                },
                            }
                        )
                    except Exception:
                        pass

                except Exception as e:
                    logger.error(f"实验执行失败: {e}")
                    task_service.append_task_log(task.task_id, f"实验执行失败: {str(e)}")
                    task_service.update_task(
                        task.task_id,
                        status=TaskStatus.FAILED,
                        message=f"实验执行失败: {str(e)}",
                        error_details={"error": str(e)},
                    )
                    # 推送实验失败事件
                    try:
                        event_bus.publish(
                            {
                                "type": "experiment_failed",
                                "data": {
                                    "experiment_id": experiment_id,
                                    "name": request.name,
                                    "error": str(e),
                                },
                            }
                        )
                    except Exception:
                        pass

            # 启动后台线程
            thread = threading.Thread(target=run_experiment_async, daemon=True)
            thread.start()

            # 在返回任务前，保存初始的实验摘要，确保前端列表能立即看到新实验
            try:
                from src.models.experiment import ExperimentSummary

                summary = ExperimentSummary(
                    experiment_id=experiment_id,
                    timestamp=datetime.now().isoformat(),
                    config=config,
                    total_runs=0,
                    successful_runs=0,
                    failed_runs=0,
                    algorithms_tested=[],
                    sequences_processed=[],
                )
                self.experiment_storage.save_experiment(experiment_id, summary)
            except Exception as save_err:
                logger.warning(f"保存初始实验摘要失败（不影响创建）：{save_err}")

            return task

        except Exception as e:
            logger.error(f"创建实验失败: {e}")
            raise ValidationError(f"创建实验失败: {str(e)}")

    def get_experiment(self, experiment_id: str) -> ExperimentResponse:
        """从存储中获取实验信息和摘要。"""
        try:
            experiment = self.experiment_storage.get_experiment(experiment_id)
            if experiment is None:
                raise ExperimentNotFoundError(f"实验未找到: {experiment_id}")

            # 真实状态与时间
            status = self._determine_experiment_status(experiment_id)
            created_at = datetime.fromisoformat(experiment.timestamp)
            completed_at = self._get_experiment_completion_time(experiment_id)

            # 算法列表：优先从存储扫描实际存在的完整算法键（含序列后缀），否则回退摘要
            try:
                results = self.experiment_storage.get_all_algorithm_results(
                    experiment_id
                )
                if results:
                    algorithms = [r.algorithm_key for r in results]
                else:
                    algorithms = (
                        experiment.algorithms_tested
                        if hasattr(experiment, "algorithms_tested")
                        else []
                    )
            except Exception:
                algorithms = (
                    experiment.algorithms_tested
                    if hasattr(experiment, "algorithms_tested")
                    else []
                )

            return ExperimentResponse(
                experiment_id=experiment.experiment_id,
                name=experiment.config.name,
                description=None,
                status=status,
                created_at=created_at,
                updated_at=created_at,
                completed_at=completed_at,
                config=self._serialize_experiment_config(experiment.config),
                summary=self._serialize_experiment_summary(experiment),
                task_id=None,
                output_files=[],
                algorithms=algorithms,
            )

        except Exception as e:
            logger.error(f"获取实验详情失败: {e}")
            raise

    def list_experiments(
        self,
        page: int = 1,
        per_page: int = 20,
        status: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> dict:
        """分页列出所有实验。"""
        try:
            experiments = self.experiment_storage.list_experiments()
            # 记录数量与当前根
            logger.info(
                f"list_experiments(service): found={len(experiments)} root={getattr(self.experiment_storage._storage, 'root_dir', None)}"
            )

            # 状态过滤
            if status:
                filtered_experiments = []
                for exp in experiments:
                    exp_status = self._determine_experiment_status(exp.experiment_id)
                    if exp_status.value == status:
                        filtered_experiments.append(exp)
                experiments = filtered_experiments

            # 排序
            if sort_by == "created_at":
                experiments.sort(
                    key=lambda x: x.timestamp, reverse=(sort_order == "desc")
                )
            elif sort_by == "name":
                experiments.sort(
                    key=lambda x: x.config.name, reverse=(sort_order == "desc")
                )
            elif sort_by == "status":
                experiments.sort(
                    key=lambda x: self._determine_experiment_status(
                        x.experiment_id
                    ).value,
                    reverse=(sort_order == "desc"),
                )

            # 计算分页
            total = len(experiments)
            start = (page - 1) * per_page
            end = start + per_page
            paginated_experiments = experiments[start:end]

            # 构建响应
            experiment_responses = [
                ExperimentResponse(
                    experiment_id=exp.experiment_id,
                    name=exp.config.name,
                    description=None,
                    status=self._determine_experiment_status(exp.experiment_id),
                    created_at=datetime.fromisoformat(exp.timestamp),
                    updated_at=datetime.fromisoformat(exp.timestamp),
                    completed_at=self._get_experiment_completion_time(
                        exp.experiment_id
                    ),
                    config=self._serialize_experiment_config(exp.config),
                    summary=self._serialize_experiment_summary(exp),
                    task_id=None,
                    output_files=[],
                    algorithms=(
                        [
                            r.algorithm_key
                            for r in self.experiment_storage.get_all_algorithm_results(
                                exp.experiment_id
                            )
                        ]
                        if self.experiment_storage.get_all_algorithm_results(
                            exp.experiment_id
                        )
                        else (
                            exp.algorithms_tested
                            if hasattr(exp, "algorithms_tested")
                            else []
                        )
                    ),
                )
                for exp in paginated_experiments
            ]

            # 分页信息（统一为 PaginationInfo 契约）
            pagination = {
                "page": page,
                "limit": per_page,
                "total": total,
                "total_pages": (total + per_page - 1) // per_page,
                "has_previous": page > 1,
                "has_next": end < total,
            }

            return {"experiments": experiment_responses, "pagination": pagination}

        except Exception as e:
            logger.error(f"获取实验列表失败: {e}")
            raise

    def _determine_experiment_status(self, experiment_id: str) -> TaskStatus:
        """确定实验的真实状态"""
        try:
            from src.api.services.task import task_service

            # 检查是否有相关的活跃任务
            active_tasks = task_service.get_active_tasks()
            for task in active_tasks:
                if task.experiment_id == experiment_id:
                    return task.status

            # 检查实验是否有完整的结果数据
            experiment = self.experiment_storage.get_experiment(experiment_id)
            if experiment:
                # 检查实验摘要中的成功/失败统计
                if hasattr(experiment, "successful_runs") and hasattr(experiment, "failed_runs"):
                    if experiment.successful_runs > 0 and experiment.failed_runs == 0:
                        return TaskStatus.COMPLETED
                    elif experiment.failed_runs > 0:
                        return TaskStatus.FAILED

                # 备用方案：检查是否有任何算法结果
                try:
                    all_results = self.experiment_storage.get_all_algorithm_results(experiment_id)
                    if all_results and len(all_results) > 0:
                        return TaskStatus.COMPLETED
                    else:
                        return TaskStatus.FAILED
                except Exception:
                    # 如果无法获取结果，检查是否有算法测试记录
                    if hasattr(experiment, "algorithms_tested") and experiment.algorithms_tested:
                        return TaskStatus.COMPLETED
                    else:
                        return TaskStatus.FAILED

            # 默认状态
            return TaskStatus.COMPLETED

        except Exception as e:
            logger.warning(f"确定实验状态失败 {experiment_id}: {e}")
            return TaskStatus.COMPLETED

    def _get_experiment_completion_time(self, experiment_id: str) -> Optional[datetime]:
        """获取实验完成时间"""
        try:
            from src.api.services.task import task_service

            # 查找相关的已完成任务
            all_tasks = task_service.list_tasks()
            for task in all_tasks:
                if (
                    task.experiment_id == experiment_id
                    and task.status
                    in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]
                    and task.completed_at
                ):
                    return task.completed_at

            # 如果没有找到任务，使用实验的时间戳
            experiment = self.experiment_storage.get_experiment(experiment_id)
            if experiment:
                return datetime.fromisoformat(experiment.timestamp)

            return None

        except Exception as e:
            logger.warning(f"获取实验完成时间失败 {experiment_id}: {e}")
            return None

    def delete_experiment(self, experiment_id: str) -> None:
        """删除实验及其所有相关数据。"""
        try:
            # 验证实验是否存在
            experiment = self.experiment_storage.get_experiment(experiment_id)
            if experiment is None:
                raise ExperimentNotFoundError(f"实验未找到: {experiment_id}")

            # 1) 删除存储中的实验数据
            deleted = self.experiment_storage.delete_experiment(experiment_id)
            logger.info(f"删除实验存储数据: {experiment_id}, deleted={deleted}")

            # 2) 清理输出目录（若存在）
            try:
                output_dir = (
                    experiment.config.output_dir
                    if hasattr(experiment, "config")
                    else None
                )
                if output_dir:
                    from shutil import rmtree

                    out_path = Path(output_dir)
                    if out_path.exists():
                        rmtree(out_path, ignore_errors=True)
                        logger.info(f"已清理输出目录: {out_path}")
            except Exception as _cleanup_err:
                logger.warning(f"清理输出目录失败（不阻塞删除流程）: {_cleanup_err}")

            # 3) 推送删除事件（可选）
            try:
                event_bus.publish(
                    {
                        "type": "experiment_deleted",
                        "data": {
                            "experiment_id": experiment_id,
                            "name": experiment.config.name,
                        },
                    }
                )
            except Exception:
                pass

        except Exception as e:
            logger.error(f"删除实验失败: {e}")
            raise

    def _convert_request_to_config(
        self, request: CreateExperimentRequest
    ) -> ExperimentConfig:
        """将API请求转换为内部配置"""
        try:
            feature_types = [FeatureType(ft) for ft in request.feature_types]
            ransac_types = [RANSACType(rt) for rt in request.ransac_types]

            # 先做空值校验，避免 Optional[str] 直接传入 Path
            if request.dataset_path is None or request.output_dir is None:
                raise ValidationError("dataset_path 与 output_dir 不能为空")

            return ExperimentConfig(
                name=request.name,
                dataset_path=Path(request.dataset_path),
                output_dir=Path(request.output_dir),
                feature_types=feature_types,
                ransac_types=ransac_types,
                sequences=request.sequences,
                num_runs=request.num_runs,
                parallel_jobs=request.parallel_jobs,
                random_seed=request.random_seed,
                save_frame_data=request.save_frame_data,
                save_descriptors=request.save_descriptors,
                compute_pr_curves=request.compute_pr_curves,
                analyze_ransac=request.analyze_ransac,
                ransac_success_threshold=request.ransac_success_threshold,
                max_features=request.max_features,
                feature_params=request.feature_params,
                ransac_threshold=request.ransac_threshold,
                ransac_confidence=request.ransac_confidence,
                ransac_max_iters=request.ransac_max_iters,
            )
        except Exception as e:
            raise ValidationError(f"配置转换失败: {str(e)}")

    def _serialize_experiment_config(self, config: ExperimentConfig):
        """序列化实验配置为响应模型"""
        from src.api.schemas.response import ExperimentConfigResponse

        return ExperimentConfigResponse(
            name=config.name,
            dataset_path=str(config.dataset_path),
            output_dir=str(config.output_dir),
            feature_types=[ft.value for ft in config.feature_types],
            ransac_types=[rt.value for rt in config.ransac_types],
            sequences=list(config.sequences),
            num_runs=config.num_runs,
            parallel_jobs=config.parallel_jobs,
            feature_params=config.feature_params,
            ransac_params={
                "threshold": config.ransac_threshold,
                "confidence": config.ransac_confidence,
                "max_iters": config.ransac_max_iters,
            },
        )

    def _serialize_experiment_summary(self, summary: ExperimentSummary):
        """序列化实验摘要为响应模型"""
        from src.api.schemas.response import ExperimentSummaryResponse

        return ExperimentSummaryResponse(
            total_runs=summary.total_runs,
            successful_runs=summary.successful_runs,
            failed_runs=summary.failed_runs,
            total_frames=0,
            total_processing_time=0.0,
            average_fps=0.0,
            algorithms_tested=list(summary.algorithms_tested),
            sequences_processed=list(summary.sequences_processed),
            best_algorithm=None,
            worst_algorithm=None,
        )



    def get_experiment_history(self, experiment_id: str, hours: int = 24) -> List[dict]:
        """
        获取实验历史状态

        Args:
            experiment_id: 实验ID
            hours: 时间范围（小时）

        Returns:
            List[dict]: 历史状态列表

        Raises:
            ExperimentNotFoundError: 实验不存在
        """
        try:
            # 验证实验是否存在
            experiment = self.experiment_storage.get_experiment(experiment_id)
            if not experiment:
                raise ExperimentNotFoundError(f"实验 {experiment_id} 不存在")

            # 获取任务状态历史
            from src.api.services.task import task_service

            task_history = task_service.get_task_history(experiment_id, hours)

            # 转换为实验状态格式
            history_data = []
            for task_status in task_history:
                # 构建实验状态数据
                experiment_status = {
                    "experiment_id": experiment_id,
                    "name": experiment.config.name,
                    "status": task_status.get("status", "unknown"),
                    "overall_progress": task_status.get("progress", 0),
                    "tasks": task_status.get("tasks", []),
                    "system_metrics": task_status.get("system_metrics", {}),
                    "statistics": {
                        "total_tasks": task_status.get("total_tasks", 0),
                        "completed_tasks": task_status.get("completed_tasks", 0),
                        "failed_tasks": task_status.get("failed_tasks", 0),
                        "average_processing_speed": task_status.get(
                            "average_processing_speed", 0
                        ),
                        "total_processing_time": task_status.get(
                            "total_processing_time", 0
                        ),
                    },
                    "created_at": (
                        experiment.created_at.isoformat()
                        if hasattr(experiment, "created_at")
                        else datetime.now().isoformat()
                    ),
                    "started_at": task_status.get("started_at"),
                    "estimated_completion": task_status.get("estimated_completion"),
                    "timestamp": task_status.get(
                        "timestamp", datetime.now().isoformat()
                    ),
                }
                history_data.append(experiment_status)

            # 如果没有历史数据，返回当前状态
            if not history_data:
                logger.info(f"实验 {experiment_id} 没有历史数据，返回当前状态")
                current_status = self._get_current_experiment_status(
                    experiment_id, experiment
                )
                history_data = [current_status]

            return history_data

        except ExperimentNotFoundError:
            raise
        except Exception as e:
            logger.error(f"获取实验历史失败: {e}")
            # 降级方案：返回当前状态
            try:
                experiment = self.experiment_storage.get_experiment(experiment_id)
                if experiment:
                    current_status = self._get_current_experiment_status(
                        experiment_id, experiment
                    )
                    return [current_status]
            except Exception as fallback_error:
                logger.error(f"降级方案也失败: {fallback_error}")

            raise Exception(f"无法获取实验历史数据: {e}")

    def _get_current_experiment_status(self, experiment_id: str, experiment) -> dict:
        """获取当前实验状态"""
        from src.api.services.task import task_service

        try:
            # 尝试获取当前任务状态
            # 兼容：TaskService 可能无 get_task_status；退化为扫描列表
            status = "created"
            progress = 0
            try:
                if hasattr(task_service, "get_task_status"):
                    current_task = task_service.get_task_status(experiment_id)  # type: ignore
                    status = current_task.get("status", "unknown")
                    progress = current_task.get("progress", 0)
                else:
                    tasks = task_service.list_tasks()
                    for t in tasks:
                        if getattr(t, "experiment_id", None) == experiment_id:
                            status = (
                                t.status.value
                                if hasattr(t.status, "value")
                                else str(t.status)
                            )
                            progress = getattr(t, "progress", 0)
                            break
            except Exception:
                status = "created"
                progress = 0
        except Exception:
            # 如果无法获取任务状态，使用默认值
            status = "created"
            progress = 0

        return {
            "experiment_id": experiment_id,
            "name": experiment.config.name,
            "status": status,
            "overall_progress": progress,
            "tasks": [],
            "system_metrics": {},
            "statistics": {
                "total_tasks": 0,
                "completed_tasks": 0,
                "failed_tasks": 0,
                "average_processing_speed": 0,
                "total_processing_time": 0,
            },
            "created_at": (
                experiment.created_at.isoformat()
                if hasattr(experiment, "created_at")
                else datetime.now().isoformat()
            ),
            "started_at": None,
            "estimated_completion": None,
            "timestamp": datetime.now().isoformat(),
        }


# 全局单例实例
experiment_service = ExperimentService()
