"""
测试PR曲线生成的单元测试
"""
import pytest
import numpy as np
from unittest.mock import Mock, patch
from src.api.services.result import ResultService
from src.models.frame import FrameResult, FrameFeatures, FrameMatches, RANSACResult


class TestPRCurveGeneration:
    """PR曲线生成测试类"""

    def setup_method(self):
        """设置测试环境"""
        self.result_service = ResultService()

    def create_mock_frame_result(self, frame_id: int, scores: list, inlier_mask: list) -> FrameResult:
        """创建模拟的帧结果"""
        matches = FrameMatches(
            matches=[(i, i) for i in range(len(scores))],
            scores=scores
        )
        
        ransac_result = RANSACResult(
            inlier_mask=inlier_mask,
            num_iterations=100,
            fundamental_matrix=np.eye(3),
            essential_matrix=np.eye(3),
            rotation=np.eye(3),
            translation=np.array([0.1, 0.05, 0.0]).reshape(3, 1),
            confidence=0.95,
            ransac_time=0.01,
            min_samples=8
        )
        
        return FrameResult(
            frame_id=frame_id,
            timestamp=frame_id * 0.1,
            features=FrameFeatures(
                keypoints=[(100.0 + i, 150.0 + i) for i in range(len(scores))],
                descriptors=np.random.rand(len(scores), 128),
                scores=[0.8] * len(scores)
            ),
            matches=matches,
            ransac=ransac_result,
            num_matches=len(scores),
            num_inliers=sum(inlier_mask),
            inlier_ratio=sum(inlier_mask) / len(inlier_mask) if inlier_mask else 0.0,
            estimated_pose=np.eye(4),
            ground_truth_pose=np.eye(4),
            processing_time=0.05,
            status="SUCCESS",
            pose_error=0.1,
            reprojection_errors=[0.5] * len(scores),
            error=None
        )

    def test_pr_curve_with_real_inlier_mask(self):
        """测试使用真实inlier_mask的PR曲线计算"""
        # 创建测试数据：高分数对应内点，低分数对应外点
        frame_results = [
            self.create_mock_frame_result(
                0, 
                scores=[0.1, 0.2, 0.8, 0.9, 0.3, 0.7],  # 匹配分数
                inlier_mask=[True, True, False, False, True, False]  # 真实标签
            ),
            self.create_mock_frame_result(
                1,
                scores=[0.15, 0.85, 0.25, 0.95],
                inlier_mask=[True, False, True, False]
            )
        ]

        # 计算PR曲线
        pr_data = self.result_service._calculate_pr_curve_from_frames("test_algorithm", frame_results)

        # 验证结果结构
        assert "algorithm" in pr_data
        assert "precisions" in pr_data
        assert "recalls" in pr_data
        assert "thresholds" in pr_data
        assert "auc_score" in pr_data
        assert pr_data["algorithm"] == "test_algorithm"
        
        # 验证有数据
        assert len(pr_data["precisions"]) > 0
        assert len(pr_data["recalls"]) > 0
        assert len(pr_data["thresholds"]) > 0

    def test_pr_curve_with_empty_data(self):
        """测试空数据的PR曲线计算"""
        frame_results = []

        pr_data = self.result_service._calculate_pr_curve_from_frames("test_algorithm", frame_results)

        # 验证返回空曲线
        assert pr_data["algorithm"] == "test_algorithm"
        assert pr_data["precisions"] == []
        assert pr_data["recalls"] == []
        assert pr_data["thresholds"] == []
        assert pr_data["auc_score"] == 0.0
        assert pr_data["has_data"] == False
        assert "No PR data available" in pr_data["message"]

    def test_pr_curve_with_missing_ransac_data(self):
        """测试缺少RANSAC数据的情况"""
        # 创建没有RANSAC结果的帧
        frame_result = FrameResult(
            frame_id=0,
            timestamp=0.0,
            features=FrameFeatures(
                keypoints=[(100.0, 150.0)],
                descriptors=np.random.rand(1, 128),
                scores=[0.8]
            ),
            matches=FrameMatches(
                matches=[(0, 0)],
                scores=[0.9]
            ),
            ransac=None,  # 没有RANSAC结果
            num_matches=1,
            num_inliers=0,
            inlier_ratio=0.0,
            estimated_pose=None,
            ground_truth_pose=None,
            processing_time=0.05,
            status="RANSAC_FAILED",
            pose_error=None,
            reprojection_errors=None,
            error="RANSAC failed"
        )

        pr_data = self.result_service._calculate_pr_curve_from_frames("test_algorithm", [frame_result])

        # 验证返回空曲线
        assert pr_data["has_data"] == False

    def test_pr_curve_with_mismatched_data_lengths(self):
        """测试匹配数量与inlier_mask长度不一致的情况"""
        # 创建数据长度不一致的帧
        matches = FrameMatches(
            matches=[(0, 0), (1, 1), (2, 2)],
            scores=[0.8, 0.9, 0.7]  # 3个匹配
        )
        
        ransac_result = RANSACResult(
            inlier_mask=[True, False],  # 只有2个标签，长度不匹配
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
            frame_id=0,
            timestamp=0.0,
            features=FrameFeatures(
                keypoints=[(100.0, 150.0), (200.0, 250.0), (300.0, 350.0)],
                descriptors=np.random.rand(3, 128),
                scores=[0.8, 0.9, 0.7]
            ),
            matches=matches,
            ransac=ransac_result,
            num_matches=3,
            num_inliers=1,
            inlier_ratio=0.5,
            estimated_pose=np.eye(4),
            ground_truth_pose=np.eye(4),
            processing_time=0.05,
            status="SUCCESS",
            pose_error=0.1,
            reprojection_errors=[0.5, 2.0, 1.0],
            error=None
        )

        pr_data = self.result_service._calculate_pr_curve_from_frames("test_algorithm", [frame_result])

        # 验证返回空曲线（因为数据不一致被跳过）
        assert pr_data["has_data"] == False

    def test_pr_curve_with_large_dataset_sampling(self):
        """测试大数据集的采样功能"""
        # 创建大量匹配的帧
        large_scores = [0.1 + i * 0.001 for i in range(100)]  # 100个分数
        large_inlier_mask = [i % 3 == 0 for i in range(100)]  # 每3个中有1个内点

        frame_results = [
            self.create_mock_frame_result(0, large_scores, large_inlier_mask)
        ]

        pr_data = self.result_service._calculate_pr_curve_from_frames("test_algorithm", frame_results)

        # 验证有数据且采样正常工作
        assert len(pr_data["precisions"]) > 0
        assert len(pr_data["recalls"]) > 0
        assert len(pr_data["thresholds"]) > 0

    def test_pr_curve_score_negation(self):
        """测试分数取负值的逻辑"""
        # 创建测试数据，验证分数被正确取负
        frame_results = [
            self.create_mock_frame_result(
                0,
                scores=[0.1, 0.9],  # 原始分数
                inlier_mask=[True, False]
            )
        ]

        # 使用patch来监控_compute_pr_curve_inline的调用
        with patch.object(self.result_service, '_compute_pr_curve_inline') as mock_compute:
            mock_compute.return_value = {
                "algorithm": "test_algorithm",
                "precisions": [1.0, 0.5],
                "recalls": [0.5, 1.0],
                "thresholds": [-0.9, -0.1],  # 期望的负值
                "auc_score": 0.75,
                "optimal_threshold": -0.5,
                "optimal_precision": 0.75,
                "optimal_recall": 0.75,
                "f1_scores": [0.67, 0.67],
                "max_f1_score": 0.67
            }

            pr_data = self.result_service._calculate_pr_curve_from_frames("test_algorithm", frame_results)

            # 验证_compute_pr_curve_inline被调用，且分数被取负
            mock_compute.assert_called_once()
            call_args = mock_compute.call_args[0]
            algorithm_key, scores, labels = call_args
            
            assert algorithm_key == "test_algorithm"
            assert scores == [-0.1, -0.9]  # 分数被取负
            assert labels == [True, False]

    def test_pr_curve_with_no_matches(self):
        """测试没有匹配的帧"""
        frame_result = FrameResult(
            frame_id=0,
            timestamp=0.0,
            features=FrameFeatures(
                keypoints=[],
                descriptors=np.empty((0, 128)),
                scores=[]
            ),
            matches=FrameMatches(
                matches=[],
                scores=[]
            ),
            ransac=RANSACResult(
                inlier_mask=[],
                num_iterations=100,
                fundamental_matrix=np.eye(3),
                essential_matrix=np.eye(3),
                rotation=np.eye(3),
                translation=np.array([0.1, 0.05, 0.0]).reshape(3, 1),
                confidence=0.95,
                ransac_time=0.01,
                min_samples=8
            ),
            num_matches=0,
            num_inliers=0,
            inlier_ratio=0.0,
            estimated_pose=None,
            ground_truth_pose=None,
            processing_time=0.05,
            status="SUCCESS",
            pose_error=None,
            reprojection_errors=None,
            error=None
        )

        pr_data = self.result_service._calculate_pr_curve_from_frames("test_algorithm", [frame_result])

        # 验证返回空曲线
        assert pr_data["has_data"] == False
