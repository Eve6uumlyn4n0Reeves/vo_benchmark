"""
测试指标计算的单元测试
"""
import pytest
import numpy as np
from unittest.mock import Mock
from src.evaluation.metrics import MetricsCalculator
from src.models.frame import FrameResult, FrameFeatures, FrameMatches, RANSACResult
from src.models.experiment import AlgorithmRun
from src.models.types import FeatureType, RANSACType


class TestMetricsCalculation:
    """指标计算测试类"""

    def setup_method(self):
        """设置测试环境"""
        self.calculator = MetricsCalculator()

    def create_mock_frame_result(self, frame_id: int, success: bool = True, 
                                 num_iterations: int = 100, ransac_time: float = 0.01,
                                 confidence: float = 0.95, inlier_ratio: float = 0.8) -> FrameResult:
        """创建模拟的帧结果"""
        if success:
            ransac_result = RANSACResult(
                inlier_mask=[True] * 10 + [False] * 2,  # 10个内点，2个外点
                num_iterations=num_iterations,
                fundamental_matrix=np.eye(3),
                essential_matrix=np.eye(3),
                rotation=np.eye(3),
                translation=np.array([0.1, 0.05, 0.0]).reshape(3, 1),
                confidence=confidence,
                ransac_time=ransac_time,
                min_samples=8
            )
            
            return FrameResult(
                frame_id=frame_id,
                timestamp=frame_id * 0.1,
                features=FrameFeatures(
                    keypoints=[(100.0 + i, 150.0 + i) for i in range(12)],
                    descriptors=np.random.rand(12, 128),
                    scores=[0.8] * 12
                ),
                matches=FrameMatches(
                    matches=[(i, i) for i in range(12)],
                    scores=[0.9] * 12
                ),
                ransac=ransac_result,
                num_matches=12,
                num_inliers=10,
                inlier_ratio=inlier_ratio,
                estimated_pose=np.eye(4),
                ground_truth_pose=np.eye(4),
                processing_time=0.05,
                status="SUCCESS",
                pose_error=0.1,
                reprojection_errors=[0.5] * 10 + [2.0] * 2,
                error=None
            )
        else:
            return FrameResult(
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
                processing_time=0.02,
                status="FEATURE_EXTRACTION_FAILED",
                pose_error=None,
                reprojection_errors=None,
                error="Feature extraction failed"
            )

    def test_compute_ransac_metrics_with_real_data(self):
        """测试基于真实数据的RANSAC指标计算"""
        # 创建测试数据
        frame_results = [
            self.create_mock_frame_result(0, True, 80, 0.008, 0.95, 0.8),
            self.create_mock_frame_result(1, True, 120, 0.012, 0.90, 0.7),
            self.create_mock_frame_result(2, True, 100, 0.010, 0.85, 0.75),
            self.create_mock_frame_result(3, False),  # 失败的帧
        ]

        # 计算指标
        metrics = self.calculator.compute_ransac_metrics(frame_results)

        # 验证结果
        assert metrics.avg_iterations == 100.0  # (80 + 120 + 100) / 3
        assert metrics.std_iterations == pytest.approx(16.33, rel=1e-2)  # std([80, 120, 100])
        assert metrics.min_iterations == 80
        assert metrics.max_iterations == 120
        assert metrics.avg_inlier_ratio == pytest.approx(0.75, rel=1e-2)  # (0.8 + 0.7 + 0.75) / 3
        assert metrics.avg_processing_time_ms == pytest.approx(10.0, rel=1e-2)  # (8 + 12 + 10) ms / 3
        assert metrics.convergence_rate == 1.0  # 3/3 成功（confidence > 0.5）
        assert metrics.success_rate == 0.75  # 3/4 帧成功

    def test_streaming_ransac_metrics_calculation(self):
        """测试流式RANSAC指标计算"""
        # 创建模拟的算法运行
        algorithm_run = AlgorithmRun(
            experiment_id="test_exp",
            algorithm_key="SIFT_STANDARD_seq1",
            feature_type=FeatureType.SIFT,
            ransac_type=RANSACType.STANDARD,
            sequence="seq1",
            run_number=1
        )

        # 创建测试数据生成器
        def frame_generator():
            yield self.create_mock_frame_result(0, True, 90, 0.009, 0.95, 0.8)
            yield self.create_mock_frame_result(1, True, 110, 0.011, 0.88, 0.7)
            yield self.create_mock_frame_result(2, True, 95, 0.010, 0.92, 0.75)

        # 计算流式指标
        metrics = self.calculator.calculate_algorithm_metrics_streaming(
            algorithm_run, frame_generator(), 3
        )

        # 验证RANSAC指标
        ransac_metrics = metrics.ransac
        assert ransac_metrics.avg_iterations == pytest.approx(98.33, rel=1e-2)  # (90 + 110 + 95) / 3
        assert ransac_metrics.min_iterations == 90
        assert ransac_metrics.max_iterations == 110
        assert ransac_metrics.avg_inlier_ratio == pytest.approx(0.75, rel=1e-2)  # (0.8 + 0.7 + 0.75) / 3
        assert ransac_metrics.avg_processing_time_ms == pytest.approx(10.0, rel=1e-2)  # (9 + 11 + 10) ms / 3
        assert ransac_metrics.convergence_rate == 1.0  # 3/3 成功
        assert ransac_metrics.success_rate == 1.0  # 3/3 成功

    def test_ransac_metrics_with_empty_data(self):
        """测试空数据的RANSAC指标计算"""
        frame_results = []
        metrics = self.calculator.compute_ransac_metrics(frame_results)

        # 验证所有指标都为0
        assert metrics.avg_iterations == 0.0
        assert metrics.std_iterations == 0.0
        assert metrics.min_iterations == 0
        assert metrics.max_iterations == 0
        assert metrics.convergence_rate == 0.0
        assert metrics.avg_inlier_ratio == 0.0
        assert metrics.success_rate == 0.0
        assert metrics.avg_processing_time_ms == 0.0

    def test_ransac_metrics_with_failed_frames_only(self):
        """测试只有失败帧的RANSAC指标计算"""
        frame_results = [
            self.create_mock_frame_result(0, False),
            self.create_mock_frame_result(1, False),
        ]

        metrics = self.calculator.compute_ransac_metrics(frame_results)

        # 验证所有指标都为0
        assert metrics.avg_iterations == 0.0
        assert metrics.std_iterations == 0.0
        assert metrics.min_iterations == 0
        assert metrics.max_iterations == 0
        assert metrics.convergence_rate == 0.0
        assert metrics.avg_inlier_ratio == 0.0
        assert metrics.success_rate == 0.0
        assert metrics.avg_processing_time_ms == 0.0

    def test_ransac_metrics_with_mixed_confidence(self):
        """测试混合置信度的RANSAC指标计算"""
        frame_results = [
            self.create_mock_frame_result(0, True, 100, 0.01, 0.8, 0.7),  # 高置信度
            self.create_mock_frame_result(1, True, 150, 0.015, 0.3, 0.6),  # 低置信度
            self.create_mock_frame_result(2, True, 80, 0.008, 0.9, 0.8),   # 高置信度
        ]

        metrics = self.calculator.compute_ransac_metrics(frame_results)

        # 验证收敛率和成功率
        assert metrics.convergence_rate == pytest.approx(0.67, rel=1e-2)  # 2/3 (confidence > 0.5)
        assert metrics.success_rate == pytest.approx(0.67, rel=1e-2)  # 2/3 帧成功
        assert metrics.avg_iterations == pytest.approx(110.0, rel=1e-2)  # (100 + 150 + 80) / 3

    def test_streaming_vs_non_streaming_consistency(self):
        """测试流式和非流式版本的一致性"""
        # 创建相同的测试数据
        frame_results = [
            self.create_mock_frame_result(0, True, 100, 0.01, 0.95, 0.8),
            self.create_mock_frame_result(1, True, 120, 0.012, 0.90, 0.7),
            self.create_mock_frame_result(2, True, 80, 0.008, 0.85, 0.75),
        ]

        # 非流式计算
        non_streaming_metrics = self.calculator.compute_ransac_metrics(frame_results)

        # 流式计算
        algorithm_run = AlgorithmRun(
            experiment_id="test_exp",
            algorithm_key="SIFT_STANDARD_seq1",
            feature_type=FeatureType.SIFT,
            ransac_type=RANSACType.STANDARD,
            sequence="seq1",
            run_number=1
        )

        def frame_generator():
            for frame in frame_results:
                yield frame

        streaming_algorithm_metrics = self.calculator.calculate_algorithm_metrics_streaming(
            algorithm_run, frame_generator(), len(frame_results)
        )
        streaming_metrics = streaming_algorithm_metrics.ransac

        # 验证两种方法的结果一致
        assert streaming_metrics.avg_iterations == non_streaming_metrics.avg_iterations
        assert streaming_metrics.std_iterations == non_streaming_metrics.std_iterations
        assert streaming_metrics.min_iterations == non_streaming_metrics.min_iterations
        assert streaming_metrics.max_iterations == non_streaming_metrics.max_iterations
        assert streaming_metrics.convergence_rate == non_streaming_metrics.convergence_rate
        assert streaming_metrics.avg_inlier_ratio == non_streaming_metrics.avg_inlier_ratio
        assert streaming_metrics.success_rate == non_streaming_metrics.success_rate
        assert abs(streaming_metrics.avg_processing_time_ms - non_streaming_metrics.avg_processing_time_ms) < 0.01
