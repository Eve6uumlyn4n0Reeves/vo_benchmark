#
# 功能: 提供结果查询的业务逻辑服务。
#
from typing import Dict, Any, IO, List
import json
import csv
import io
from pathlib import Path
from src.api.schemas.response import (
    AlgorithmResultResponse,
    FrameResultsResponse,
    AlgorithmMetricsResponse,
)
from src.storage.experiment import ExperimentStorage
from src.storage.filesystem import FileSystemStorage
from src.api.exceptions.base import ExperimentNotFoundError
from src.models.evaluation import PRCurveData
from src.models.frame import FrameResult
from src.api.serializers import UnifiedSerializer
import logging
import threading
import time

logger = logging.getLogger(__name__)


class ResultService:
    """结果查询服务（单例模式）"""

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
        """初始化结果服务（单例模式）"""
        if self._initialized:
            return

        # 使用文件系统存储作为默认存储（统一到配置的 RESULTS_ROOT/experiments）
        def _has_any_experiments(root: Path) -> bool:
            exp_dir = (root / "experiments") if root.name != "experiments" else root
            patterns = [
                "**/summary.json",
                "**/summary.json.gz",
                "**/summary.pkl",
                "**/summary.pkl.gz",
            ]
            for pat in patterns:
                if any(exp_dir.glob(pat)):
                    return True
            return False

        try:
            from src.config.manager import get_config

            cfg_results_root = get_config().storage.results_root
        except Exception:
            cfg_results_root = None

        # 与 ExperimentService 完全一致：优先使用统一配置；否则使用 ./results。
        chosen_base = (
            Path(cfg_results_root).resolve()
            if cfg_results_root
            else Path("./results").resolve()
        )
        chosen_base.mkdir(parents=True, exist_ok=True)

        experiments_root = (chosen_base / "experiments").resolve()
        experiments_root.mkdir(parents=True, exist_ok=True)
        # 存储根指向 base
        storage = FileSystemStorage(str(chosen_base))
        self.experiment_storage = ExperimentStorage(storage)

        # 记录所选结果根路径，便于排障
        try:
            logger.info(
                f"ResultService initialized with base={str(chosen_base)} experiments_root={str(experiments_root)}"
            )
        except Exception:
            pass

        # 添加内存缓存
        self._frame_cache = {}  # {experiment_id/algorithm_key: (frames, timestamp)}
        self._pr_cache = {}     # {experiment_id/algorithm_key: (data, timestamp)}
        self._trajectory_cache = {}  # {experiment_id/algorithm_key/include_ref: (data, timestamp)}
        self._cache_ttl = 300   # 5分钟缓存

        # 添加内存缓存
        self._frame_cache = {}  # {experiment_id/algorithm_key: (frames, timestamp)}
        self._pr_cache = {}     # {experiment_id/algorithm_key: (data, timestamp)}
        self._trajectory_cache = {}  # {experiment_id/algorithm_key: (data, timestamp)}
        self._cache_ttl = 300   # 5分钟缓存

        self._initialized = True

    def get_results_overview(self, experiment_id: str) -> Dict[str, Any]:
        """聚合返回某实验的概览信息。
        返回结构：
        {
          "algorithms": [str, ...],
          "summary_per_algorithm": {
             alg_key: {
               "success_rate": float,
               "fps": float,
               "matching": {"avg_inlier_ratio": float},
               "trajectory": {"ate_rmse": float, "rpe_rmse": float} | None
             }
          }
        }
        """
        # 验证实验
        experiment = self.experiment_storage.get_experiment(experiment_id)
        if experiment is None:
            raise ExperimentNotFoundError(f"实验未找到: {experiment_id}")

        # 获取算法列表：优先摘要，其次从存储扫描
        algorithms: List[str] = []
        try:
            if (
                hasattr(experiment, "algorithms_tested")
                and experiment.algorithms_tested
            ):
                algorithms = list(experiment.algorithms_tested)
            else:
                all_results = self.experiment_storage.get_all_algorithm_results(
                    experiment_id
                )
                algorithms = (
                    [r.algorithm_key for r in all_results] if all_results else []
                )
        except Exception:
            algorithms = []

        summary_per_algorithm: Dict[str, Any] = {}
        if algorithms:
            for alg in algorithms:
                try:
                    metrics = self.experiment_storage.get_algorithm_result(
                        experiment_id, alg
                    )
                    if not metrics:
                        continue
                    m = self.experiment_storage._serialize_algorithm_metrics(metrics)
                    traj = m.get("trajectory") or None

                    def _num(x, default=0.0):
                        try:
                            return float(x) if x is not None else float(default)
                        except Exception:
                            return float(default)

                    summary_per_algorithm[alg] = {
                        "success_rate": _num(m.get("success_rate"), 0.0),
                        "fps": _num(m.get("fps"), 0.0),
                        "avg_frame_time_ms": _num(m.get("avg_frame_time_ms"), 0.0),
                        "total_time_s": _num(m.get("total_time_s"), 0.0),
                        "total_frames": int(m.get("total_frames") or 0),
                        "successful_frames": int(m.get("successful_frames") or 0),
                        "failed_frames": int(m.get("failed_frames") or 0),
                        "failure_reasons": (m.get("failure_reasons") or {}),
                        "matching": {
                            "avg_inlier_ratio": _num((m.get("matching") or {}).get(
                                "avg_inlier_ratio", 0.0
                            ), 0.0)
                        },
                        "trajectory": (
                            None
                            if not traj
                            else {
                                "ate_rmse": _num(traj.get("ate_rmse"), 0.0),
                                "rpe_rmse": _num(traj.get("rpe_rmse"), 0.0),
                            }
                        ),
                    }
                except Exception as e:
                    logger.warning(f"聚合算法摘要失败 {experiment_id}/{alg}: {e}")
                    continue

        # 若摘要中算法列表为空且我们扫描到了，写回缓存
        try:
            if (
                hasattr(experiment, "algorithms_tested")
                and not experiment.algorithms_tested
                and algorithms
            ):
                from src.models.experiment import ExperimentSummary

                updated = ExperimentSummary(
                    experiment_id=experiment.experiment_id,
                    timestamp=experiment.timestamp,
                    config=experiment.config,
                    total_runs=experiment.total_runs,
                    successful_runs=experiment.successful_runs,
                    failed_runs=experiment.failed_runs,
                    algorithms_tested=algorithms,
                    sequences_processed=getattr(experiment, "sequences_processed", []),
                )
                self.experiment_storage.save_experiment(experiment_id, updated)
        except Exception as e:
            logger.warning(f"写回实验摘要失败（忽略）：{e}")

        return {
            "algorithms": algorithms,
            "summary_per_algorithm": summary_per_algorithm,
        }

    def diagnose_experiment(self, experiment_id: str) -> Dict[str, Any]:
        """诊断指定实验的存储结构与可见结果。"""
        # 基本信息
        root_dir = getattr(self.experiment_storage._storage, "root_dir", None)

        experiment = self.experiment_storage.get_experiment(experiment_id)
        if experiment is None:
            raise ExperimentNotFoundError(f"实验未找到: {experiment_id}")

        # 列出可见键
        try:
            prefix = f"experiments/{experiment_id}"
            keys = self.experiment_storage._storage.list_keys(prefix)
        except Exception:
            keys = []

        # 解析算法
        algorithms: List[str] = []
        try:
            algorithms = (
                experiment.algorithms_tested
                if hasattr(experiment, "algorithms_tested")
                else []
            )
            if not algorithms:
                all_results = self.experiment_storage.get_all_algorithm_results(
                    experiment_id
                )
                algorithms = (
                    [r.algorithm_key for r in all_results] if all_results else []
                )
        except Exception:
            algorithms = []

        per_algorithm: Dict[str, Any] = {}
        for alg in algorithms:
            metrics_key = f"experiments/{experiment_id}/algorithms/{alg}"
            frames_key = f"experiments/{experiment_id}/frames/{alg}"
            metrics_exists = False
            frames_exists = False
            try:
                metrics_exists = self.experiment_storage._storage.exists(metrics_key)
            except Exception:
                metrics_exists = False
            try:
                frames_exists = self.experiment_storage._storage.exists(frames_key)
            except Exception:
                frames_exists = False
            per_algorithm[alg] = {
                "metrics_exists": metrics_exists,
                "frames_exists": frames_exists,
            }

        return {
            "storage_root": str(root_dir) if root_dir else None,
            "visible_keys": keys,
            "algorithms": algorithms,
            "per_algorithm": per_algorithm,
        }

    def get_algorithm_result(
        self, experiment_id: str, algorithm_key: str
    ) -> AlgorithmResultResponse:
        """获取算法结果"""
        try:
            # 验证实验是否存在
            experiment = self.experiment_storage.get_experiment(experiment_id)
            if experiment is None:
                raise ExperimentNotFoundError(f"实验未找到: {experiment_id}")

            # 获取算法结果
            algorithm_result = self.experiment_storage.get_algorithm_result(
                experiment_id, algorithm_key
            )
            if algorithm_result is None:
                raise ExperimentNotFoundError(f"算法结果未找到: {algorithm_key}")

            # 转换为响应格式（使用统一序列化器）
            serialized_metrics = UnifiedSerializer.serialize_algorithm_metrics(
                algorithm_result
            )

            return AlgorithmResultResponse(
                algorithm_key=algorithm_result.algorithm_key,
                feature_type=algorithm_result.feature_type,
                ransac_type=algorithm_result.ransac_type,
                sequence=(
                    algorithm_key.split("_")[-1] if "_" in algorithm_key else "unknown"
                ),
                metrics=AlgorithmMetricsResponse(**serialized_metrics),
                pr_curve=None,  # PR曲线数据通过单独接口获取
            )

        except Exception as e:
            logger.error(f"获取算法结果失败: {e}")
            raise

    def get_frame_results(
        self, experiment_id: str, algorithm_key: str, start: int, limit: int
    ) -> FrameResultsResponse:
        """获取帧级别结果"""
        try:
            # 验证实验是否存在
            experiment = self.experiment_storage.get_experiment(experiment_id)
            if experiment is None:
                raise ExperimentNotFoundError(f"实验未找到: {experiment_id}")

            # 检查内存缓存（仅对第一页进行缓存，避免内存过大）
            cache_key = f"{experiment_id}/{algorithm_key}"
            if start == 0 and cache_key in self._frame_cache:
                cached_frames, timestamp = self._frame_cache[cache_key]
                if time.time() - timestamp < self._cache_ttl:
                    # 使用缓存数据
                    page_frames = cached_frames[:limit]
                    total_cached = len(cached_frames)
                    logger.info(f"使用缓存帧结果: {experiment_id}/{algorithm_key}")

                    # 构建分页信息
                    from math import ceil
                    from src.api.schemas.response import PaginationInfo

                    total_pages = ceil(total_cached / limit) if limit > 0 else 0
                    page = (start // limit) + 1 if limit > 0 else 1

                    pagination = PaginationInfo(
                        page=page,
                        limit=limit,
                        total=total_cached,
                        total_pages=total_pages,
                        has_next=page < total_pages,
                        has_previous=page > 1,
                    )

                    frames_serialized = [
                        UnifiedSerializer.serialize_frame_result_summary(frame) for frame in page_frames
                    ]

                    # 与非缓存路径保持一致的 sequence 推断
                    seq = (
                        algorithm_key.split("_")[-1] if "_" in algorithm_key else "unknown"
                    )
                    return FrameResultsResponse(
                        experiment_id=experiment_id,
                        algorithm_key=algorithm_key,
                        frames=frames_serialized,
                        pagination=pagination,
                        sequence=seq,
                        summary={"total_frames": total_cached, "algorithm": algorithm_key}
                    )

            # 获取帧结果
            frame_results, total = self.experiment_storage.get_frame_results(
                experiment_id, algorithm_key, start, limit
            )

            # 缓存第一页结果
            if start == 0 and frame_results:
                self._frame_cache[cache_key] = (frame_results, time.time())
                logger.info(f"缓存帧结果: {experiment_id}/{algorithm_key}, {len(frame_results)} 帧")

            # 转换为响应格式：修正分页字段并补充 sequence 与 summary
            from math import ceil
            from src.api.schemas.response import PaginationInfo

            total_pages = ceil(total / limit) if limit > 0 else 0
            page = (start // limit) + 1 if limit > 0 else 1

            pagination = PaginationInfo(
                page=page,
                limit=limit,
                total=total,
                total_pages=total_pages,
                has_next=page < total_pages,
                has_previous=page > 1,
            )

            frames_serialized = [
                UnifiedSerializer.serialize_frame_result_summary(frame) for frame in frame_results
            ]

            # 构建摘要信息
            if len(frame_results) > 0:
                avg_matches: float = sum(
                    float(getattr(f, "num_matches", 0)) for f in frame_results
                ) / float(len(frame_results))
                avg_inliers = sum(
                    getattr(f, "num_inliers", 0) for f in frame_results
                ) / len(frame_results)
                avg_inlier_ratio = sum(
                    getattr(f, "inlier_ratio", 0.0) for f in frame_results
                ) / len(frame_results)
            else:
                avg_matches = 0.0
                avg_inliers = 0.0
                avg_inlier_ratio = 0.0
            # 将帧序列化结果转为模型实例，mypy 友好
            from src.api.schemas.response import FrameResultResponse

            summary = {
                "avg_matches": float(avg_matches),
                "avg_inliers": float(avg_inliers),
                "avg_inlier_ratio": float(avg_inlier_ratio),
                "total_frames": int(total),
            }

            return FrameResultsResponse(
                experiment_id=experiment_id,
                algorithm_key=algorithm_key,
                sequence=(
                    algorithm_key.split("_")[-1] if "_" in algorithm_key else "unknown"
                ),
                frames=[FrameResultResponse(**f) if isinstance(f, dict) else f for f in frames_serialized],
                pagination=pagination,
                summary=summary,
            )

        except Exception as e:
            logger.error(f"获取帧结果失败: {e}")
            raise

    def get_pr_curve(self, experiment_id: str, algorithm_key: str) -> Dict[str, Any]:
        """获取PR曲线数据（带内存缓存与预计算优先）"""
        try:
            cache_key = f"{experiment_id}/{algorithm_key}"
            # 0. 内存缓存命中
            if cache_key in self._pr_cache:
                data, ts = self._pr_cache[cache_key]
                if time.time() - ts < self._cache_ttl:
                    logger.info(f"使用内存缓存PR曲线: {experiment_id}/{algorithm_key}")
                    return data

            # 1. 优先读取预计算结果
            precomputed = self.experiment_storage.get_pr_curve(experiment_id, algorithm_key)
            if precomputed:
                logger.info(f"使用预计算PR曲线: {experiment_id}/{algorithm_key}")
                processed = self._postprocess_pr_curve(precomputed)
                self._pr_cache[cache_key] = (processed, time.time())
                return processed


            # --- Helper: postprocess PR curve (monotonize precision, optional resample) ---



            # 2. 如果没有预计算结果，现算（向后兼容）
            logger.info(f"预计算PR曲线不存在，开始现算: {experiment_id}/{algorithm_key}")

            # 验证实验是否存在
            experiment = self.experiment_storage.get_experiment(experiment_id)
            if experiment is None:
                raise ExperimentNotFoundError(f"实验未找到: {experiment_id}")

            # 获取算法结果
            algorithm_result = self.experiment_storage.get_algorithm_result(
                experiment_id, algorithm_key
            )
            if algorithm_result is None:
                raise ExperimentNotFoundError(f"算法结果未找到: {algorithm_key}")

            # 限制帧结果数量以提高性能，使用采样策略
            max_frames = 1000  # 限制最大帧数
            frame_results, total = self.experiment_storage.get_frame_results(
                experiment_id, algorithm_key, 0, max_frames
            )

            logger.info(f"获取到 {len(frame_results)} 个帧结果，总数: {total}")

            if not frame_results:
                logger.warning(f"未找到帧结果数据: {experiment_id}/{algorithm_key}")
                return self._create_empty_pr_curve(algorithm_key)

            # 如果数据量太大，进行采样
            if len(frame_results) > 500:
                import random

                random.seed(42)  # 确保结果可重现
                frame_results = random.sample(frame_results, 500)
                logger.info(f"数据采样：从 {len(frame_results)} 个帧结果中采样 500 个")

            # 使用真实数据计算PR曲线
            pr_curve_data = self._calculate_pr_curve_from_frames(
                algorithm_key, frame_results
            )

            logger.info(f"PR曲线计算完成: {experiment_id}/{algorithm_key}")

            result_obj = {
                "algorithm": pr_curve_data["algorithm"],
                "precisions": pr_curve_data["precisions"],
                "recalls": pr_curve_data["recalls"],
                "thresholds": pr_curve_data["thresholds"],
                "auc_score": pr_curve_data["auc_score"],
                "optimal_threshold": pr_curve_data["optimal_threshold"],
                "optimal_precision": pr_curve_data["optimal_precision"],
                "optimal_recall": pr_curve_data["optimal_recall"],
                "f1_scores": pr_curve_data["f1_scores"],
                "max_f1_score": pr_curve_data["max_f1_score"],
            }

            # 3. 结果写入内存缓存与落盘（最佳努力）
            try:
                self._pr_cache[cache_key] = (result_obj, time.time())
                # 落盘以便二次访问命中
                self.experiment_storage.save_pr_curve(experiment_id, algorithm_key, result_obj)
            except Exception as e:
                logger.warning(f"PR曲线结果缓存/落盘失败（忽略）: {e}")

            return result_obj

        except Exception as e:
            logger.error(f"获取PR曲线失败: {e}", exc_info=True)
            # 返回空的PR曲线而不是抛出异常，避免前端崩溃
            return self._create_empty_pr_curve(algorithm_key)

    def get_trajectory_data(
        self, experiment_id: str, algorithm_key: str, include_reference: bool = False
    ) -> Dict[str, Any]:
        """获取轨迹数据（内存缓存 + 预计算优先 + 统一结构）
        :param include_reference: 当无GT时，是否生成参考直线groundtruth（默认否）
        """
        try:
            cache_key = f"{experiment_id}/{algorithm_key}/{int(include_reference)}"
            # 0. 内存缓存命中
            if cache_key in self._trajectory_cache:
                data, ts = self._trajectory_cache[cache_key]
                if time.time() - ts < self._cache_ttl:
                    logger.info(f"使用内存缓存轨迹数据: {experiment_id}/{algorithm_key}")
                    return data

            # 1. 优先读取预计算结果（基础轨迹，不区分include_reference）
            precomputed = self.experiment_storage.get_trajectory(experiment_id, algorithm_key)
            if precomputed:
                logger.info(f"使用预计算轨迹数据: {experiment_id}/{algorithm_key}")
                # 如果需要参考轨迹但预计算没有，可以动态添加
                if include_reference and 'reference_trajectory' not in precomputed:
                    precomputed = self._add_reference_trajectory(precomputed, experiment_id)
                self._trajectory_cache[cache_key] = (precomputed, time.time())
                return precomputed

            # 2. 如果没有预计算结果，现算（向后兼容）
            logger.info(
                f"预计算轨迹不存在，开始现算: {experiment_id}/{algorithm_key}, include_reference={include_reference}"
            )

            # 验证实验是否存在
            experiment = self.experiment_storage.get_experiment(experiment_id)
            if experiment is None:
                raise ExperimentNotFoundError(f"实验未找到: {experiment_id}")

            # 获取算法结果
            algorithm_result = self.experiment_storage.get_algorithm_result(
                experiment_id, algorithm_key
            )
            if algorithm_result is None:
                raise ExperimentNotFoundError(f"算法结果未找到: {algorithm_key}")

            # 限制帧结果数量以提高性能
            max_frames = 500  # 限制轨迹点数量
            frame_results, total = self.experiment_storage.get_frame_results(
                experiment_id, algorithm_key, 0, max_frames
            )

            logger.info(f"获取到 {len(frame_results)} 个帧结果用于轨迹构建")

            if not frame_results:
                logger.warning(f"未找到帧结果数据: {experiment_id}/{algorithm_key}")
                return self._create_empty_trajectory_data(experiment_id, algorithm_key)

            # 从帧结果构建轨迹数据（包含统计字段对齐与ATE计算）
            trajectory = self._build_trajectory_from_frames(
                experiment_id,
                algorithm_key,
                frame_results,
                experiment.config,
                False,  # 预计算/落盘仅保存基础轨迹，不包含reference
            )

            # 补充元数据（对齐与采样信息）
            try:
                trajectory.setdefault("metadata", {})
                trajectory["metadata"].update({
                    "alignment": "index",
                    "source_total_frames": int(total),
                    "used_frames": int(len(frame_results)),
                    "max_frames": int(max_frames),
                    "downsampled": bool(total > max_frames),
                })
            except Exception:
                pass

            # 3. 结果写入内存缓存与落盘（最佳努力）
            try:
                # 落盘基础轨迹，便于二次访问命中
                self.experiment_storage.save_trajectory(experiment_id, algorithm_key, trajectory)
            except Exception as e:
                logger.warning(f"轨迹结果落盘失败（忽略）: {e}")

            # 根据 include_reference 需要动态添加参考轨迹
            if include_reference:
                trajectory = self._add_reference_trajectory(trajectory, experiment_id)

            # 写入内存缓存
            self._trajectory_cache[cache_key] = (trajectory, time.time())
            return trajectory

        except Exception as e:
            logger.error(f"获取轨迹数据失败: {e}")
            raise

    def export_results(self, experiment_id: str, format: str) -> IO[bytes]:
        """导出实验结果"""
        try:
            # 验证实验是否存在
            experiment = self.experiment_storage.get_experiment(experiment_id)
            if experiment is None:
                raise ExperimentNotFoundError(f"实验未找到: {experiment_id}")

            # 获取所有算法结果
            all_algorithms = (
                experiment.algorithms_tested
                if hasattr(experiment, "algorithms_tested")
                else []
            )

            # 收集所有算法的结果数据
            export_data = {
                "experiment_info": {
                    "experiment_id": experiment_id,
                    "timestamp": experiment.timestamp,
                    "config": (
                        self.experiment_storage._serialize_experiment_config(
                            experiment.config
                        )
                        if hasattr(experiment, "config")
                        else {}
                    ),
                    "total_runs": (
                        experiment.total_runs
                        if hasattr(experiment, "total_runs")
                        else 0
                    ),
                    "successful_runs": (
                        experiment.successful_runs
                        if hasattr(experiment, "successful_runs")
                        else 0
                    ),
                    "failed_runs": (
                        experiment.failed_runs
                        if hasattr(experiment, "failed_runs")
                        else 0
                    ),
                },
                "algorithm_results": [],
            }

            # 为每个算法收集详细结果
            for algorithm_key in all_algorithms:
                try:
                    # 获取算法结果
                    algorithm_result = self.experiment_storage.get_algorithm_result(
                        experiment_id, algorithm_key
                    )
                    if algorithm_result:
                        # 获取帧结果
                        frame_results, _ = self.experiment_storage.get_frame_results(
                            experiment_id, algorithm_key, 0, 10000
                        )

                        algorithm_data = {
                            "algorithm_key": algorithm_key,
                            "metrics": UnifiedSerializer.serialize_algorithm_metrics(
                                algorithm_result
                            ),
                            "frame_count": len(frame_results),
                            "frame_results": [
                                UnifiedSerializer.serialize_frame_result_summary(frame)
                                for frame in frame_results[:100]
                            ],  # 限制帧数量
                        }
                        # 使用强类型列表，便于 mypy
                        from typing import cast, Dict, Any, List
                        algorithm_results_list = cast(List[Dict[str, Any]], export_data.setdefault("algorithm_results", []))
                        algorithm_results_list.append(algorithm_data)
                except Exception as e:
                    logger.warning(f"获取算法结果失败 {algorithm_key}: {e}")
                    continue

            # 类型窄化：确保 algorithm_results 是 list
            if not isinstance(export_data.get("algorithm_results"), list):
                export_data["algorithm_results"] = list(export_data.get("algorithm_results", []))

            if format == "json":

                return self._export_json(export_data)
            elif format == "csv":
                return self._export_csv(export_data)
            elif format == "xlsx":
                return self._export_xlsx(export_data)
            elif format == "pdf":
                return self._export_pdf(export_data)
            else:
                raise ValueError(f"不支持的导出格式: {format}")

        except Exception as e:
            logger.error(f"导出结果失败: {e}")
            raise

    def _calculate_pr_curve_from_frames(
        self, algorithm_key: str, frame_results: List
    ) -> Dict[str, Any]:
        """从帧结果计算PR曲线"""
        import numpy as np
        import time

        start_time = time.time()
        logger.info(f"开始处理 {len(frame_results)} 个帧结果")

        # 收集所有匹配数据和分数
        all_scores = []
        all_labels = []
        processed_frames = 0

        for i, frame in enumerate(frame_results):
            if i % 100 == 0 and i > 0:
                logger.debug(f"处理进度: {i}/{len(frame_results)}")

            # 检查必要的数据是否存在
            if not (
                frame.matches and frame.matches.scores and len(frame.matches.scores) > 0
                and frame.ransac and frame.ransac.inlier_mask
            ):
                continue

            # 确保匹配数量与inlier_mask长度一致
            if len(frame.matches.scores) != len(frame.ransac.inlier_mask):
                logger.warning(f"帧 {i}: 匹配数量({len(frame.matches.scores)})与inlier_mask长度({len(frame.ransac.inlier_mask)})不一致")
                continue

            # 使用匹配分数（距离越小越好，所以取负值）
            frame_scores = [-score for score in frame.matches.scores]

            # 使用真实的inlier_mask作为标签
            frame_labels = frame.ransac.inlier_mask.copy()

            # 限制每帧的匹配数量以控制内存使用
            if len(frame_scores) > 50:
                # 只取前50个最高分数的匹配
                top_indices = np.argsort(frame_scores)[-50:]
                frame_scores = [frame_scores[idx] for idx in top_indices]
                frame_labels = [frame_labels[idx] for idx in top_indices]

            all_scores.extend(frame_scores)
            all_labels.extend(frame_labels)
            processed_frames += 1

        processing_time = time.time() - start_time
        logger.info(
            f"帧结果处理完成: 处理了 {processed_frames} 个有效帧，"
            f"收集了 {len(all_scores)} 个匹配点，耗时 {processing_time:.2f}s"
        )

        if not all_scores:
            logger.warning(f"未找到匹配分数数据: {algorithm_key}")
            return self._create_empty_pr_curve(algorithm_key)

        # 如果数据点太多，进行采样以提高计算速度
        if len(all_scores) > 2000:
            import random

            random.seed(42)
            sampled_indices: List[int] = random.sample(range(len(all_scores)), 2000)
            all_scores = [all_scores[i] for i in sampled_indices]
            all_labels = [all_labels[i] for i in sampled_indices]
            logger.info(f"数据采样：从 {len(all_scores)} 个匹配点中采样 2000 个")

        # 内联PR曲线计算逻辑 + 统一后处理
        raw = self._compute_pr_curve_inline(algorithm_key, all_scores, all_labels)
        return self._postprocess_pr_curve(raw)

    def _compute_pr_curve_inline(
        self, algorithm_key: str, scores: List[float], labels: List[bool]
    ) -> Dict[str, Any]:
        """使用标准 scikit-learn PR 曲线算法"""
        import numpy as np
        import time
        from sklearn.metrics import precision_recall_curve, average_precision_score

        start_time = time.time()
        logger.info(f"开始计算PR曲线: {len(scores)} 个数据点")

        if len(scores) != len(labels):
            logger.error("分数和标签的长度必须相同")
            return self._create_empty_pr_curve(algorithm_key)

        if len(scores) == 0:
            logger.warning("输入数据为空，返回默认PR曲线")
            return self._create_empty_pr_curve(algorithm_key)

        try:
            # 转换为numpy数组
            scores_arr = np.asarray(scores, dtype=float)
            labels_arr = np.asarray(labels, dtype=int)

            # 使用 scikit-learn 标准 PR 曲线算法
            precisions, recalls, thresholds = precision_recall_curve(labels_arr, scores_arr)

            # 计算平均精确率 (AUC-PR)
            auc_score = average_precision_score(labels_arr, scores_arr)

            # 计算 F1 分数
            # 避免除零错误
            with np.errstate(divide='ignore', invalid='ignore'):
                f1_scores = 2 * (precisions * recalls) / (precisions + recalls)
                f1_scores = np.nan_to_num(f1_scores, nan=0.0)

            # 找到最优阈值（最大F1分数）
            if len(f1_scores) > 0:
                max_f1_idx = int(np.argmax(f1_scores))
                max_f1_score = float(f1_scores[max_f1_idx])
                optimal_precision = float(precisions[max_f1_idx])
                optimal_recall = float(recalls[max_f1_idx])

                # 获取对应的阈值
                if max_f1_idx < len(thresholds):
                    optimal_threshold = float(thresholds[max_f1_idx])
                else:
                    # 处理边界情况
                    optimal_threshold = float(np.min(scores_arr)) if len(thresholds) > 0 else 0.0
            else:
                max_f1_score = 0.0
                optimal_precision = 0.0
                optimal_recall = 0.0
                optimal_threshold = 0.0

            logger.info(f"PR曲线计算完成: AUC={auc_score:.3f}, 最优F1={max_f1_score:.3f}, 耗时={time.time()-start_time:.2f}s")

            return {
                "algorithm": algorithm_key,
                "precisions": precisions.tolist(),
                "recalls": recalls.tolist(),
                "thresholds": thresholds.tolist(),
                "auc_score": float(auc_score),
                "optimal_threshold": float(optimal_threshold),
                "optimal_precision": float(optimal_precision),
                "optimal_recall": float(optimal_recall),
                "f1_scores": f1_scores.tolist(),
                "max_f1_score": float(max_f1_score),
                "num_points": len(precisions),
                "computation_time": time.time() - start_time,
            }

        except Exception as e:
            logger.error(f"PR曲线计算失败: {e}")
            return self._create_empty_pr_curve(algorithm_key)



    def _build_trajectory_from_frames(
        self,
        experiment_id: str,
        algorithm_key: str,
        frame_results: List,
        config: Any,
        include_reference: bool = False,
    ) -> Dict[str, Any]:
        """从帧结果构建轨迹数据，返回结构与前端严格对齐
        - 无GT时不生成理想轨迹；仅当 include_reference=True 才生成参考直线
        - 在 metadata 中标记 has_groundtruth/reference_groundtruth
        """
        import numpy as np

        estimated_trajectory = []
        groundtruth_trajectory = []
        has_groundtruth = False

        # 累积位姿（仅使用真实的estimated_pose）
        current_position = np.array([0.0, 0.0, 0.0])
        last_valid_position = current_position.copy()

        for i, frame in enumerate(frame_results):
            timestamp = frame.timestamp if hasattr(frame, "timestamp") else i * 0.1
            position_updated = False

            # 仅使用真实的estimated_pose
            if hasattr(frame, "estimated_pose") and frame.estimated_pose is not None:
                pose = frame.estimated_pose
                try:
                    # 处理不同格式的位姿矩阵
                    if hasattr(pose, "shape") and pose.shape == (4, 4):
                        # numpy 数组格式
                        current_position = np.array(
                            [pose[0, 3], pose[1, 3], pose[2, 3]]
                        )
                        last_valid_position = current_position.copy()
                        position_updated = True
                    elif isinstance(pose, list) and len(pose) == 4 and all(isinstance(row, list) and len(row) == 4 for row in pose):
                        # 嵌套列表格式 [[row1], [row2], [row3], [row4]]
                        current_position = np.array(
                            [pose[0][3], pose[1][3], pose[2][3]]
                        )
                        last_valid_position = current_position.copy()
                        position_updated = True
                    elif isinstance(pose, list) and len(pose) == 16:
                        # 平坦列表格式 [a11, a12, a13, a14, a21, ...]
                        current_position = np.array(
                            [pose[3], pose[7], pose[11]]
                        )
                        last_valid_position = current_position.copy()
                        position_updated = True
                    elif hasattr(pose, "translation") and pose.translation is not None:
                        # 对象格式
                        current_position = np.array(
                            [pose.translation.x, pose.translation.y, pose.translation.z]
                        )
                        last_valid_position = current_position.copy()
                        position_updated = True
                except Exception as e:
                    logger.warning(f"解析位姿矩阵失败 (帧 {i}): {e}")
                    pass

            # 如果没有有效的位姿估计，有两种策略：
            # 1. 跳过该点（不添加到轨迹中）
            # 2. 使用上一个有效位置（插值策略）
            # 这里采用插值策略，保持轨迹的连续性
            if not position_updated:
                current_position = last_valid_position.copy()

            # 只有当有有效位姿时才添加轨迹点
            if position_updated or i == 0:  # 第一帧总是添加（即使位置为原点）
                estimated_trajectory.append(
                    {
                        "x": float(current_position[0]),
                        "y": float(current_position[1]),
                        "z": float(current_position[2]),
                        "timestamp": float(timestamp),
                        "frame_id": int(getattr(frame, "frame_id", i)),
                        "has_pose_estimate": position_updated,  # 标记是否有真实位姿估计
                    }
                )

            # 地面真值轨迹（如果有的话）
            if (
                hasattr(frame, "ground_truth_pose")
                and frame.ground_truth_pose is not None
            ):
                has_groundtruth = True
                gt_pose = frame.ground_truth_pose
                try:
                    gt_position = None

                    if hasattr(gt_pose, "shape") and gt_pose.shape == (4, 4):
                        # numpy 数组格式
                        gt_position = [float(gt_pose[0, 3]), float(gt_pose[1, 3]), float(gt_pose[2, 3])]
                    elif isinstance(gt_pose, list) and len(gt_pose) == 4 and all(isinstance(row, list) and len(row) == 4 for row in gt_pose):
                        # 嵌套列表格式 [[row1], [row2], [row3], [row4]]
                        gt_position = [float(gt_pose[0][3]), float(gt_pose[1][3]), float(gt_pose[2][3])]
                    elif isinstance(gt_pose, list) and len(gt_pose) == 16:
                        # 平坦列表格式 [a11, a12, a13, a14, a21, ...]
                        gt_position = [float(gt_pose[3]), float(gt_pose[7]), float(gt_pose[11])]
                    elif hasattr(gt_pose, "translation") and gt_pose.translation is not None:
                        # 对象格式
                        gt_position = [float(gt_pose.translation.x), float(gt_pose.translation.y), float(gt_pose.translation.z)]

                    if gt_position is not None:
                        groundtruth_trajectory.append(
                            {
                                "x": gt_position[0],
                                "y": gt_position[1],
                                "z": gt_position[2],
                                "timestamp": float(timestamp),
                                "frame_id": int(getattr(frame, "frame_id", i)),
                            }
                        )
                except Exception as e:
                    logger.warning(f"解析真实位姿矩阵失败 (帧 {i}): {e}")
                    pass
            # 若无GT且允许参考，生成参考直线
            elif include_reference:
                ideal_position = np.array([i * 0.1, 0.0, 0.0])
                groundtruth_trajectory.append(
                    {
                        "x": float(ideal_position[0]),
                        "y": float(ideal_position[1]),
                        "z": float(ideal_position[2]),
                        "timestamp": float(timestamp),
                        "frame_id": int(getattr(frame, "frame_id", i)),
                    }
                )

        # 计算轨迹统计信息
        def path_length(path):
            if len(path) < 2:
                return 0.0
            total = 0.0
            for i in range(1, len(path)):
                dx = path[i]["x"] - path[i - 1]["x"]
                dy = path[i]["y"] - path[i - 1]["y"]
                dz = path[i]["z"] - path[i - 1]["z"]
                total += float(np.sqrt(dx * dx + dy * dy + dz * dz))
            return total

        length = path_length(estimated_trajectory)

        # ATE 估计（按时间戳最近邻对齐）
        if len(estimated_trajectory) > 1 and len(groundtruth_trajectory) > 1 and has_groundtruth:
            import bisect
            import math

            gt_ts = [p.get("timestamp", 0.0) for p in groundtruth_trajectory]
            diffs = []
            for est_p in estimated_trajectory:
                t = est_p.get("timestamp", 0.0)
                j = bisect.bisect_left(gt_ts, t)
                if j == 0:
                    gt_p = groundtruth_trajectory[0]
                elif j >= len(gt_ts):
                    gt_p = groundtruth_trajectory[-1]
                else:
                    # 选择更近的一个
                    before = groundtruth_trajectory[j - 1]
                    after = groundtruth_trajectory[j]
                    gt_p = before if abs(t - before.get("timestamp", 0.0)) <= abs(t - after.get("timestamp", 0.0)) else after
                dx = est_p["x"] - gt_p["x"]
                dy = est_p["y"] - gt_p["y"]
                dz = est_p["z"] - gt_p["z"]
                diffs.append(dx * dx + dy * dy + dz * dz)

            n = len(diffs)
            ate_rmse = math.sqrt(sum(diffs) / n) if n > 0 else 0.0
            ate_mean = ate_rmse  # 近似
            ate_median = ate_rmse
            ate_std = 0.0
            ate_min = 0.0
            ate_max = float(max(diffs)) ** 0.5 if diffs else 0.0
        else:
            ate_rmse = ate_mean = ate_median = ate_std = ate_min = ate_max = 0.0

        duration = (
            (
                estimated_trajectory[-1]["timestamp"]
                - estimated_trajectory[0]["timestamp"]
            )
            if len(estimated_trajectory) > 1
            else 0.0
        )

        return {
            "experiment_id": experiment_id,
            "algorithm_key": algorithm_key,
            "sequence": (
                getattr(config, "sequences", ["unknown"])[0]
                if hasattr(config, "sequences")
                else "unknown"
            ),
            "estimated_trajectory": estimated_trajectory,
            "groundtruth_trajectory": groundtruth_trajectory,
            "statistics": {
                "total_points": len(estimated_trajectory),
                "trajectory_length": float(length),
                "ate_rmse": float(ate_rmse),
                "ate_mean": float(ate_mean),
                "ate_median": float(ate_median),
                "ate_std": float(ate_std),
                "ate_min": float(ate_min),
                "ate_max": float(ate_max),
                "duration_seconds": float(duration),
                "success_rate": (
                    float(getattr(algorithm_key, "success_rate", 0.0))
                    if hasattr(algorithm_key, "success_rate")
                    else 0.0
                ),
            },
            "metadata": {
                "coordinate_system": "camera",
                "units": "meters",
                "dataset_name": str(getattr(config, "dataset_path", "unknown")),
                "algorithm_type": algorithm_key,
                "has_groundtruth": bool(has_groundtruth),
                "reference_groundtruth": bool(
                    not has_groundtruth and include_reference
                ),
                "alignment": "timestamp" if has_groundtruth else "index",
            },
        }

    def _create_empty_trajectory_data(
        self, experiment_id: str, algorithm_key: str
    ) -> Dict[str, Any]:
        """创建空的轨迹数据（对齐前端字段）"""
        return {
            "experiment_id": experiment_id,
            "algorithm_key": algorithm_key,
            "sequence": "unknown",
            "estimated_trajectory": [],
            "groundtruth_trajectory": [],
            "statistics": {
                "total_points": 0,
                "trajectory_length": 0.0,
                "ate_rmse": 0.0,
                "ate_mean": 0.0,
                "ate_median": 0.0,
                "ate_std": 0.0,
                "ate_min": 0.0,
                "ate_max": 0.0,
                "duration_seconds": 0.0,
                "success_rate": 0.0,
            },
            "metadata": {
                "coordinate_system": "camera",
                "units": "meters",
                "dataset_name": "unknown",
                "algorithm_type": algorithm_key,
            },
        }

    def _create_empty_pr_curve(self, algorithm_key: str) -> Dict[str, Any]:
        """创建空的PR曲线数据（不返回示例折线，避免误导）。"""
        return {
            "algorithm": algorithm_key,
            "precisions": [],
            "recalls": [],
            "thresholds": [],
            "auc_score": 0.0,
            "optimal_threshold": 0.0,
            "optimal_precision": 0.0,
            "optimal_recall": 0.0,
            "f1_scores": [],
            "max_f1_score": 0.0,
            "has_data": False,
            "message": "No PR data available for the given algorithm",
        }

    def _postprocess_pr_curve(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """对PR数据做轻量后处理：
        - precision 单调化（对每个 recall 位置取右侧最大 precision 包络）
        - 可选下采样（若点数>500，均匀采样至500），减少前端传输与渲染成本
        - 重新计算AUC与最优点以保证一致性
        """
        try:
            import numpy as np

            precisions = np.asarray(data.get("precisions") or [], dtype=float)
            recalls = np.asarray(data.get("recalls") or [], dtype=float)
            thresholds = np.asarray(data.get("thresholds") or [], dtype=float)
            f1_scores = np.asarray(data.get("f1_scores") or [], dtype=float)

            if len(precisions) == 0 or len(recalls) == 0:
                return data

            # 保留原始数组供前端选择“原始/单调化”展示
            # 先按召回率排序原始数据，确保原始数据也是正确顺序
            raw_order = np.argsort(recalls)
            raw_precisions = precisions[raw_order].copy()
            raw_recalls = recalls[raw_order].copy()
            raw_thresholds = thresholds[raw_order].copy() if thresholds.size > 0 else thresholds
            raw_f1_scores = f1_scores[raw_order].copy() if f1_scores.size > 0 else f1_scores

            # 1) 对齐长度
            n = min(len(precisions), len(recalls), len(thresholds) if thresholds.size > 0 else 10**9, len(f1_scores) if f1_scores.size > 0 else 10**9)
            precisions = precisions[:n]
            recalls = recalls[:n]
            thresholds = thresholds[:n] if thresholds.size > 0 else thresholds
            f1_scores = f1_scores[:n] if f1_scores.size > 0 else f1_scores

            # 2) 按 recall 升序排序
            order = np.argsort(recalls)
            recalls = recalls[order]
            precisions = precisions[order]
            thresholds = thresholds[order] if thresholds.size > 0 else thresholds
            f1_scores = f1_scores[order] if f1_scores.size > 0 else f1_scores

            # 3) 单调化：precision[i] = max(precision[i:])
            for i in range(len(precisions) - 2, -1, -1):
                if precisions[i] < precisions[i + 1]:
                    precisions[i] = precisions[i + 1]

            # 4) 下采样至最多500点
            max_points = 500
            if len(recalls) > max_points:
                idx = np.linspace(0, len(recalls) - 1, max_points).astype(int)
                recalls = recalls[idx]
                precisions = precisions[idx]
                thresholds = thresholds[idx] if thresholds.size > 0 else thresholds
                f1_scores = f1_scores[idx] if f1_scores.size > 0 else f1_scores

            # 5) 使用原始 AUC（scikit-learn 计算的更准确）
            auc = float(data.get("auc_score", 0.0))
            if f1_scores.size == 0:
                # 若没有提供F1，按 2PR/(P+R) 现算
                denom = (precisions + recalls)
                f1_scores = np.where(denom > 0, 2 * precisions * recalls / denom, 0.0)

            max_idx = int(np.argmax(f1_scores))
            optimal_threshold = float(thresholds[max_idx]) if thresholds.size > 0 else float(data.get("optimal_threshold", 0.0))

            result = dict(data)
            result.update({
                # 处理后的
                "precisions": precisions.tolist(),
                "recalls": recalls.tolist(),
                "thresholds": thresholds.tolist() if thresholds.size > 0 else data.get("thresholds", []),
                "auc_score": float(max(0.0, min(1.0, auc))),
                "optimal_threshold": optimal_threshold,
                "optimal_precision": float(precisions[max_idx]) if len(precisions) else 0.0,
                "optimal_recall": float(recalls[max_idx]) if len(recalls) else 0.0,
                "f1_scores": f1_scores.tolist(),
                "max_f1_score": float(f1_scores[max_idx]) if len(f1_scores) else 0.0,
                # 原始的
                "raw_precisions": raw_precisions.tolist(),
                "raw_recalls": raw_recalls.tolist(),
                "raw_thresholds": raw_thresholds.tolist() if hasattr(raw_thresholds, 'tolist') else (data.get("thresholds", [])),
                "raw_f1_scores": raw_f1_scores.tolist() if hasattr(raw_f1_scores, 'tolist') else (data.get("f1_scores", [])),
            })
            return result
        except Exception:
            return data





    def _export_json(self, export_data: Dict[str, Any]) -> IO[bytes]:
        """导出JSON格式"""
        json_str = json.dumps(export_data, indent=2, ensure_ascii=False)
        return io.BytesIO(json_str.encode("utf-8"))

    def _export_csv(self, export_data: Dict[str, Any]) -> IO[bytes]:
        """导出CSV格式"""
        output = io.StringIO()
        writer = csv.writer(output)

        # 写入表头
        headers = [
            "experiment_id",
            "algorithm_key",
            "feature_type",
            "ransac_type",
            "success_rate",
            "avg_frame_time_ms",
            "avg_matches",
            "avg_inliers",
            "avg_inlier_ratio",
        ]
        writer.writerow(headers)

        # 写入数据
        experiment_id = export_data.get("experiment_info", {}).get(
            "experiment_id", "unknown"
        )
        for alg_result in export_data.get("algorithm_results", []):
            algorithm_key = alg_result.get("algorithm_key", "unknown")
            metrics = alg_result.get("metrics", {})

            # 解析算法键获取特征类型和RANSAC类型
            parts = algorithm_key.split("_")
            feature_type = parts[0] if len(parts) > 0 else "unknown"
            ransac_type = parts[1] if len(parts) > 1 else "unknown"

            row = [
                experiment_id,
                algorithm_key,
                feature_type,
                ransac_type,
                metrics.get("success_rate", 0.0),
                metrics.get("avg_frame_time_ms", 0.0),
                metrics.get("matching", {}).get("avg_matches", 0),
                metrics.get("matching", {}).get("avg_inliers", 0),
                metrics.get("matching", {}).get("avg_inlier_ratio", 0.0),
            ]
            writer.writerow(row)

        csv_bytes = output.getvalue().encode("utf-8")
        return io.BytesIO(csv_bytes)

    def _export_xlsx(self, export_data: Dict[str, Any]) -> IO[bytes]:
        """导出Excel格式"""
        try:
            import openpyxl
            from openpyxl.utils.dataframe import dataframe_to_rows
            import pandas as pd

            # 创建工作簿
            wb = openpyxl.Workbook()

            # 实验信息工作表
            ws_info = wb.active
            ws_info.title = "实验信息"

            exp_info = export_data.get("experiment_info", {})
            info_data = [
                ["实验ID", exp_info.get("experiment_id", "unknown")],
                ["时间戳", exp_info.get("timestamp", "unknown")],
                ["总运行数", exp_info.get("total_runs", 0)],
                ["成功运行数", exp_info.get("successful_runs", 0)],
                ["失败运行数", exp_info.get("failed_runs", 0)],
            ]

            for row in info_data:
                ws_info.append(row)

            # 算法结果工作表
            ws_results = wb.create_sheet("算法结果")
            headers = [
                "算法键",
                "特征类型",
                "RANSAC类型",
                "成功率",
                "平均帧处理时间(ms)",
                "平均匹配数",
                "平均内点数",
                "平均内点比例",
            ]
            ws_results.append(headers)

            for alg_result in export_data.get("algorithm_results", []):
                algorithm_key = alg_result.get("algorithm_key", "unknown")
                metrics = alg_result.get("metrics", {})

                parts = algorithm_key.split("_")
                feature_type = parts[0] if len(parts) > 0 else "unknown"
                ransac_type = parts[1] if len(parts) > 1 else "unknown"

                row = [
                    algorithm_key,
                    feature_type,
                    ransac_type,
                    metrics.get("success_rate", 0.0),
                    metrics.get("avg_frame_time_ms", 0.0),
                    metrics.get("matching", {}).get("avg_matches", 0),
                    metrics.get("matching", {}).get("avg_inliers", 0),
                    metrics.get("matching", {}).get("avg_inlier_ratio", 0.0),
                ]
                ws_results.append(row)

            # 保存到字节流
            output = io.BytesIO()
            wb.save(output)
            output.seek(0)
            return output

        except ImportError:
            logger.warning("openpyxl未安装，无法导出Excel格式")
            # 回退到CSV格式
            return self._export_csv(export_data)
        except Exception as e:
            logger.error(f"导出Excel失败: {e}")
            # 回退到CSV格式
            return self._export_csv(export_data)

    def _export_pdf(self, export_data: Dict[str, Any]) -> IO[bytes]:
        """导出PDF格式"""
        try:
            from reportlab.lib.pagesizes import letter, A4
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            from reportlab.lib import colors
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont
            import os

            # 注册中文字体（如果可用）
            try:
                # 尝试使用系统字体
                font_paths = [
                    '/System/Library/Fonts/PingFang.ttc',  # macOS
                    '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',  # Linux
                    'C:/Windows/Fonts/msyh.ttc',  # Windows
                ]
                font_registered = False
                for font_path in font_paths:
                    if os.path.exists(font_path):
                        try:
                            pdfmetrics.registerFont(TTFont('Chinese', font_path))
                            font_registered = True
                            break
                        except:
                            continue

                if not font_registered:
                    # 使用默认字体
                    chinese_font = 'Helvetica'
                else:
                    chinese_font = 'Chinese'
            except:
                chinese_font = 'Helvetica'

            # 创建PDF文档
            output = io.BytesIO()
            doc = SimpleDocTemplate(output, pagesize=A4)
            story = []

            # 获取样式
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontName=chinese_font,
                fontSize=16,
                spaceAfter=30,
                alignment=1  # 居中
            )
            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontName=chinese_font,
                fontSize=14,
                spaceAfter=12
            )
            normal_style = ParagraphStyle(
                'CustomNormal',
                parent=styles['Normal'],
                fontName=chinese_font,
                fontSize=10,
                spaceAfter=6
            )

            # 标题
            exp_info = export_data.get("experiment_info", {})
            title = f"Experiment Results Report - {exp_info.get('experiment_id', 'Unknown')}"
            story.append(Paragraph(title, title_style))
            story.append(Spacer(1, 12))

            # 实验信息
            story.append(Paragraph("Experiment Information", heading_style))
            exp_data = [
                ["Experiment ID", exp_info.get("experiment_id", "unknown")],
                ["Timestamp", str(exp_info.get("timestamp", "unknown"))],
                ["Total Runs", str(exp_info.get("total_runs", 0))],
                ["Successful Runs", str(exp_info.get("successful_runs", 0))],
                ["Failed Runs", str(exp_info.get("failed_runs", 0))],
            ]

            exp_table = Table(exp_data, colWidths=[2*inch, 3*inch])
            exp_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), chinese_font),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(exp_table)
            story.append(Spacer(1, 20))

            # 算法结果
            story.append(Paragraph("Algorithm Results", heading_style))

            # 创建算法结果表格
            alg_headers = [
                "Algorithm", "Feature Type", "RANSAC Type", "Success Rate",
                "Avg Frame Time (ms)", "Avg Matches", "Avg Inliers", "Avg Inlier Ratio"
            ]
            alg_data = [alg_headers]

            for alg_result in export_data.get("algorithm_results", []):
                algorithm_key = alg_result.get("algorithm_key", "unknown")
                metrics = alg_result.get("metrics", {})

                parts = algorithm_key.split("_")
                feature_type = parts[0] if len(parts) > 0 else "unknown"
                ransac_type = parts[1] if len(parts) > 1 else "unknown"

                row = [
                    algorithm_key,
                    feature_type,
                    ransac_type,
                    f"{metrics.get('success_rate', 0.0):.3f}",
                    f"{metrics.get('avg_frame_time_ms', 0.0):.2f}",
                    str(metrics.get("matching", {}).get("avg_matches", 0)),
                    str(metrics.get("matching", {}).get("avg_inliers", 0)),
                    f"{metrics.get('matching', {}).get('avg_inlier_ratio', 0.0):.3f}",
                ]
                alg_data.append(row)

            if len(alg_data) > 1:  # 有数据
                alg_table = Table(alg_data, colWidths=[1.2*inch, 0.8*inch, 0.8*inch, 0.8*inch, 1*inch, 0.8*inch, 0.8*inch, 1*inch])
                alg_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, -1), chinese_font),
                    ('FONTSIZE', (0, 0), (-1, -1), 8),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                story.append(alg_table)
            else:
                story.append(Paragraph("No algorithm results available.", normal_style))

            # 生成PDF
            doc.build(story)
            output.seek(0)
            return output

        except ImportError as e:
            logger.warning(f"PDF导出依赖未安装 (reportlab): {e}")
            # 回退到JSON格式
            return self._export_json(export_data)
        except Exception as e:
            logger.error(f"导出PDF失败: {e}")
            # 回退到JSON格式
            return self._export_json(export_data)

    def _add_reference_trajectory(self, trajectory_data: dict, experiment_id: str) -> dict:
        """为轨迹数据动态添加参考轨迹"""
        try:
            # 如果已有参考轨迹，直接返回
            if 'reference_trajectory' in trajectory_data:
                return trajectory_data

            # 生成简单的参考直线轨迹
            estimated = trajectory_data.get('estimated_trajectory', [])
            if not estimated:
                return trajectory_data

            # 基于估计轨迹的起点和终点生成直线参考
            start_point = estimated[0] if estimated else {"x": 0.0, "y": 0.0, "z": 0.0, "timestamp": 0.0}
            end_point = estimated[-1] if len(estimated) > 1 else {"x": 1.0, "y": 0.0, "z": 0.0, "timestamp": 1.0}

            reference = []
            for i, est_point in enumerate(estimated):
                t = i / (len(estimated) - 1) if len(estimated) > 1 else 0
                ref_point = {
                    "x": float(start_point.get("x", 0.0) + t * (end_point.get("x", 0.0) - start_point.get("x", 0.0))),
                    "y": float(start_point.get("y", 0.0) + t * (end_point.get("y", 0.0) - start_point.get("y", 0.0))),
                    "z": float(start_point.get("z", 0.0) + t * (end_point.get("z", 0.0) - start_point.get("z", 0.0))),
                    "timestamp": float(est_point.get("timestamp", 0.0)),
                    "frame_id": int(est_point.get("frame_id", i)),
                }
                reference.append(ref_point)

            trajectory_data['reference_trajectory'] = reference
            return trajectory_data

        except Exception as e:
            logger.error(f"添加参考轨迹失败: {e}")
            return trajectory_data


# 全局单例实例
result_service = ResultService()
