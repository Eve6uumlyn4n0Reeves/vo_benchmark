"""
测试轨迹构建的单元测试
"""
import pytest
import numpy as np
from unittest.mock import Mock
from src.api.services.result import ResultService
from src.models.frame import FrameResult, FrameFeatures, FrameMatches, RANSACResult


class TestTrajectoryBuilding:
    """轨迹构建测试类"""

    def setup_method(self):
        """设置测试环境"""
        self.result_service = ResultService()

    def create_mock_frame_result(self, frame_id: int, estimated_pose=None, 
                                 ground_truth_pose=None, inlier_ratio=0.8) -> FrameResult:
        """创建模拟的帧结果"""
        return FrameResult(
            frame_id=frame_id,
            timestamp=frame_id * 0.1,
            features=FrameFeatures(
                keypoints=[(100.0, 150.0)],
                descriptors=np.random.rand(1, 128),
                scores=[0.8]
            ),
            matches=FrameMatches(
                matches=[(0, 0)],
                scores=[0.9]
            ),
            ransac=RANSACResult(
                inlier_mask=[True],
                num_iterations=100,
                fundamental_matrix=np.eye(3),
                essential_matrix=np.eye(3),
                rotation=np.eye(3),
                translation=np.array([0.1, 0.05, 0.0]).reshape(3, 1),
                confidence=0.95,
                ransac_time=0.01,
                min_samples=8
            ),
            num_matches=1,
            num_inliers=1,
            inlier_ratio=inlier_ratio,
            estimated_pose=estimated_pose,
            ground_truth_pose=ground_truth_pose,
            processing_time=0.05,
            status="SUCCESS",
            pose_error=0.1,
            reprojection_errors=[0.5],
            error=None
        )

    def test_trajectory_with_valid_poses(self):
        """测试有有效位姿估计的轨迹构建"""
        # 创建一系列位姿
        poses = [
            np.array([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]),  # 原点
            np.array([[1, 0, 0, 1], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]),  # x=1
            np.array([[1, 0, 0, 2], [0, 1, 0, 1], [0, 0, 1, 0], [0, 0, 0, 1]]),  # x=2, y=1
        ]

        frame_results = [
            self.create_mock_frame_result(i, estimated_pose=poses[i])
            for i in range(len(poses))
        ]

        # 创建模拟配置
        mock_config = Mock()
        mock_config.sequences = ["test_sequence"]

        # 构建轨迹
        trajectory_data = self.result_service._build_trajectory_from_frames(
            "test_exp", "test_alg", frame_results, mock_config, False
        )

        # 验证轨迹点
        estimated_traj = trajectory_data["estimated_trajectory"]
        assert len(estimated_traj) == 3

        # 验证位置
        assert estimated_traj[0]["x"] == 0.0
        assert estimated_traj[0]["y"] == 0.0
        assert estimated_traj[0]["z"] == 0.0
        assert estimated_traj[0]["has_pose_estimate"] == True

        assert estimated_traj[1]["x"] == 1.0
        assert estimated_traj[1]["y"] == 0.0
        assert estimated_traj[1]["z"] == 0.0
        assert estimated_traj[1]["has_pose_estimate"] == True

        assert estimated_traj[2]["x"] == 2.0
        assert estimated_traj[2]["y"] == 1.0
        assert estimated_traj[2]["z"] == 0.0
        assert estimated_traj[2]["has_pose_estimate"] == True

    def test_trajectory_with_missing_poses(self):
        """测试缺少位姿估计的轨迹构建"""
        # 创建混合数据：有些帧有位姿，有些没有
        poses = [
            np.array([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]),  # 原点
            None,  # 缺少位姿
            np.array([[1, 0, 0, 2], [0, 1, 0, 1], [0, 0, 1, 0], [0, 0, 0, 1]]),  # x=2, y=1
        ]

        frame_results = [
            self.create_mock_frame_result(i, estimated_pose=poses[i], inlier_ratio=0.9)
            for i in range(len(poses))
        ]

        # 创建模拟配置
        mock_config = Mock()
        mock_config.sequences = ["test_sequence"]

        # 构建轨迹
        trajectory_data = self.result_service._build_trajectory_from_frames(
            "test_exp", "test_alg", frame_results, mock_config, False
        )

        # 验证轨迹点
        estimated_traj = trajectory_data["estimated_trajectory"]
        assert len(estimated_traj) == 2  # 只有有位姿的帧会被添加（第一帧和第三帧）

        # 第一帧：有位姿
        assert estimated_traj[0]["x"] == 0.0
        assert estimated_traj[0]["y"] == 0.0
        assert estimated_traj[0]["has_pose_estimate"] == True

        # 第三帧：有位姿（第二帧被跳过了，因为没有位姿）
        assert estimated_traj[1]["x"] == 2.0
        assert estimated_traj[1]["y"] == 1.0
        assert estimated_traj[1]["has_pose_estimate"] == True

    def test_trajectory_with_no_poses(self):
        """测试完全没有位姿估计的轨迹构建"""
        frame_results = [
            self.create_mock_frame_result(i, estimated_pose=None, inlier_ratio=0.8)
            for i in range(3)
        ]

        # 创建模拟配置
        mock_config = Mock()
        mock_config.sequences = ["test_sequence"]

        # 构建轨迹
        trajectory_data = self.result_service._build_trajectory_from_frames(
            "test_exp", "test_alg", frame_results, mock_config, False
        )

        # 验证轨迹点
        estimated_traj = trajectory_data["estimated_trajectory"]
        assert len(estimated_traj) == 1  # 只有第一帧被添加

        # 第一帧：即使没有位姿也会被添加（原点）
        assert estimated_traj[0]["x"] == 0.0
        assert estimated_traj[0]["y"] == 0.0
        assert estimated_traj[0]["z"] == 0.0
        assert estimated_traj[0]["has_pose_estimate"] == False

    def test_trajectory_no_inlier_ratio_simulation(self):
        """测试不再使用inlier_ratio进行运动模拟"""
        # 创建高inlier_ratio但没有位姿的帧
        frame_results = [
            self.create_mock_frame_result(0, estimated_pose=None, inlier_ratio=0.9),
            self.create_mock_frame_result(1, estimated_pose=None, inlier_ratio=0.8),
            self.create_mock_frame_result(2, estimated_pose=None, inlier_ratio=0.7),
        ]

        # 创建模拟配置
        mock_config = Mock()
        mock_config.sequences = ["test_sequence"]

        # 构建轨迹
        trajectory_data = self.result_service._build_trajectory_from_frames(
            "test_exp", "test_alg", frame_results, mock_config, False
        )

        # 验证轨迹点
        estimated_traj = trajectory_data["estimated_trajectory"]
        
        # 应该只有第一帧（原点），不应该有基于inlier_ratio的模拟运动
        assert len(estimated_traj) == 1
        assert estimated_traj[0]["x"] == 0.0
        assert estimated_traj[0]["y"] == 0.0
        assert estimated_traj[0]["z"] == 0.0

    def test_trajectory_with_ground_truth(self):
        """测试包含地面真值的轨迹构建"""
        # 创建估计位姿和地面真值位姿
        estimated_poses = [
            np.array([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]),
            np.array([[1, 0, 0, 1.1], [0, 1, 0, 0.1], [0, 0, 1, 0], [0, 0, 0, 1]]),
        ]
        
        gt_poses = [
            np.array([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]),
            np.array([[1, 0, 0, 1], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]),
        ]

        frame_results = [
            self.create_mock_frame_result(i, estimated_pose=estimated_poses[i], 
                                        ground_truth_pose=gt_poses[i])
            for i in range(len(estimated_poses))
        ]

        # 创建模拟配置
        mock_config = Mock()
        mock_config.sequences = ["test_sequence"]

        # 构建轨迹
        trajectory_data = self.result_service._build_trajectory_from_frames(
            "test_exp", "test_alg", frame_results, mock_config, False
        )

        # 验证估计轨迹
        estimated_traj = trajectory_data["estimated_trajectory"]
        assert len(estimated_traj) == 2
        assert estimated_traj[1]["x"] == 1.1  # 估计值
        assert estimated_traj[1]["y"] == 0.1

        # 验证地面真值轨迹
        gt_traj = trajectory_data["groundtruth_trajectory"]
        assert len(gt_traj) == 2
        assert gt_traj[1]["x"] == 1.0  # 真值
        assert gt_traj[1]["y"] == 0.0

        # 验证元数据
        assert trajectory_data["metadata"]["has_groundtruth"] == True

    def test_trajectory_with_reference_generation(self):
        """测试参考轨迹生成"""
        frame_results = [
            self.create_mock_frame_result(i, estimated_pose=None)
            for i in range(3)
        ]

        # 创建模拟配置
        mock_config = Mock()
        mock_config.sequences = ["test_sequence"]

        # 构建轨迹，启用参考生成
        trajectory_data = self.result_service._build_trajectory_from_frames(
            "test_exp", "test_alg", frame_results, mock_config, include_reference=True
        )

        # 验证参考轨迹被生成
        gt_traj = trajectory_data["groundtruth_trajectory"]
        assert len(gt_traj) == 3
        
        # 参考轨迹应该是直线
        assert gt_traj[0]["x"] == 0.0
        assert gt_traj[1]["x"] == 0.1
        assert gt_traj[2]["x"] == 0.2

        # 验证元数据
        assert trajectory_data["metadata"]["has_groundtruth"] == False
        assert trajectory_data["metadata"]["reference_groundtruth"] == True

    def test_trajectory_statistics_calculation(self):
        """测试轨迹统计信息计算"""
        poses = [
            np.array([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]),
            np.array([[1, 0, 0, 1], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]),
            np.array([[1, 0, 0, 2], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]),
        ]

        frame_results = [
            self.create_mock_frame_result(i, estimated_pose=poses[i])
            for i in range(len(poses))
        ]

        # 创建模拟配置
        mock_config = Mock()
        mock_config.sequences = ["test_sequence"]

        # 构建轨迹
        trajectory_data = self.result_service._build_trajectory_from_frames(
            "test_exp", "test_alg", frame_results, mock_config, False
        )

        # 验证统计信息
        stats = trajectory_data["statistics"]
        assert stats["total_points"] == 3
        assert stats["trajectory_length"] == 2.0  # 总长度为2米（0->1->2）
        assert stats["duration_seconds"] == 0.2  # 3帧，每帧0.1秒间隔
