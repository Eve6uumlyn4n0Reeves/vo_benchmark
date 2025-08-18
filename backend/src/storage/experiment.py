#
# 功能: 提供实验数据的高层存储接口。
#
from typing import List, Optional, Tuple
import json
from .base import Storage
from src.models.experiment import ExperimentSummary, ExperimentConfig
from src.models.evaluation import AlgorithmMetrics
from src.models.frame import FrameResult
from src.models.types import FeatureType, RANSACType
from src.api.serializers import UnifiedSerializer
from pathlib import Path
import logging
from .manifest import ManifestManager

logger = logging.getLogger(__name__)


class ExperimentStorage:
    """实验数据存储管理器

    为了兼容旧代码路径，允许无参初始化：将自动使用配置中的 RESULTS_ROOT 或当前目录下的 ./results 作为根目录。
    建议新代码始终显式传入 Storage 实现。
    """

    def __init__(self, storage: Optional[Storage] = None):
        if storage is None:
            # 兼容无参构造：回退到文件系统存储
            try:
                from flask import current_app

                cfg_results_root = None
                if current_app and hasattr(current_app, "config"):
                    cfg_results_root = current_app.config.get("RESULTS_ROOT")
            except Exception:
                cfg_results_root = None

            from src.storage.filesystem import FileSystemStorage  # 延迟导入避免循环

            base = (
                Path(cfg_results_root).resolve()
                if cfg_results_root
                else Path("./results").resolve()
            )
            base.mkdir(parents=True, exist_ok=True)
            storage = FileSystemStorage(str(base))
            logger.info(
                f"ExperimentStorage: initialized with default FileSystemStorage at {base}"
            )
        self._storage = storage
        self._manifest_manager = ManifestManager(storage.root_dir)

    def save_experiment(self, experiment_id: str, summary: ExperimentSummary) -> None:
        """保存实验摘要"""
        try:
            # 序列化实验摘要
            data = self._serialize_experiment_summary(summary)
            key = f"experiments/{experiment_id}/summary"
            self._storage.save(key, data)
            logger.info(f"保存实验摘要: {experiment_id}")
        except Exception as e:
            logger.error(f"保存实验摘要失败: {e}")
            raise

    def save_algorithm_result(
        self, experiment_id: str, algorithm_key: str, result: AlgorithmMetrics
    ) -> None:
        """保存算法结果"""
        try:
            # 序列化算法指标
            data = self._serialize_algorithm_metrics(result)
            key = f"experiments/{experiment_id}/algorithms/{algorithm_key}"
            self._storage.save(key, data)
            logger.info(f"保存算法结果: {experiment_id}/{algorithm_key}")
        except Exception as e:
            logger.error(f"保存算法结果失败: {e}")
            raise

    def save_frame_result(
        self, experiment_id: str, algorithm_key: str, frame_id: int, frame: FrameResult
    ) -> None:
        """保存单个帧结果（用于流式处理）"""
        try:
            # 序列化单个帧结果
            data = self._serialize_frame_result(frame)
            key = f"experiments/{experiment_id}/frames/{algorithm_key}/{frame_id:06d}"
            self._storage.save(key, data)
            logger.debug(
                f"保存帧结果: {experiment_id}/{algorithm_key}/frame_{frame_id}"
            )
        except Exception as e:
            logger.error(f"保存帧结果失败: {e}")
            raise

    def save_frame_results(
        self, experiment_id: str, algorithm_key: str, frames: List[FrameResult]
    ) -> None:
        """保存帧结果（批量保存，向后兼容）"""
        try:
            # 序列化帧结果列表
            data = [self._serialize_frame_result(frame) for frame in frames]
            key = f"experiments/{experiment_id}/frames/{algorithm_key}"
            self._storage.save(key, data)
            logger.info(f"保存帧结果: {experiment_id}/{algorithm_key}, {len(frames)}帧")
        except Exception as e:
            logger.error(f"保存帧结果失败: {e}")
            raise

    def save_pr_curve(self, experiment_id: str, algorithm_key: str, pr_data: dict) -> None:
        """保存预计算的PR曲线数据（同时保存Full和UI版本）"""
        try:
            # 保存Full版本（JSON格式，向后兼容）
            key = f"experiments/{experiment_id}/pr_curves/{algorithm_key}"
            self._storage.save(key, pr_data)

            # 保存Arrow格式（Full + UI）
            self._save_pr_curve_arrow(experiment_id, algorithm_key, pr_data)

            # 更新清单
            self._manifest_manager.update_manifest_after_save(experiment_id, algorithm_key)

            logger.info(f"保存PR曲线数据: {experiment_id}/{algorithm_key}")
        except Exception as e:
            logger.error(f"保存PR曲线数据失败: {e}")
            raise

    def get_pr_curve(self, experiment_id: str, algorithm_key: str) -> Optional[dict]:
        """获取预计算的PR曲线数据"""
        try:
            key = f"experiments/{experiment_id}/pr_curves/{algorithm_key}"
            return self._storage.load(key)
        except Exception as e:
            logger.debug(f"获取PR曲线数据失败: {e}")
            return None

    def get_pr_curve_arrow(self, experiment_id: str, algorithm_key: str, ui_version: bool = False) -> Optional[dict]:
        """获取Arrow格式的PR曲线数据"""
        try:
            from .arrow_writer import ArrowReader
            reader = ArrowReader()

            suffix = ".ui.arrow" if ui_version else ".arrow"
            arrow_path = self._storage.root_dir / f"experiments/{experiment_id}/pr_curves/{algorithm_key}{suffix}"

            return reader.read_pr_curve(arrow_path)
        except Exception as e:
            logger.debug(f"获取Arrow PR曲线数据失败: {e}")
            return None


    def save_trajectory(self, experiment_id: str, algorithm_key: str, trajectory_data: dict) -> None:
        """保存预计算的轨迹数据（同时保存Full和UI版本）"""
        try:
            # 保存Full版本（JSON格式，向后兼容）
            key = f"experiments/{experiment_id}/trajectories/{algorithm_key}"
            self._storage.save(key, trajectory_data)

            # 保存Arrow格式（Full + UI）
            self._save_trajectory_arrow(experiment_id, algorithm_key, trajectory_data)

            # 更新清单
            self._manifest_manager.update_manifest_after_save(experiment_id, algorithm_key)

            logger.info(f"保存轨迹数据: {experiment_id}/{algorithm_key}")
        except Exception as e:
            logger.error(f"保存轨迹数据失败: {e}")
            raise

    def get_trajectory(self, experiment_id: str, algorithm_key: str) -> Optional[dict]:
        """获取预计算的轨迹数据"""
        try:
            key = f"experiments/{experiment_id}/trajectories/{algorithm_key}"
            return self._storage.load(key)
        except Exception as e:
            logger.debug(f"获取轨迹数据失败: {e}")
            return None

    def get_trajectory_arrow(self, experiment_id: str, algorithm_key: str, ui_version: bool = False) -> Optional[dict]:
        """获取Arrow格式的轨迹数据"""
        try:
            from .arrow_writer import ArrowReader
            reader = ArrowReader()

            suffix = ".ui.arrow" if ui_version else ".arrow"
            arrow_path = self._storage.root_dir / f"experiments/{experiment_id}/trajectories/{algorithm_key}{suffix}"

            return reader.read_trajectory(arrow_path)
        except Exception as e:
            logger.debug(f"获取Arrow轨迹数据失败: {e}")
            return None

    def get_manifest(self, experiment_id: str, algorithm_key: str) -> Optional[dict]:
        """获取实验数据清单"""
        return self._manifest_manager.load_manifest(experiment_id, algorithm_key)

    def generate_manifest(self, experiment_id: str, algorithm_key: str) -> dict:
        """生成实验数据清单"""
        return self._manifest_manager.generate_manifest(experiment_id, algorithm_key)

    def save_frame_summary(self, experiment_id: str, algorithm_key: str, summary: dict) -> None:
        """保存预计算的帧结果统计"""
        try:
            key = f"experiments/{experiment_id}/frame_summaries/{algorithm_key}"
            self._storage.save(key, summary)
            logger.info(f"保存帧结果统计: {experiment_id}/{algorithm_key}")
        except Exception as e:
            logger.error(f"保存帧结果统计失败: {e}")
            raise

    def get_frame_summary(self, experiment_id: str, algorithm_key: str) -> Optional[dict]:
        """获取预计算的帧结果统计"""
        try:
            key = f"experiments/{experiment_id}/frame_summaries/{algorithm_key}"
            return self._storage.load(key)
        except Exception as e:
            logger.debug(f"获取帧结果统计失败: {e}")
            return None

    def list_algorithms(self, experiment_id: str) -> List[str]:
        """列出实验下的算法键（仅一层，不包含帧/文件名）。"""
        try:
            prefix = f"experiments/{experiment_id}/algorithms/"
            keys = self._storage.list_keys(prefix)
            algs = []
            for k in keys:
                if not k.startswith(prefix):
                    continue
                parts = k[len(prefix):].split("/")
                if parts and parts[0] and parts[0] not in algs:
                    algs.append(parts[0])
            return sorted(algs)
        except Exception:
            return []

    def _batch_load_frames(self, frame_keys: List[str]) -> List[FrameResult]:
        """批量加载帧文件，提升性能"""
        import concurrent.futures
        import threading

        frames = []

        def load_single_frame(key: str) -> Optional[FrameResult]:
            try:
                frame_data = self._storage.load(key)
                if frame_data is not None:
                    return self._deserialize_frame_result(frame_data)
            except Exception as e:
                logger.warning(f"批量加载帧文件失败 {key}: {e}")
            return None

        # 使用线程池并行加载，限制并发数避免过多I/O
        max_workers = min(8, len(frame_keys))
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_key = {executor.submit(load_single_frame, key): key for key in frame_keys}

            for future in concurrent.futures.as_completed(future_to_key):
                result = future.result()
                if result is not None:
                    frames.append(result)

        # 按原始顺序排序（根据frame_id）
        frames.sort(key=lambda f: f.frame_id if hasattr(f, 'frame_id') else 0)

        logger.info(f"批量加载完成：{len(frames)}/{len(frame_keys)} 个帧文件")
        return frames

    def get_experiment(self, experiment_id: str) -> Optional[ExperimentSummary]:
        """获取实验摘要"""
        try:
            # 统一目录结构：仅允许 experiments/{id}/summary
            key = f"experiments/{experiment_id}/summary"
            data = self._storage.load(key)
            if data is None:
                return None
            return self._deserialize_experiment_summary(data)
        except Exception as e:
            logger.error(f"获取实验摘要失败: {e}")
            return None

    def get_algorithm_result(
        self, experiment_id: str, algorithm_key: str
    ) -> Optional[AlgorithmMetrics]:
        """获取算法结果"""
        try:
            key = f"experiments/{experiment_id}/algorithms/{algorithm_key}"
            data = self._storage.load(key)
            if data is None:
                return None

            return self._deserialize_algorithm_metrics(data)
        except Exception as e:
            logger.error(f"获取算法结果失败: {e}")
            return None

    def get_frame_results(
        self, experiment_id: str, algorithm_key: str, start: int, limit: int
    ) -> Tuple[List[FrameResult], int]:
        """获取帧结果（分页）
        兼容两种存储结构：
        1) 批量保存：experiments/{id}/frames/{alg} -> [frame,...]
        2) 逐帧保存：experiments/{id}/frames/{alg}/{frame_id:06d} -> frame
        """
        try:
            base_key = f"experiments/{experiment_id}/frames/{algorithm_key}"

            # 优先尝试批量文件
            data = self._storage.load(base_key)
            if isinstance(data, list):
                all_frames = [
                    self._deserialize_frame_result(frame_data) for frame_data in data
                ]
                total = len(all_frames)
                end = start + limit
                return all_frames[start:end], total

            # 回退：聚合逐帧文件
            try:
                keys = self._storage.list_keys(base_key)
            except Exception:
                keys = []

            # 过滤出逐帧文件键（base_key/xxxxxx 形式），并按文件名排序
            frame_keys = [
                k
                for k in keys
                if k.startswith(base_key + "/")
                and len(k.split("/")) == len(base_key.split("/")) + 1
            ]
            frame_keys.sort()  # 000001, 000002 ... 的字典序即可

            if not frame_keys:
                return [], 0

            total = len(frame_keys)
            # 仅加载当前分页范围内的帧，避免一次性加载全部
            end = min(start + limit, total)
            page_keys = frame_keys[start:end]

            frames: List[FrameResult] = []

            # 批量加载优化：并行加载多个帧文件
            if len(page_keys) > 10:
                logger.info(f"批量加载 {len(page_keys)} 个帧文件")
                frames = self._batch_load_frames(page_keys)
            else:
                # 少量文件仍使用逐个加载
                for k in page_keys:
                    try:
                        frame_data = self._storage.load(k)
                        if frame_data is not None:
                            frames.append(self._deserialize_frame_result(frame_data))
                    except Exception as e:
                        logger.warning(f"加载帧文件失败 {k}: {e}")
                        continue

            return frames, total
        except Exception as e:
            logger.error(f"获取帧结果失败: {e}")
            return [], 0

    def list_experiments(self) -> List[ExperimentSummary]:
        """列出所有实验（优化版本）"""
        try:
            import time
            start_time = time.time()

            # 直接扫描实验目录，避免递归扫描所有文件
            experiments_dir = self._storage.root_dir / "experiments"
            if not experiments_dir.exists():
                logger.info("实验目录不存在")
                return []

            experiment_ids = set()
            experiments = []

            # 直接遍历实验目录，而不是扫描所有文件
            for exp_dir in experiments_dir.iterdir():
                if exp_dir.is_dir() and exp_dir.name != "experiments":  # 避免双层experiments目录
                    exp_id = exp_dir.name

                    # 检查是否有summary文件
                    summary_files = [
                        exp_dir / "summary.json.gz",
                        exp_dir / "summary.json",
                        exp_dir / "summary.pkl.gz",
                        exp_dir / "summary.pkl"
                    ]

                    summary_found = False
                    for summary_file in summary_files:
                        if summary_file.exists():
                            try:
                                # 直接加载summary文件，避免通过get_experiment的双重查找
                                data = self._storage._load_file(summary_file)
                                if data:
                                    exp_summary = self._deserialize_experiment_summary(data)
                                    if exp_summary:
                                        experiments.append(exp_summary)
                                        experiment_ids.add(exp_id)
                                        summary_found = True
                                        break
                            except Exception as e:
                                logger.warning(f"加载实验摘要失败 {exp_id}: {e}")
                                continue

                    if not summary_found:
                        logger.debug(f"实验 {exp_id} 没有找到有效的summary文件")

            # 按时间戳排序
            experiments.sort(key=lambda x: x.timestamp, reverse=True)

            end_time = time.time()
            logger.info(f"list_experiments: 找到 {len(experiments)} 个实验，耗时 {end_time - start_time:.3f}秒")
            return experiments

        except Exception as e:
            logger.error(f"列出实验失败: {e}")
            return []

    def get_all_algorithm_results(self, experiment_id: str) -> List[AlgorithmMetrics]:
        """获取实验的所有算法结果"""
        try:
            # 获取算法结果键
            prefix = f"experiments/{experiment_id}/algorithms/"
            keys = self._storage.list_keys(prefix)

            results = []
            for key in keys:
                # 提取算法键
                algorithm_key = key.replace(prefix, "")
                result = self.get_algorithm_result(experiment_id, algorithm_key)
                if result:
                    results.append(result)

            return results

        except Exception as e:
            logger.error(f"获取所有算法结果失败: {e}")
            return []

    def delete_experiment(self, experiment_id: str) -> bool:
        """删除实验及其所有数据（统一目录 experiments/{id}/...）。"""
        try:
            deleted_count = 0

            # 仅标准前缀
            prefixes = [f"experiments/{experiment_id}/"]

            seen_keys = set()
            for prefix in prefixes:
                keys = self._storage.list_keys(prefix)
                for key in keys:
                    if key in seen_keys:
                        continue
                    if self._storage.delete(key):
                        deleted_count += 1
                        seen_keys.add(key)

            # 3) 兜底：全量扫描 experiments/ 下包含该 experiment_id 的键
            if deleted_count == 0:
                for key in self._storage.list_keys("experiments/"):
                    if f"/{experiment_id}/" in key:
                        if key in seen_keys:
                            continue
                        if self._storage.delete(key):
                            deleted_count += 1
                            seen_keys.add(key)

            logger.info(f"删除实验 {experiment_id}，删除了 {deleted_count} 个文件")
            return deleted_count > 0

        except Exception as e:
            logger.error(f"删除实验失败: {e}")
            return False

    def _serialize_experiment_summary(self, summary: ExperimentSummary) -> dict:
        """序列化实验摘要"""
        return {
            "experiment_id": summary.experiment_id,
            "timestamp": summary.timestamp,
            "config": self._serialize_experiment_config(summary.config),
            "total_runs": summary.total_runs,
            "successful_runs": summary.successful_runs,
            "failed_runs": summary.failed_runs,
            "algorithms_tested": summary.algorithms_tested,
            "sequences_processed": summary.sequences_processed,
        }

    def _serialize_experiment_config(self, config: ExperimentConfig) -> dict:
        """序列化实验配置"""
        return {
            "name": config.name,
            "dataset_path": str(config.dataset_path),
            "output_dir": str(config.output_dir),
            "feature_types": [ft.value for ft in config.feature_types],
            "ransac_types": [rt.value for rt in config.ransac_types],
            "sequences": config.sequences,
            "num_runs": config.num_runs,
            "parallel_jobs": config.parallel_jobs,
            "random_seed": config.random_seed,
            "save_frame_data": config.save_frame_data,
            "save_descriptors": config.save_descriptors,
            "compute_pr_curves": config.compute_pr_curves,
            "analyze_ransac": config.analyze_ransac,
            "ransac_success_threshold": config.ransac_success_threshold,
            "max_features": config.max_features,
            "feature_params": config.feature_params,
            "ransac_threshold": config.ransac_threshold,
            "ransac_confidence": config.ransac_confidence,
            "ransac_max_iters": config.ransac_max_iters,
        }

    def _deserialize_experiment_summary(self, data: dict) -> ExperimentSummary:
        """反序列化实验摘要"""
        config_data = data["config"]
        config = ExperimentConfig(
            name=config_data["name"],
            dataset_path=Path(config_data["dataset_path"]),
            output_dir=Path(config_data["output_dir"]),
            feature_types=[FeatureType(ft) for ft in config_data["feature_types"]],
            ransac_types=[RANSACType(rt) for rt in config_data["ransac_types"]],
            sequences=config_data["sequences"],
            num_runs=config_data["num_runs"],
            parallel_jobs=config_data["parallel_jobs"],
            random_seed=config_data["random_seed"],
            save_frame_data=config_data["save_frame_data"],
            save_descriptors=config_data["save_descriptors"],
            compute_pr_curves=config_data["compute_pr_curves"],
            analyze_ransac=config_data["analyze_ransac"],
            ransac_success_threshold=config_data["ransac_success_threshold"],
            max_features=config_data["max_features"],
            feature_params=config_data["feature_params"],
            ransac_threshold=config_data["ransac_threshold"],
            ransac_confidence=config_data["ransac_confidence"],
            ransac_max_iters=config_data["ransac_max_iters"],
        )

        return ExperimentSummary(
            experiment_id=data["experiment_id"],
            timestamp=data["timestamp"],
            config=config,
            total_runs=data["total_runs"],
            successful_runs=data["successful_runs"],
            failed_runs=data["failed_runs"],
            algorithms_tested=data["algorithms_tested"],
            sequences_processed=data["sequences_processed"],
        )

    def _serialize_algorithm_metrics(self, metrics: AlgorithmMetrics) -> dict:
        """序列化算法指标（使用统一序列化器）"""
        return UnifiedSerializer.serialize_algorithm_metrics(metrics)



    def get_frame_result(
        self, experiment_id: str, algorithm_key: str, frame_id: int
    ) -> Optional[FrameResult]:
        """获取单个帧结果（同时兼容批量和逐帧两种存储结构）。

        优先按逐帧键读取：experiments/{id}/frames/{alg}/{frame_id:06d}
        若不存在，则回退加载批量文件并按 frame_id 查找。
        """
        try:
            # 1) 尝试逐帧文件
            single_key = f"experiments/{experiment_id}/frames/{algorithm_key}/{frame_id:06d}"
            data = self._storage.load(single_key)
            if isinstance(data, dict):
                return self._deserialize_frame_result(data)

            # 2) 回退批量文件
            base_key = f"experiments/{experiment_id}/frames/{algorithm_key}"
            data = self._storage.load(base_key)
            if isinstance(data, list):
                for frame_data in data:
                    try:
                        if isinstance(frame_data, dict) and frame_data.get("frame_id") == frame_id:
                            return self._deserialize_frame_result(frame_data)
                    except Exception:
                        continue
            return None
        except Exception as e:
            logger.error(f"获取单帧结果失败: exp={experiment_id} alg={algorithm_key} frame={frame_id} err={e}")
            return None


    def _serialize_frame_result(self, frame: FrameResult) -> dict:
        """序列化帧结果"""
        return {
            "frame_id": frame.frame_id,
            "timestamp": frame.timestamp,
            "features": (
                self._serialize_frame_features(frame.features)
                if frame.features
                else None
            ),
            "matches": (
                self._serialize_frame_matches(frame.matches) if frame.matches else None
            ),
            "ransac": (
                self._serialize_ransac_result(frame.ransac) if frame.ransac else None
            ),
            "num_matches": frame.num_matches,
            "num_inliers": frame.num_inliers,
            "inlier_ratio": frame.inlier_ratio,
            "estimated_pose": (
                frame.estimated_pose.tolist()
                if frame.estimated_pose is not None
                else None
            ),
            "ground_truth_pose": (
                frame.ground_truth_pose.tolist()
                if frame.ground_truth_pose is not None
                else None
            ),
            "processing_time": frame.processing_time,
            "status": frame.status,
            "pose_error": frame.pose_error,
            "reprojection_errors": frame.reprojection_errors,
            "error": frame.error,
        }

    def _serialize_frame_features(self, features) -> dict:
        """序列化帧特征"""
        return {
            "keypoints": features.keypoints,
            "descriptors": (
                features.descriptors.tolist()
                if hasattr(features, "descriptors") and features.descriptors is not None
                else []
            ),
            "scores": (
                features.scores
                if hasattr(features, "scores") and features.scores is not None
                else []
            ),
        }

    def _save_trajectory_arrow(self, experiment_id: str, algorithm_key: str, trajectory_data: dict) -> None:
        """保存轨迹数据的Arrow格式（Full + UI版本）"""
        try:
            from .arrow_writer import ArrowWriter
            writer = ArrowWriter()

            # 提取轨迹数据
            estimated = trajectory_data.get("estimated_trajectory", [])
            groundtruth = trajectory_data.get("groundtruth_trajectory", [])
            reference = trajectory_data.get("reference_trajectory", [])
            metadata = trajectory_data.get("metadata", {})

            if not estimated:
                logger.warning(f"轨迹数据为空，跳过Arrow保存: {experiment_id}/{algorithm_key}")
                return

            # 保存Full版本
            full_path = self._storage.root_dir / f"experiments/{experiment_id}/trajectories/{algorithm_key}.arrow"
            writer.write_trajectory(
                full_path,
                estimated,
                groundtruth,
                reference,
                {**metadata, "version": "full"}
            )

            # 创建UI版本（下采样）
            ui_estimated = writer.downsample_trajectory(estimated, max_points=1500)
            ui_groundtruth = writer.downsample_trajectory(groundtruth, max_points=1500) if groundtruth else None
            ui_reference = writer.downsample_trajectory(reference, max_points=1500) if reference else None

            ui_path = self._storage.root_dir / f"experiments/{experiment_id}/trajectories/{algorithm_key}.ui.arrow"
            writer.write_trajectory(
                ui_path,
                ui_estimated,
                ui_groundtruth,
                ui_reference,
                {**metadata, "version": "ui", "downsampled": len(estimated) > 1500, "original_points": len(estimated)}
            )

            logger.info(f"Arrow轨迹数据已保存: Full({len(estimated)}点) + UI({len(ui_estimated)}点)")

        except Exception as e:
            logger.warning(f"保存Arrow轨迹数据失败（忽略）: {e}")

    def _save_pr_curve_arrow(self, experiment_id: str, algorithm_key: str, pr_data: dict) -> None:
        """保存PR曲线数据的Arrow格式（Full + UI版本）"""
        try:
            from .arrow_writer import ArrowWriter
            writer = ArrowWriter()

            # 提取PR数据
            precisions = pr_data.get("precisions", [])
            recalls = pr_data.get("recalls", [])
            thresholds = pr_data.get("thresholds", [])
            f1_scores = pr_data.get("f1_scores", [])

            # 原始数据（如果存在）
            raw_precisions = pr_data.get("raw_precisions")
            raw_recalls = pr_data.get("raw_recalls")
            raw_thresholds = pr_data.get("raw_thresholds")
            raw_f1_scores = pr_data.get("raw_f1_scores")

            if not precisions or not recalls:
                logger.warning(f"PR曲线数据为空，跳过Arrow保存: {experiment_id}/{algorithm_key}")
                return

            # 元数据
            metadata = {
                "algorithm": pr_data.get("algorithm", algorithm_key),
                "auc_score": str(pr_data.get("auc_score", 0.0)),
                "optimal_threshold": str(pr_data.get("optimal_threshold", 0.0)),
                "optimal_precision": str(pr_data.get("optimal_precision", 0.0)),
                "optimal_recall": str(pr_data.get("optimal_recall", 0.0)),
                "max_f1_score": str(pr_data.get("max_f1_score", 0.0)),
            }

            # 保存Full版本
            full_path = self._storage.root_dir / f"experiments/{experiment_id}/pr_curves/{algorithm_key}.arrow"
            writer.write_pr_curve(
                full_path,
                precisions, recalls, thresholds, f1_scores,
                raw_precisions, raw_recalls, raw_thresholds, raw_f1_scores,
                {**metadata, "version": "full"}
            )

            # 创建UI版本（下采样）
            ui_precisions, ui_recalls, ui_thresholds, ui_f1_scores = writer.downsample_pr_curve(
                precisions, recalls, thresholds, f1_scores, max_points=500
            )

            ui_path = self._storage.root_dir / f"experiments/{experiment_id}/pr_curves/{algorithm_key}.ui.arrow"
            writer.write_pr_curve(
                ui_path,
                ui_precisions, ui_recalls, ui_thresholds, ui_f1_scores,
                metadata={**metadata, "version": "ui", "downsampled": len(precisions) > 500, "original_points": len(precisions)}
            )

            logger.info(f"Arrow PR曲线数据已保存: Full({len(precisions)}点) + UI({len(ui_precisions)}点)")

        except Exception as e:
            logger.warning(f"保存Arrow PR曲线数据失败（忽略）: {e}")

    def _serialize_frame_matches(self, matches) -> dict:
        """序列化帧匹配"""
        return {"matches": matches.matches, "scores": matches.scores}

    def _serialize_ransac_result(self, ransac) -> dict:
        """序列化RANSAC结果"""
        return {
            "inlier_mask": ransac.inlier_mask,
            "num_iterations": ransac.num_iterations,
            "fundamental_matrix": (
                ransac.fundamental_matrix.tolist()
                if ransac.fundamental_matrix is not None
                else None
            ),
            "essential_matrix": (
                ransac.essential_matrix.tolist()
                if ransac.essential_matrix is not None
                else None
            ),
            "rotation": (
                ransac.rotation.tolist() if ransac.rotation is not None else None
            ),
            "translation": (
                ransac.translation.tolist() if ransac.translation is not None else None
            ),
            "confidence": ransac.confidence,
            "ransac_time": ransac.ransac_time,
            "min_samples": ransac.min_samples,
        }

    def _deserialize_algorithm_metrics(self, data: dict) -> AlgorithmMetrics:
        """反序列化算法指标"""
        from src.models.evaluation import (
            AlgorithmMetrics,
            TrajectoryMetrics,
            MatchingMetrics,
            RANSACMetrics,
        )

        # 处理轨迹指标
        trajectory = None
        if data.get("trajectory"):
            traj_data = data["trajectory"]
            trajectory = TrajectoryMetrics(**traj_data)

        # 处理匹配指标
        matching_data = data.get("matching", {})
        matching = MatchingMetrics(
            avg_matches=matching_data.get("avg_matches", 0.0),
            avg_inliers=matching_data.get("avg_inliers", 0.0),
            avg_inlier_ratio=matching_data.get("avg_inlier_ratio", 0.0),
            avg_match_score=matching_data.get("avg_match_score", 0.0),
            avg_reprojection_error=matching_data.get("avg_reprojection_error", 0.0),
        )

        # 处理RANSAC指标
        ransac_data = data.get("ransac", {})
        ransac = RANSACMetrics(
            avg_iterations=ransac_data.get("avg_iterations", 0.0),
            std_iterations=ransac_data.get("std_iterations", 0.0),
            min_iterations=ransac_data.get("min_iterations", 0),
            max_iterations=ransac_data.get("max_iterations", 0),
            convergence_rate=ransac_data.get("convergence_rate", 0.0),
            avg_inlier_ratio=ransac_data.get("avg_inlier_ratio", 0.0),
            success_rate=ransac_data.get("success_rate", 0.0),
            avg_processing_time_ms=ransac_data.get("avg_processing_time_ms", 0.0),
        )

        return AlgorithmMetrics(
            algorithm_key=data.get("algorithm_key", "unknown"),
            feature_type=data.get("feature_type", "UNKNOWN"),
            ransac_type=data.get("ransac_type", "UNKNOWN"),
            trajectory=trajectory,
            matching=matching,
            ransac=ransac,
            avg_frame_time_ms=data.get("avg_frame_time_ms", 0.0),
            total_time_s=data.get("total_time_s", 0.0),
            fps=data.get("fps", 0.0),
            success_rate=data.get("success_rate", 0.0),
            failure_reasons=data.get("failure_reasons", {}),
            total_frames=data.get("total_frames", 0),
            successful_frames=data.get("successful_frames", 0),
            failed_frames=data.get("failed_frames", 0),
        )

    def _deserialize_frame_result(self, data: dict) -> FrameResult:
        """反序列化帧结果"""
        import numpy as np

        features = None
        if data.get("features"):
            feat_data = data["features"]
            from src.models.frame import FrameFeatures

            features = FrameFeatures(
                keypoints=feat_data["keypoints"],
                descriptors=(
                    np.array(feat_data["descriptors"])
                    if feat_data.get("descriptors")
                    else None
                ),
                scores=feat_data.get("scores"),
            )

        matches = None
        if data.get("matches"):
            match_data = data["matches"]
            from src.models.frame import FrameMatches

            matches = FrameMatches(
                matches=match_data["matches"], scores=match_data["scores"]
            )

        ransac = None
        if data.get("ransac"):
            ransac_data = data["ransac"]
            from src.models.frame import RANSACResult

            ransac = RANSACResult(
                inlier_mask=ransac_data["inlier_mask"],
                num_iterations=ransac_data["num_iterations"],
                fundamental_matrix=(
                    np.array(ransac_data["fundamental_matrix"])
                    if ransac_data["fundamental_matrix"]
                    else None
                ),
                essential_matrix=(
                    np.array(ransac_data["essential_matrix"])
                    if ransac_data["essential_matrix"]
                    else None
                ),
                rotation=(
                    np.array(ransac_data["rotation"])
                    if ransac_data["rotation"]
                    else None
                ),
                translation=(
                    np.array(ransac_data["translation"])
                    if ransac_data["translation"]
                    else None
                ),
                confidence=ransac_data["confidence"],
                ransac_time=ransac_data["ransac_time"],
                min_samples=ransac_data["min_samples"],
            )

        return FrameResult(
            frame_id=data["frame_id"],
            timestamp=data["timestamp"],
            features=features,
            matches=matches,
            ransac=ransac,
            num_matches=data["num_matches"],
            num_inliers=data["num_inliers"],
            inlier_ratio=data["inlier_ratio"],
            estimated_pose=(
                np.array(data["estimated_pose"]) if data["estimated_pose"] else None
            ),
            ground_truth_pose=(
                np.array(data["ground_truth_pose"])
                if data["ground_truth_pose"]
                else None
            ),
            processing_time=data["processing_time"],
            status=data["status"],
            pose_error=data["pose_error"],
            reprojection_errors=data["reprojection_errors"],
            error=data["error"],
        )
