"""
统一的序列化工具模块

提供一致的序列化/反序列化方法，确保API响应和存储层使用相同的序列化逻辑。
"""
from typing import Dict, Any, Optional
import numpy as np
from src.models.frame import FrameResult, FrameFeatures, FrameMatches, RANSACResult
from src.models.evaluation import AlgorithmMetrics, MatchingMetrics, RANSACMetrics, TrajectoryMetrics


class UnifiedSerializer:
    """统一序列化器"""

    @staticmethod
    def serialize_algorithm_metrics(metrics: AlgorithmMetrics) -> Dict[str, Any]:
        """序列化算法指标"""
        return {
            "algorithm_key": metrics.algorithm_key,
            "feature_type": metrics.feature_type,
            "ransac_type": metrics.ransac_type,
            "trajectory": (
                UnifiedSerializer.serialize_trajectory_metrics(metrics.trajectory)
                if metrics.trajectory
                else None
            ),
            "matching": UnifiedSerializer.serialize_matching_metrics(metrics.matching),
            "ransac": UnifiedSerializer.serialize_ransac_metrics(metrics.ransac),
            "avg_frame_time_ms": metrics.avg_frame_time_ms,
            "total_time_s": metrics.total_time_s,
            "fps": metrics.fps,
            "success_rate": metrics.success_rate,
            "failure_reasons": metrics.failure_reasons,
            "total_frames": metrics.total_frames,
            "successful_frames": metrics.successful_frames,
            "failed_frames": metrics.failed_frames,
            "metrics_schema_version": getattr(metrics, 'metrics_schema_version', '1.1'),
            "source_flags": getattr(metrics, 'source_flags', {}) or {},

        }

    @staticmethod
    def serialize_trajectory_metrics(metrics: TrajectoryMetrics) -> Dict[str, Any]:
        """序列化轨迹指标"""
        return {
            "ate_rmse": metrics.ate_rmse,
            "ate_mean": metrics.ate_mean,
            "ate_median": metrics.ate_median,
            "ate_std": metrics.ate_std,
            "ate_min": metrics.ate_min,
            "ate_max": metrics.ate_max,
            "rpe_rmse": metrics.rpe_rmse,
            "rpe_mean": metrics.rpe_mean,
            "rpe_median": metrics.rpe_median,
            "rpe_std": metrics.rpe_std,
            "trajectory_length": metrics.trajectory_length,
            "num_valid_poses": metrics.num_valid_poses,
        }

    @staticmethod
    def serialize_matching_metrics(metrics: MatchingMetrics) -> Dict[str, Any]:
        """序列化匹配指标"""
        return {
            "avg_matches": metrics.avg_matches,
            "avg_inliers": metrics.avg_inliers,
            "avg_inlier_ratio": metrics.avg_inlier_ratio,
            "avg_match_score": metrics.avg_match_score,
            "avg_reprojection_error": metrics.avg_reprojection_error,
        }

    @staticmethod
    def serialize_ransac_metrics(metrics: RANSACMetrics) -> Dict[str, Any]:
        """序列化RANSAC指标"""
        return {
            "avg_iterations": metrics.avg_iterations,
            "std_iterations": metrics.std_iterations,
            "min_iterations": metrics.min_iterations,
            "max_iterations": metrics.max_iterations,
            "convergence_rate": metrics.convergence_rate,
            "avg_inlier_ratio": metrics.avg_inlier_ratio,
            "success_rate": metrics.success_rate,
            "avg_processing_time_ms": metrics.avg_processing_time_ms,
        }

    @staticmethod
    def serialize_frame_result(frame: FrameResult) -> Dict[str, Any]:
        """序列化帧结果"""
        return {
            "frame_id": frame.frame_id,
            "timestamp": frame.timestamp,
            "features": (
                UnifiedSerializer.serialize_frame_features(frame.features)
                if frame.features
                else None
            ),
            "matches": (
                UnifiedSerializer.serialize_frame_matches(frame.matches)
                if frame.matches
                else None
            ),
            "ransac": (
                UnifiedSerializer.serialize_ransac_result(frame.ransac)
                if frame.ransac
                else None
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

    @staticmethod
    def serialize_frame_features(features: FrameFeatures) -> Dict[str, Any]:
        """序列化帧特征"""
        return {
            "keypoints": features.keypoints,
            "descriptors": (
                features.descriptors.tolist()
                if features.descriptors is not None
                else None
            ),
            "scores": features.scores,
        }

    @staticmethod
    def serialize_frame_matches(matches: FrameMatches) -> Dict[str, Any]:
        """序列化帧匹配"""
        return {
            "matches": matches.matches,
            "scores": matches.scores
        }

    @staticmethod
    def serialize_ransac_result(ransac: RANSACResult) -> Dict[str, Any]:
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

    @staticmethod
    def serialize_frame_result_summary(frame: FrameResult) -> Dict[str, Any]:
        """序列化帧结果摘要（用于API响应，不包含详细的features/matches/ransac）"""
        return {
            "frame_id": frame.frame_id,
            "timestamp": frame.timestamp,
            "num_matches": frame.num_matches,
            "num_inliers": frame.num_inliers,
            "inlier_ratio": frame.inlier_ratio,
            "processing_time": frame.processing_time,
            "status": frame.status,
            "pose_error": frame.pose_error,
            "error": frame.error,
        }

    # 反序列化方法（用于存储层）
    @staticmethod
    def deserialize_algorithm_metrics(data: Dict[str, Any]) -> AlgorithmMetrics:
        """反序列化算法指标"""
        trajectory = None
        if data.get("trajectory"):
            trajectory = UnifiedSerializer.deserialize_trajectory_metrics(data["trajectory"])

        matching = UnifiedSerializer.deserialize_matching_metrics(data["matching"])
        ransac = UnifiedSerializer.deserialize_ransac_metrics(data["ransac"])

        return AlgorithmMetrics(
            algorithm_key=data["algorithm_key"],
            feature_type=data["feature_type"],
            ransac_type=data["ransac_type"],
            trajectory=trajectory,
            matching=matching,
            ransac=ransac,
            avg_frame_time_ms=data["avg_frame_time_ms"],
            total_time_s=data["total_time_s"],
            fps=data["fps"],
            success_rate=data["success_rate"],
            failure_reasons=data["failure_reasons"],
            total_frames=data["total_frames"],
            successful_frames=data["successful_frames"],
            failed_frames=data["failed_frames"],
            metrics_schema_version=data.get("metrics_schema_version", "1.1"),
            source_flags=data.get("source_flags", {}) or {},

        )

    @staticmethod
    def deserialize_trajectory_metrics(data: Dict[str, Any]) -> TrajectoryMetrics:
        """反序列化轨迹指标"""
        return TrajectoryMetrics(
            ate_rmse=data["ate_rmse"],
            ate_mean=data["ate_mean"],
            ate_median=data["ate_median"],
            ate_std=data["ate_std"],
            ate_min=data["ate_min"],
            ate_max=data["ate_max"],
            rpe_rmse=data["rpe_rmse"],
            rpe_mean=data["rpe_mean"],
            rpe_median=data["rpe_median"],
            rpe_std=data["rpe_std"],
            trajectory_length=data["trajectory_length"],
            num_valid_poses=data["num_valid_poses"],
        )

    @staticmethod
    def deserialize_matching_metrics(data: Dict[str, Any]) -> MatchingMetrics:
        """反序列化匹配指标"""
        return MatchingMetrics(
            avg_matches=data["avg_matches"],
            avg_inliers=data["avg_inliers"],
            avg_inlier_ratio=data["avg_inlier_ratio"],
            avg_match_score=data["avg_match_score"],
            avg_reprojection_error=data["avg_reprojection_error"],
        )

    @staticmethod
    def deserialize_ransac_metrics(data: Dict[str, Any]) -> RANSACMetrics:
        """反序列化RANSAC指标"""
        return RANSACMetrics(
            avg_iterations=data.get("avg_iterations", 0.0),
            std_iterations=data.get("std_iterations", 0.0),
            min_iterations=data.get("min_iterations", 0),
            max_iterations=data.get("max_iterations", 0),
            convergence_rate=data.get("convergence_rate", 0.0),
            avg_inlier_ratio=data.get("avg_inlier_ratio", 0.0),
            success_rate=data.get("success_rate", 0.0),
            avg_processing_time_ms=data.get("avg_processing_time_ms", 0.0),
        )
