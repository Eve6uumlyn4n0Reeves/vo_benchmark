#
# 功能: 管理整个实验的生命周期, 包括并行执行多个算法运行。
#
from typing import List, Callable, Optional
import logging
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from itertools import product
from src.models.experiment import (
    ExperimentConfig,
    AlgorithmRun,
    ExperimentSummary,
)
from src.models.evaluation import AlgorithmMetrics
from src.models.frame import FrameResult
from src.models.types import FeatureType, RANSACType
from src.storage.experiment import ExperimentStorage
from src.datasets.factory import DatasetFactory
from src.core.features.factory import FeatureFactory
from src.core.ransac.factory import RANSACFactory
from src.pipeline.processor import FrameProcessor
from src.evaluation.metrics import MetricsCalculator
from src.config.manager import get_config

logger = logging.getLogger(__name__)


class ExperimentManager:
    """实验管理器 - 协调整个实验的执行"""

    def __init__(self, config: ExperimentConfig, storage: ExperimentStorage):
        self.config = config
        self.storage = storage
        self.metrics_calculator = MetricsCalculator()

    def run_experiment(
        self, experiment_id: str, progress_callback: Optional[Callable] = None
    ) -> List[AlgorithmMetrics]:
        """
        执行完整的实验:
        1. 生成所有算法运行组合 (AlgorithmRun)。
        2. 使用 concurrent.futures.ThreadPoolExecutor 或 ProcessPoolExecutor 并行执行 run_algorithm。
        3. 收集所有结果, 计算总结, 并存储。
        """
        start_time = time.time()
        logger.info(f"开始执行实验: {experiment_id}")

        try:
            # 1. 生成所有算法运行组合
            algorithm_runs = self._generate_algorithm_runs(experiment_id)
            total_runs = len(algorithm_runs)

            logger.info(f"生成 {total_runs} 个算法运行组合")

            if progress_callback:
                progress_callback(0, f"开始执行 {total_runs} 个算法运行")

            # 2. 并行执行算法运行
            all_metrics = []
            completed_runs = 0

            with ThreadPoolExecutor(max_workers=self.config.parallel_jobs) as executor:
                # 提交所有任务
                future_to_run = {
                    executor.submit(self.run_algorithm, run, progress_callback): run
                    for run in algorithm_runs
                }

                # 收集结果
                for future in as_completed(future_to_run):
                    algorithm_run = future_to_run[future]
                    try:
                        metrics = future.result()
                        all_metrics.append(metrics)
                        completed_runs += 1

                        if progress_callback:
                            progress = completed_runs / total_runs
                            progress_callback(
                                progress,
                                f"完成算法运行 {completed_runs}/{total_runs}: {algorithm_run.algorithm_key}",
                            )

                        logger.info(f"算法运行完成: {algorithm_run.algorithm_key}")

                    except Exception as e:
                        logger.error(
                            f"算法运行失败: {algorithm_run.algorithm_key}, 错误: {e}"
                        )
                        completed_runs += 1

                        if progress_callback:
                            # 统一进度范围为 [0.0, 1.0]
                            progress = completed_runs / total_runs
                            progress_callback(
                                progress,
                                f"算法运行失败 {completed_runs}/{total_runs}: {algorithm_run.algorithm_key}",
                            )

            # 3. 计算实验总结并存储
            summary = self._create_experiment_summary(
                experiment_id, all_metrics, start_time
            )
            self.storage.save_experiment(experiment_id, summary)

            total_time = time.time() - start_time
            logger.info(
                f"实验完成: {experiment_id}, 总耗时: {total_time:.2f}s, "
                f"成功运行: {len(all_metrics)}/{total_runs}"
            )

            if progress_callback:
                # 完成时设置为 1.0
                progress_callback(
                    1.0, f"实验完成，成功运行: {len(all_metrics)}/{total_runs}"
                )

            return all_metrics

        except Exception as e:
            logger.error(f"实验执行失败: {e}")
            if progress_callback:
                # 失败时使用当前进度，不传递越界值
                progress_callback(0.0, f"实验执行失败: {str(e)}")
            raise

    def run_algorithm(
        self, algorithm_run: AlgorithmRun, progress_callback: Optional[Callable] = None
    ) -> AlgorithmMetrics:
        """
        运行一个具体的算法组合 (e.g., SIFT+STANDARD on sequence01):
        1. 初始化数据集、特征提取器等。
        2. 遍历序列中的所有帧。
        3. 调用 FrameProcessor 处理每一对帧。
        4. 收集所有 FrameResult。
        5. 调用评估模块计算最终的 AlgorithmMetrics。
        6. 保存结果到存储。
        """
        logger.info(f"开始算法运行: {algorithm_run.algorithm_key}")
        start_time = time.time()

        try:
            # 1. 初始化组件
            dataset = DatasetFactory.create_dataset(
                self.config.dataset_path, {"sequences": [algorithm_run.sequence]}
            )

            extractor = FeatureFactory.create_extractor(
                algorithm_run.feature_type,
                self.config.feature_params.get(algorithm_run.feature_type.value, {}),
            )

            matcher = FeatureFactory.create_matcher(
                algorithm_run.feature_type,
                {"ratio_threshold": get_config().experiment.default_ratio_threshold},
            )

            estimator = RANSACFactory.create_estimator(
                algorithm_run.ransac_type,
                {
                    "threshold": self.config.ransac_threshold,
                    "confidence": self.config.ransac_confidence,
                    "max_iters": self.config.ransac_max_iters,
                },
            )

            calibration = dataset.get_calibration(algorithm_run.sequence)
            processor = FrameProcessor(extractor, matcher, estimator, calibration)

            # 2. 流式处理序列中的所有帧
            frame_count = dataset.get_frame_count(algorithm_run.sequence)

            # 使用生成器进行流式处理，避免内存溢出
            frame_results_generator = self._process_frames_streaming(
                dataset, processor, algorithm_run, frame_count, progress_callback
            )

            # 3. 流式计算算法指标
            metrics = self.metrics_calculator.calculate_algorithm_metrics_streaming(
                algorithm_run, frame_results_generator, frame_count
            )

            # 4. 保存结果
            self.storage.save_algorithm_result(
                algorithm_run.experiment_id, algorithm_run.algorithm_key, metrics
            )

            # 注意：帧数据已在流式处理过程中保存，无需再次保存

            # 5. 预计算可视化数据（避免查看时现算）
            self._precompute_visualization_data(algorithm_run)

            total_time = time.time() - start_time
            logger.info(
                f"算法运行完成: {algorithm_run.algorithm_key}, 耗时: {total_time:.2f}s"
            )

            return metrics

        except Exception as e:
            logger.error(f"算法运行失败: {algorithm_run.algorithm_key}, 错误: {e}")
            raise

    def _precompute_visualization_data(self, algorithm_run: AlgorithmRun):
        """预计算可视化数据，避免查看时现算
        - 幂等：若已存在预计算结果则跳过
        - 写入失败仅记录日志，不影响主流程
        - 采样与上限：PR最多1000帧、轨迹最多500帧
        """
        try:
            experiment_id = algorithm_run.experiment_id
            algorithm_key = algorithm_run.algorithm_key

            logger.info(f"开始预计算可视化数据: {algorithm_key}")

            # 获取帧结果用于计算（限制最大帧数，避免占用过多内存/I/O）
            frame_results, total = self.storage.get_frame_results(
                experiment_id, algorithm_key, 0, 1000
            )

            if not frame_results:
                logger.warning(f"无帧结果数据，跳过预计算: {algorithm_key}")
                return

            # 1. 预计算PR曲线（幂等：存在则跳过）
            try:
                existing_pr = self.storage.get_pr_curve(experiment_id, algorithm_key)
                if existing_pr is None:
                    pr_data = self._calculate_pr_curve_from_frames(algorithm_key, frame_results)
                    self.storage.save_pr_curve(experiment_id, algorithm_key, pr_data)
                    logger.info(f"PR曲线预计算完成: {algorithm_key}")
                else:
                    logger.info(f"检测到已存在的PR曲线，跳过: {algorithm_key}")
            except Exception as e:
                logger.error(f"PR曲线预计算失败: {e}")

            # 2. 预计算轨迹数据（幂等：存在则跳过）
            try:
                existing_traj = self.storage.get_trajectory(experiment_id, algorithm_key)
                if existing_traj is None:
                    trajectory_data = self._build_trajectory_from_frames(
                        experiment_id, algorithm_key, frame_results[:500], algorithm_run.config
                    )
                    self.storage.save_trajectory(experiment_id, algorithm_key, trajectory_data)
                    logger.info(f"轨迹数据预计算完成: {algorithm_key}")
                else:
                    logger.info(f"检测到已存在的轨迹数据，跳过: {algorithm_key}")
            except Exception as e:
                logger.error(f"轨迹数据预计算失败: {e}")

            # 3. 预计算帧结果统计（幂等：存在则跳过）
            try:
                existing_summary = self.storage.get_frame_summary(experiment_id, algorithm_key)
                if existing_summary is None:
                    summary = self._calculate_frame_summary(frame_results)
                    self.storage.save_frame_summary(experiment_id, algorithm_key, summary)
                    logger.info(f"帧结果统计预计算完成: {algorithm_key}")
                else:
                    logger.info(f"检测到已存在的帧结果统计，跳过: {algorithm_key}")
            except Exception as e:
                logger.error(f"帧结果统计预计算失败: {e}")

        except Exception as e:
            logger.error(f"预计算可视化数据失败: {algorithm_key}, 错误: {e}")
            # 不抛出异常，避免影响主实验流程

    def _calculate_pr_curve_from_frames(self, algorithm_key: str, frame_results: list) -> dict:
        """从帧结果计算PR曲线（复用ResultService的逻辑）"""
        from src.api.services.result import ResultService
        result_service = ResultService()
        return result_service._calculate_pr_curve_from_frames(algorithm_key, frame_results)

    def _build_trajectory_from_frames(self, experiment_id: str, algorithm_key: str, frame_results: list, config: any) -> dict:
        """从帧结果构建轨迹数据（复用ResultService的逻辑）"""
        from src.api.services.result import ResultService
        result_service = ResultService()
        return result_service._build_trajectory_from_frames(
            experiment_id, algorithm_key, frame_results, config, False
        )

    def _calculate_frame_summary(self, frame_results: list) -> dict:
        """计算帧结果统计摘要"""
        if not frame_results:
            return {
                "total_frames": 0,
                "avg_matches": 0.0,
                "avg_inliers": 0.0,
                "avg_inlier_ratio": 0.0
            }

        total_matches = sum(len(f.matches) if hasattr(f, 'matches') and f.matches else 0 for f in frame_results)
        total_inliers = sum(f.inliers if hasattr(f, 'inliers') and f.inliers else 0 for f in frame_results)

        avg_matches = total_matches / len(frame_results) if frame_results else 0
        avg_inliers = total_inliers / len(frame_results) if frame_results else 0
        avg_inlier_ratio = (total_inliers / total_matches) if total_matches > 0 else 0

        return {
            "total_frames": len(frame_results),
            "avg_matches": float(avg_matches),
            "avg_inliers": float(avg_inliers),
            "avg_inlier_ratio": float(avg_inlier_ratio)
        }

    def _process_frames_streaming(
        self, dataset, processor, algorithm_run, frame_count, progress_callback
    ):
        """流式处理帧数据，避免内存溢出"""
        for frame_id in range(frame_count):
            try:
                # 加载图像和真值位姿
                image = dataset.get_image(algorithm_run.sequence, frame_id)
                ground_truth = dataset.get_ground_truth_pose(
                    algorithm_run.sequence, frame_id
                )

                # 处理帧
                # 时间戳：优先从数据集提供，退化为 frame_id * 0.1
                try:
                    get_ts = getattr(dataset, "get_timestamp", None)
                    timestamp = (
                        float(get_ts(algorithm_run.sequence, frame_id))
                        if callable(get_ts)
                        else (frame_id * 0.1)
                    )
                except Exception:
                    timestamp = frame_id * 0.1

                result = processor.process_single_frame(
                    image, frame_id, timestamp, ground_truth
                )

                # 立即保存帧结果到磁盘（如果启用）
                if self.config.save_frame_data:
                    self.storage.save_frame_result(
                        algorithm_run.experiment_id,
                        algorithm_run.algorithm_key,
                        frame_id,
                        result,
                    )

                # 更新进度
                if progress_callback and frame_id % 10 == 0:
                    # 统一进度范围为 [0, 1]
                    progress = (frame_id / frame_count) if frame_count else 0.0
                    progress_callback(
                        progress,
                        f"处理帧 {frame_id}/{frame_count} - {algorithm_run.algorithm_key}",
                    )

                yield result

            except Exception as e:
                logger.warning(f"处理帧 {frame_id} 失败: {e}")
                # 创建失败的帧结果（统一使用 FEATURE_EXTRACTION_FAILED，详见 FrameResult 校验）
                failed_result = FrameResult(
                    frame_id=frame_id,
                    timestamp=frame_id * 0.1,
                    features=None,
                    matches=None,
                    ransac=None,
                    num_matches=0,
                    num_inliers=0,
                    inlier_ratio=0.0,
                    estimated_pose=None,
                    ground_truth_pose=None,
                    processing_time=0.0,
                    status="FEATURE_EXTRACTION_FAILED",
                    pose_error=None,
                    reprojection_errors=None,
                    error=str(e),
                )

                # 立即保存失败的帧结果到磁盘（如果启用）
                if self.config.save_frame_data:
                    self.storage.save_frame_result(
                        algorithm_run.experiment_id,
                        algorithm_run.algorithm_key,
                        frame_id,
                        failed_result,
                    )

                yield failed_result

    def _generate_algorithm_runs(self, experiment_id: str) -> List[AlgorithmRun]:
        """生成所有算法运行组合"""
        runs = []

        for feature_type, ransac_type, sequence in product(
            self.config.feature_types, self.config.ransac_types, self.config.sequences
        ):
            for run_id in range(self.config.num_runs):
                algorithm_key = (
                    f"{feature_type.value}_{ransac_type.value}_{sequence}_{run_id}"
                )

                run = AlgorithmRun(
                    experiment_id=experiment_id,
                    algorithm_key=algorithm_key,
                    feature_type=feature_type,
                    ransac_type=ransac_type,
                    sequence=sequence,
                    run_number=run_id,
                    random_seed=(
                        self.config.random_seed + run_id
                        if self.config.random_seed
                        else None
                    ),
                )
                runs.append(run)

        return runs

    def _create_experiment_summary(
        self, experiment_id: str, all_metrics: List[AlgorithmMetrics], start_time: float
    ) -> ExperimentSummary:
        """创建实验总结"""
        total_time = time.time() - start_time

        # 统计成功和失败的运行
        successful_runs = len([m for m in all_metrics if m.success_rate > 0])
        failed_runs = len(all_metrics) - successful_runs

        # 收集测试的算法和序列
        algorithms_tested = list(
            set([f"{m.feature_type}_{m.ransac_type}" for m in all_metrics])
        )

        sequences_processed = list(
            set(
                [
                    m.algorithm_key.split("_")[2]
                    for m in all_metrics  # 从algorithm_key提取序列名
                ]
            )
        )

        summary = ExperimentSummary(
            experiment_id=experiment_id,
            timestamp=datetime.now().isoformat(),
            config=self.config,
            total_runs=len(all_metrics),
            successful_runs=successful_runs,
            failed_runs=failed_runs,
            algorithms_tested=algorithms_tested,
            sequences_processed=sequences_processed,
        )

        logger.info(
            f"实验总结: 总运行数={summary.total_runs}, "
            f"成功={summary.successful_runs}, 失败={summary.failed_runs}"
        )

        return summary
