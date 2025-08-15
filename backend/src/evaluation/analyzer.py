#
# 功能: 定义实验结果分析函数。
#
from typing import List, Dict, Any, Optional
import numpy as np
import logging
from src.models.evaluation import AlgorithmMetrics
from src.storage.experiment import ExperimentStorage

logger = logging.getLogger(__name__)


class MetricsAnalyzer:
    """指标分析器 - 分析和比较实验结果"""

    def __init__(self):
        """初始化分析器"""
        pass

    def analyze_experiment(
        self, experiment_id: str, storage: ExperimentStorage
    ) -> Dict[str, Any]:
        """
        分析单个实验的结果

        Args:
            experiment_id: 实验ID
            storage: 存储接口

        Returns:
            实验分析结果
        """
        try:
            # 获取实验信息
            experiment = storage.get_experiment(experiment_id)
            if not experiment:
                raise ValueError(f"实验不存在: {experiment_id}")

            # 获取所有算法结果
            algorithm_results = storage.get_all_algorithm_results(experiment_id)

            if not algorithm_results:
                logger.warning(f"实验 {experiment_id} 没有算法结果")
                return {"experiment_id": experiment_id, "analysis": "无结果数据"}

            # 基本统计
            analysis = {
                "experiment_id": experiment_id,
                "experiment_name": experiment.config.name,
                "total_algorithms": len(algorithm_results),
                "algorithms_tested": [
                    result.algorithm_key for result in algorithm_results
                ],
                "summary": self._compute_experiment_summary(algorithm_results),
                "algorithm_comparison": self.compare_algorithms(algorithm_results),
                "best_performers": self._find_best_performers(algorithm_results),
                "performance_analysis": self._analyze_performance(algorithm_results),
                "failure_analysis": self._analyze_failures(algorithm_results),
            }

            return analysis

        except Exception as e:
            logger.error(f"分析实验失败: {e}")
            return {"experiment_id": experiment_id, "error": str(e)}

    def compare_algorithms(self, metrics: List[AlgorithmMetrics]) -> Dict[str, Any]:
        """
        比较多个算法的性能

        Args:
            metrics: 算法指标列表

        Returns:
            算法比较结果
        """
        if not metrics:
            return {"error": "没有算法指标数据"}

        try:
            algorithms: List[str] = [m.algorithm_key for m in metrics]
            comparison: Dict[str, Any] = {
                "algorithms": algorithms,
                "feature_types": list({m.feature_type for m in metrics}),
                "ransac_types": list({m.ransac_type for m in metrics}),
                "performance_metrics": {},
                "rankings": {},
                "statistical_summary": {},
            }

            # 收集各种指标
            metrics_data = {
                "success_rate": [m.success_rate for m in metrics],
                "avg_frame_time_ms": [m.avg_frame_time_ms for m in metrics],
                "fps": [m.fps for m in metrics],
                "avg_matches": [m.matching.avg_matches for m in metrics],
                "avg_inliers": [m.matching.avg_inliers for m in metrics],
                "avg_inlier_ratio": [m.matching.avg_inlier_ratio for m in metrics],
                "ransac_success_rate": [m.ransac.success_rate for m in metrics],
                "ransac_avg_iterations": [m.ransac.avg_iterations for m in metrics],
            }

            # 添加轨迹指标（如果可用）
            trajectory_metrics = [
                m.trajectory for m in metrics if m.trajectory is not None
            ]
            if trajectory_metrics:
                metrics_data.update(
                    {
                        "ate_rmse": [t.ate_rmse for t in trajectory_metrics],
                        "ate_mean": [t.ate_mean for t in trajectory_metrics],
                        "rpe_rmse": [t.rpe_rmse for t in trajectory_metrics],
                        "trajectory_length": [
                            t.trajectory_length for t in trajectory_metrics
                        ],
                    }
                )

            # 计算统计摘要
            for metric_name, values in metrics_data.items():
                if values and all(v is not None for v in values):
                    statistical_summary: Dict[str, Any] = comparison["statistical_summary"]
                    statistical_summary[metric_name] = {
                        "mean": float(np.mean(values)),
                        "std": float(np.std(values)),
                        "min": float(np.min(values)),
                        "max": float(np.max(values)),
                        "median": float(np.median(values)),
                    }

            # 计算排名
            for metric_name, values in metrics_data.items():
                if values and all(v is not None for v in values):
                    # 对于时间相关指标，越小越好；对于其他指标，越大越好
                    reverse = metric_name not in [
                        "avg_frame_time_ms",
                        "ate_rmse",
                        "ate_mean",
                        "rpe_rmse",
                    ]

                    sorted_indices = np.argsort(values)
                    if reverse:
                        sorted_indices = sorted_indices[::-1]

                    ranking = []
                    for i, idx in enumerate(sorted_indices):
                        ranking.append(
                            {
                                "rank": i + 1,
                                "algorithm": algorithms[idx],
                                "value": values[idx],
                            }
                        )

                    rankings: Dict[str, Any] = comparison["rankings"]
                    rankings[metric_name] = ranking

            return comparison

        except Exception as e:
            logger.error(f"比较算法失败: {e}")
            return {"error": str(e)}

    def _compute_experiment_summary(
        self, algorithm_results: List[AlgorithmMetrics]
    ) -> Dict[str, Any]:
        """计算实验摘要统计"""
        if not algorithm_results:
            return {}

        try:
            total_frames = sum(m.total_frames for m in algorithm_results)
            successful_frames = sum(m.successful_frames for m in algorithm_results)
            total_time = sum(m.total_time_s for m in algorithm_results)

            return {
                "total_algorithms": len(algorithm_results),
                "total_frames_processed": total_frames,
                "successful_frames": successful_frames,
                "overall_success_rate": (
                    successful_frames / total_frames if total_frames > 0 else 0.0
                ),
                "total_processing_time_s": total_time,
                "average_fps": np.mean([m.fps for m in algorithm_results if m.fps > 0]),
                "feature_types_tested": list(
                    set(m.feature_type for m in algorithm_results)
                ),
                "ransac_types_tested": list(
                    set(m.ransac_type for m in algorithm_results)
                ),
            }

        except Exception as e:
            logger.error(f"计算实验摘要失败: {e}")
            return {"error": str(e)}

    def _find_best_performers(
        self, algorithm_results: List[AlgorithmMetrics]
    ) -> Dict[str, Any]:
        """找到各个指标的最佳表现者"""
        if not algorithm_results:
            return {}

        try:
            best_performers = {}

            # 最高成功率
            best_success_rate = max(algorithm_results, key=lambda x: x.success_rate)
            best_performers["highest_success_rate"] = {
                "algorithm": best_success_rate.algorithm_key,
                "value": best_success_rate.success_rate,
            }

            # 最快处理速度
            best_fps = max(algorithm_results, key=lambda x: x.fps)
            best_performers["highest_fps"] = {
                "algorithm": best_fps.algorithm_key,
                "value": best_fps.fps,
            }

            # 最多匹配点
            best_matches = max(algorithm_results, key=lambda x: x.matching.avg_matches)
            best_performers["most_matches"] = {
                "algorithm": best_matches.algorithm_key,
                "value": best_matches.matching.avg_matches,
            }

            # 最高内点比例
            best_inlier_ratio = max(
                algorithm_results, key=lambda x: x.matching.avg_inlier_ratio
            )
            best_performers["highest_inlier_ratio"] = {
                "algorithm": best_inlier_ratio.algorithm_key,
                "value": best_inlier_ratio.matching.avg_inlier_ratio,
            }

            # 最佳轨迹精度（如果有轨迹数据）
            trajectory_results = [
                m for m in algorithm_results if m.trajectory is not None
            ]
            if trajectory_results:
                best_trajectory = min(
                    trajectory_results, key=lambda x: x.trajectory.ate_rmse if x.trajectory else float('inf')
                )
                if best_trajectory.trajectory is not None:
                    best_performers["best_trajectory_accuracy"] = {
                        "algorithm": best_trajectory.algorithm_key,
                        "ate_rmse": best_trajectory.trajectory.ate_rmse,
                    }

            return best_performers

        except Exception as e:
            logger.error(f"寻找最佳表现者失败: {e}")
            return {"error": str(e)}

    def _analyze_performance(
        self, algorithm_results: List[AlgorithmMetrics]
    ) -> Dict[str, Any]:
        """分析性能特征"""
        if not algorithm_results:
            return {}

        try:
            analysis = {}

            # 按特征类型分组分析
            feature_groups: Dict[str, List[AlgorithmMetrics]] = {}
            for result in algorithm_results:
                feature_type = result.feature_type
                if feature_type not in feature_groups:
                    feature_groups[feature_type] = []
                feature_groups[feature_type].append(result)

            feature_analysis = {}
            for feature_type, results in feature_groups.items():
                feature_analysis[feature_type] = {
                    "count": len(results),
                    "avg_success_rate": np.mean([r.success_rate for r in results]),
                    "avg_fps": np.mean([r.fps for r in results]),
                    "avg_matches": np.mean([r.matching.avg_matches for r in results]),
                }

            analysis["by_feature_type"] = feature_analysis

            # 按RANSAC类型分组分析
            ransac_groups: Dict[str, List[AlgorithmMetrics]] = {}
            for result in algorithm_results:
                ransac_type = result.ransac_type
                if ransac_type not in ransac_groups:
                    ransac_groups[ransac_type] = []
                ransac_groups[ransac_type].append(result)

            ransac_analysis = {}
            for ransac_type, results in ransac_groups.items():
                ransac_analysis[ransac_type] = {
                    "count": len(results),
                    "avg_success_rate": np.mean([r.success_rate for r in results]),
                    "avg_iterations": np.mean(
                        [r.ransac.avg_iterations for r in results]
                    ),
                    "avg_convergence_rate": np.mean(
                        [r.ransac.convergence_rate for r in results]
                    ),
                }

            analysis["by_ransac_type"] = ransac_analysis

            return analysis

        except Exception as e:
            logger.error(f"性能分析失败: {e}")
            return {"error": str(e)}

    def _analyze_failures(
        self, algorithm_results: List[AlgorithmMetrics]
    ) -> Dict[str, Any]:
        """分析失败模式"""
        if not algorithm_results:
            return {}

        try:
            # 收集所有失败原因
            all_failures = {}
            total_failures = 0

            for result in algorithm_results:
                for reason, count in result.failure_reasons.items():
                    if reason not in all_failures:
                        all_failures[reason] = 0
                    all_failures[reason] += count
                    total_failures += count

            # 计算失败原因的百分比
            failure_percentages = {}
            for reason, count in all_failures.items():
                failure_percentages[reason] = (
                    (count / total_failures * 100) if total_failures > 0 else 0
                )

            # 按算法分析失败率
            algorithm_failure_rates = {}
            for result in algorithm_results:
                failure_rate = (
                    result.failed_frames / result.total_frames
                    if result.total_frames > 0
                    else 0
                )
                algorithm_failure_rates[result.algorithm_key] = failure_rate

            return {
                "total_failures": total_failures,
                "failure_reasons": all_failures,
                "failure_percentages": failure_percentages,
                "algorithm_failure_rates": algorithm_failure_rates,
                "most_common_failure": (
                    max(all_failures.items(), key=lambda x: x[1])[0]
                    if all_failures
                    else None
                ),
            }

        except Exception as e:
            logger.error(f"失败分析失败: {e}")
            return {"error": str(e)}
