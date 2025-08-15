"""
测试统一序列化的单元测试
"""
import pytest
import numpy as np
from src.api.serializers import UnifiedSerializer
from src.models.frame import FrameResult, FrameFeatures, FrameMatches, RANSACResult
from src.models.evaluation import AlgorithmMetrics, MatchingMetrics, RANSACMetrics, TrajectoryMetrics
from src.models.types import FeatureType, RANSACType


class TestUnifiedSerialization:
    """统一序列化测试类"""

    def test_serialize_algorithm_metrics(self):
        """测试算法指标序列化"""
        # 创建测试数据
        trajectory_metrics = TrajectoryMetrics(
            ate_rmse=0.1, ate_mean=0.08, ate_median=0.07, ate_std=0.02,
            ate_min=0.05, ate_max=0.15, rpe_rmse=0.05, rpe_mean=0.04,
            rpe_median=0.03, rpe_std=0.01, trajectory_length=10.0, num_valid_poses=100
        )
        
        matching_metrics = MatchingMetrics(
            avg_matches=150.0, avg_inliers=120.0, avg_inlier_ratio=0.8,
            avg_match_score=0.9, avg_reprojection_error=0.5
        )
        
        ransac_metrics = RANSACMetrics(
            avg_iterations=100.0, std_iterations=20.0, min_iterations=50, max_iterations=200,
            convergence_rate=0.95, avg_inlier_ratio=0.8, success_rate=0.9, avg_processing_time_ms=10.0
        )
        
        algorithm_metrics = AlgorithmMetrics(
            algorithm_key="SIFT_STANDARD_seq1",
            feature_type=FeatureType.SIFT,
            ransac_type=RANSACType.STANDARD,
            trajectory=trajectory_metrics,
            matching=matching_metrics,
            ransac=ransac_metrics,
            avg_frame_time_ms=50.0,
            total_time_s=5.0,
            fps=20.0,
            success_rate=0.9,
            failure_reasons={"FEATURE_EXTRACTION_FAILED": 5},
            total_frames=100,
            successful_frames=90,
            failed_frames=10
        )

        # 序列化
        serialized = UnifiedSerializer.serialize_algorithm_metrics(algorithm_metrics)

        # 验证结构
        assert serialized["algorithm_key"] == "SIFT_STANDARD_seq1"
        assert serialized["feature_type"] == FeatureType.SIFT
        assert serialized["ransac_type"] == RANSACType.STANDARD
        assert serialized["avg_frame_time_ms"] == 50.0
        assert serialized["total_time_s"] == 5.0
        assert serialized["fps"] == 20.0
        assert serialized["success_rate"] == 0.9
        assert serialized["total_frames"] == 100
        assert serialized["successful_frames"] == 90
        assert serialized["failed_frames"] == 10

        # 验证嵌套对象
        assert serialized["trajectory"]["ate_rmse"] == 0.1
        assert serialized["matching"]["avg_matches"] == 150.0
        assert serialized["ransac"]["avg_iterations"] == 100.0

    def test_serialize_frame_result(self):
        """测试帧结果序列化"""
        # 创建测试数据
        features = FrameFeatures(
            keypoints=[(100.0, 150.0), (200.0, 250.0)],
            descriptors=np.random.rand(2, 128),
            scores=[0.8, 0.9]
        )
        
        matches = FrameMatches(
            matches=[(0, 0), (1, 1)],
            scores=[0.9, 0.8]
        )
        
        ransac_result = RANSACResult(
            inlier_mask=[True, False],
            num_iterations=100,
            fundamental_matrix=np.eye(3),
            essential_matrix=np.eye(3),
            rotation=np.eye(3),
            translation=np.array([0.1, 0.05, 0.0]).reshape(3, 1),
            confidence=0.95,
            ransac_time=0.01,
            min_samples=8
        )
        
        frame_result = FrameResult(
            frame_id=1,
            timestamp=0.1,
            features=features,
            matches=matches,
            ransac=ransac_result,
            num_matches=2,
            num_inliers=1,
            inlier_ratio=0.5,
            estimated_pose=np.eye(4),
            ground_truth_pose=np.eye(4),
            processing_time=0.05,
            status="SUCCESS",
            pose_error=0.1,
            reprojection_errors=[0.5, 2.0],
            error=None
        )

        # 序列化
        serialized = UnifiedSerializer.serialize_frame_result(frame_result)

        # 验证基本字段
        assert serialized["frame_id"] == 1
        assert serialized["timestamp"] == 0.1
        assert serialized["num_matches"] == 2
        assert serialized["num_inliers"] == 1
        assert serialized["inlier_ratio"] == 0.5
        assert serialized["processing_time"] == 0.05
        assert serialized["status"] == "SUCCESS"
        assert serialized["pose_error"] == 0.1
        assert serialized["reprojection_errors"] == [0.5, 2.0]

        # 验证嵌套对象
        assert serialized["features"]["keypoints"] == [(100.0, 150.0), (200.0, 250.0)]
        assert serialized["matches"]["matches"] == [(0, 0), (1, 1)]
        assert serialized["ransac"]["inlier_mask"] == [True, False]
        assert serialized["ransac"]["num_iterations"] == 100

        # 验证numpy数组转换
        assert isinstance(serialized["estimated_pose"], list)
        assert isinstance(serialized["features"]["descriptors"], list)
        assert isinstance(serialized["ransac"]["rotation"], list)

    def test_serialize_frame_result_summary(self):
        """测试帧结果摘要序列化"""
        frame_result = FrameResult(
            frame_id=1,
            timestamp=0.1,
            features=None,  # 摘要版本不包含详细数据
            matches=None,
            ransac=None,
            num_matches=2,
            num_inliers=1,
            inlier_ratio=0.5,
            estimated_pose=None,
            ground_truth_pose=None,
            processing_time=0.05,
            status="SUCCESS",
            pose_error=0.1,
            reprojection_errors=None,
            error=None
        )

        # 序列化摘要
        serialized = UnifiedSerializer.serialize_frame_result_summary(frame_result)

        # 验证只包含摘要字段
        expected_fields = {
            "frame_id", "timestamp", "num_matches", "num_inliers", 
            "inlier_ratio", "processing_time", "status", "pose_error", "error"
        }
        assert set(serialized.keys()) == expected_fields

        # 验证值
        assert serialized["frame_id"] == 1
        assert serialized["num_matches"] == 2
        assert serialized["status"] == "SUCCESS"

    def test_serialize_with_none_values(self):
        """测试包含None值的序列化"""
        # 创建包含None值的算法指标
        algorithm_metrics = AlgorithmMetrics(
            algorithm_key="TEST_ALG",
            feature_type=FeatureType.SIFT,
            ransac_type=RANSACType.STANDARD,
            trajectory=None,  # None值
            matching=MatchingMetrics(
                avg_matches=100.0, avg_inliers=80.0, avg_inlier_ratio=0.8,
                avg_match_score=0.9, avg_reprojection_error=0.5
            ),
            ransac=RANSACMetrics(
                avg_iterations=100.0, std_iterations=20.0, min_iterations=50, max_iterations=200,
                convergence_rate=0.95, avg_inlier_ratio=0.8, success_rate=0.9, avg_processing_time_ms=10.0
            ),
            avg_frame_time_ms=50.0,
            total_time_s=5.0,
            fps=20.0,
            success_rate=0.9,
            failure_reasons={},
            total_frames=100,
            successful_frames=90,
            failed_frames=10
        )

        # 序列化
        serialized = UnifiedSerializer.serialize_algorithm_metrics(algorithm_metrics)

        # 验证None值被正确处理
        assert serialized["trajectory"] is None
        assert serialized["matching"] is not None
        assert serialized["ransac"] is not None

    def test_deserialize_algorithm_metrics(self):
        """测试算法指标反序列化"""
        # 创建序列化数据
        serialized_data = {
            "algorithm_key": "SIFT_STANDARD_seq1",
            "feature_type": FeatureType.SIFT,
            "ransac_type": RANSACType.STANDARD,
            "trajectory": {
                "ate_rmse": 0.1, "ate_mean": 0.08, "ate_median": 0.07, "ate_std": 0.02,
                "ate_min": 0.05, "ate_max": 0.15, "rpe_rmse": 0.05, "rpe_mean": 0.04,
                "rpe_median": 0.03, "rpe_std": 0.01, "trajectory_length": 10.0, "num_valid_poses": 100
            },
            "matching": {
                "avg_matches": 150.0, "avg_inliers": 120.0, "avg_inlier_ratio": 0.8,
                "avg_match_score": 0.9, "avg_reprojection_error": 0.5
            },
            "ransac": {
                "avg_iterations": 100.0, "std_iterations": 20.0, "min_iterations": 50, "max_iterations": 200,
                "convergence_rate": 0.95, "avg_inlier_ratio": 0.8, "success_rate": 0.9, "avg_processing_time_ms": 10.0
            },
            "avg_frame_time_ms": 50.0,
            "total_time_s": 5.0,
            "fps": 20.0,
            "success_rate": 0.9,
            "failure_reasons": {"FEATURE_EXTRACTION_FAILED": 5},
            "total_frames": 100,
            "successful_frames": 90,
            "failed_frames": 10
        }

        # 反序列化
        metrics = UnifiedSerializer.deserialize_algorithm_metrics(serialized_data)

        # 验证结果
        assert isinstance(metrics, AlgorithmMetrics)
        assert metrics.algorithm_key == "SIFT_STANDARD_seq1"
        assert metrics.feature_type == FeatureType.SIFT
        assert metrics.ransac_type == RANSACType.STANDARD
        assert metrics.avg_frame_time_ms == 50.0
        assert metrics.total_frames == 100

        # 验证嵌套对象
        assert metrics.trajectory.ate_rmse == 0.1
        assert metrics.matching.avg_matches == 150.0
        assert metrics.ransac.avg_iterations == 100.0

    def test_serialization_roundtrip(self):
        """测试序列化-反序列化往返"""
        # 创建原始数据
        original_metrics = AlgorithmMetrics(
            algorithm_key="ROUNDTRIP_TEST",
            feature_type=FeatureType.ORB,
            ransac_type=RANSACType.PROSAC,
            trajectory=TrajectoryMetrics(
                ate_rmse=0.2, ate_mean=0.18, ate_median=0.17, ate_std=0.03,
                ate_min=0.15, ate_max=0.25, rpe_rmse=0.1, rpe_mean=0.09,
                rpe_median=0.08, rpe_std=0.02, trajectory_length=20.0, num_valid_poses=200
            ),
            matching=MatchingMetrics(
                avg_matches=200.0, avg_inliers=160.0, avg_inlier_ratio=0.8,
                avg_match_score=0.85, avg_reprojection_error=0.6
            ),
            ransac=RANSACMetrics(
                avg_iterations=120.0, std_iterations=25.0, min_iterations=60, max_iterations=250,
                convergence_rate=0.92, avg_inlier_ratio=0.8, success_rate=0.88, avg_processing_time_ms=12.0
            ),
            avg_frame_time_ms=60.0,
            total_time_s=6.0,
            fps=16.67,
            success_rate=0.88,
            failure_reasons={"MATCHING_FAILED": 3, "RANSAC_FAILED": 2},
            total_frames=200,
            successful_frames=176,
            failed_frames=24
        )

        # 序列化
        serialized = UnifiedSerializer.serialize_algorithm_metrics(original_metrics)
        
        # 反序列化
        deserialized = UnifiedSerializer.deserialize_algorithm_metrics(serialized)

        # 验证往返一致性
        assert deserialized.algorithm_key == original_metrics.algorithm_key
        assert deserialized.feature_type == original_metrics.feature_type
        assert deserialized.ransac_type == original_metrics.ransac_type
        assert deserialized.avg_frame_time_ms == original_metrics.avg_frame_time_ms
        assert deserialized.total_frames == original_metrics.total_frames
        
        # 验证嵌套对象
        assert deserialized.trajectory.ate_rmse == original_metrics.trajectory.ate_rmse
        assert deserialized.matching.avg_matches == original_metrics.matching.avg_matches
        assert deserialized.ransac.avg_iterations == original_metrics.ransac.avg_iterations
