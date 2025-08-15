"""
测试重投影误差计算的单元测试
"""
import pytest
import numpy as np
from unittest.mock import Mock, patch
from src.pipeline.processor import FrameProcessor
from src.models.frame import FrameFeatures, FrameMatches, RANSACResult
from src.models.types import Point2D, MatchPair


class TestReprojectionErrors:
    """重投影误差计算测试类"""

    def setup_method(self):
        """设置测试环境"""
        # 创建模拟的相机内参矩阵
        self.calibration = np.array([
            [800.0, 0.0, 320.0],
            [0.0, 800.0, 240.0],
            [0.0, 0.0, 1.0]
        ])
        
        # 创建模拟的特征提取器、匹配器和估计器
        self.mock_extractor = Mock()
        self.mock_matcher = Mock()
        self.mock_estimator = Mock()
        
        # 创建FrameProcessor实例
        self.processor = FrameProcessor(
            extractor=self.mock_extractor,
            matcher=self.mock_matcher,
            estimator=self.mock_estimator,
            calibration=self.calibration
        )

    def test_calculate_reprojection_errors_valid_case(self):
        """测试有效情况下的重投影误差计算"""
        # 创建测试数据
        features1 = FrameFeatures(
            keypoints=[(100.0, 150.0), (200.0, 250.0)],
            descriptors=np.random.rand(2, 128),
            scores=[0.8, 0.9]
        )
        
        features2 = FrameFeatures(
            keypoints=[(110.0, 160.0), (210.0, 260.0)],
            descriptors=np.random.rand(2, 128),
            scores=[0.7, 0.85]
        )
        
        matches = FrameMatches(
            matches=[(0, 0), (1, 1)],
            scores=[0.9, 0.8]
        )
        
        # 创建简单的旋转和平移（小的运动）
        R = np.eye(3)  # 无旋转
        t = np.array([0.1, 0.05, 0.0]).reshape(3, 1)  # 小的平移
        
        ransac_result = RANSACResult(
            inlier_mask=[True, True],
            num_iterations=100,
            fundamental_matrix=np.eye(3),
            essential_matrix=np.eye(3),
            rotation=R,
            translation=t,
            confidence=0.95,
            ransac_time=0.01,
            min_samples=8
        )
        
        # 调用重投影误差计算
        errors = self.processor._calculate_reprojection_errors(
            features1, features2, matches, ransac_result
        )
        
        # 验证结果
        assert errors is not None
        assert len(errors) == 2
        assert all(isinstance(e, float) for e in errors)
        assert all(e >= 0 for e in errors)
        assert all(not np.isinf(e) and not np.isnan(e) for e in errors)

    def test_calculate_reprojection_errors_no_rotation_translation(self):
        """测试缺少旋转或平移时的情况"""
        features1 = FrameFeatures(
            keypoints=[(100.0, 150.0)],
            descriptors=np.random.rand(1, 128),
            scores=[0.8]
        )
        
        features2 = FrameFeatures(
            keypoints=[(110.0, 160.0)],
            descriptors=np.random.rand(1, 128),
            scores=[0.7]
        )
        
        matches = FrameMatches(
            matches=[(0, 0)],
            scores=[0.9]
        )
        
        # 缺少旋转矩阵的情况
        ransac_result = RANSACResult(
            inlier_mask=[True],
            num_iterations=100,
            fundamental_matrix=np.eye(3),
            essential_matrix=np.eye(3),
            rotation=None,  # 缺少旋转
            translation=np.array([0.1, 0.05, 0.0]).reshape(3, 1),
            confidence=0.95,
            ransac_time=0.01,
            min_samples=8
        )
        
        errors = self.processor._calculate_reprojection_errors(
            features1, features2, matches, ransac_result
        )
        
        assert errors is None

    def test_calculate_reprojection_errors_empty_matches(self):
        """测试空匹配的情况"""
        features1 = FrameFeatures(
            keypoints=[],
            descriptors=np.empty((0, 128)),
            scores=[]
        )
        
        features2 = FrameFeatures(
            keypoints=[],
            descriptors=np.empty((0, 128)),
            scores=[]
        )
        
        matches = FrameMatches(
            matches=[],
            scores=[]
        )
        
        ransac_result = RANSACResult(
            inlier_mask=[],
            num_iterations=100,
            fundamental_matrix=np.eye(3),
            essential_matrix=np.eye(3),
            rotation=np.eye(3),
            translation=np.array([0.1, 0.05, 0.0]).reshape(3, 1),
            confidence=0.95,
            ransac_time=0.01,
            min_samples=8
        )
        
        errors = self.processor._calculate_reprojection_errors(
            features1, features2, matches, ransac_result
        )
        
        assert errors is None

    def test_calculate_reprojection_errors_index_out_of_bounds(self):
        """测试索引越界的情况"""
        features1 = FrameFeatures(
            keypoints=[(100.0, 150.0)],
            descriptors=np.random.rand(1, 128),
            scores=[0.8]
        )
        
        features2 = FrameFeatures(
            keypoints=[(110.0, 160.0)],
            descriptors=np.random.rand(1, 128),
            scores=[0.7]
        )
        
        # 匹配索引超出范围
        matches = FrameMatches(
            matches=[(0, 0), (1, 1)],  # 索引1超出范围
            scores=[0.9, 0.8]
        )
        
        ransac_result = RANSACResult(
            inlier_mask=[True, True],
            num_iterations=100,
            fundamental_matrix=np.eye(3),
            essential_matrix=np.eye(3),
            rotation=np.eye(3),
            translation=np.array([0.1, 0.05, 0.0]).reshape(3, 1),
            confidence=0.95,
            ransac_time=0.01,
            min_samples=8
        )
        
        errors = self.processor._calculate_reprojection_errors(
            features1, features2, matches, ransac_result
        )
        
        # 应该返回有效误差（过滤掉无效的）
        assert errors is not None
        assert len(errors) == 1  # 只有一个有效误差

    def test_calculate_reprojection_errors_behind_camera(self):
        """测试点在相机后方的情况"""
        features1 = FrameFeatures(
            keypoints=[(100.0, 150.0)],
            descriptors=np.random.rand(1, 128),
            scores=[0.8]
        )
        
        features2 = FrameFeatures(
            keypoints=[(110.0, 160.0)],
            descriptors=np.random.rand(1, 128),
            scores=[0.7]
        )
        
        matches = FrameMatches(
            matches=[(0, 0)],
            scores=[0.9]
        )
        
        # 创建会导致点在相机后方的变换
        R = np.array([[-1, 0, 0], [0, -1, 0], [0, 0, -1]])  # 180度旋转
        t = np.array([0.0, 0.0, -1.0]).reshape(3, 1)  # 向后平移
        
        ransac_result = RANSACResult(
            inlier_mask=[True],
            num_iterations=100,
            fundamental_matrix=np.eye(3),
            essential_matrix=np.eye(3),
            rotation=R,
            translation=t,
            confidence=0.95,
            ransac_time=0.01,
            min_samples=8
        )
        
        errors = self.processor._calculate_reprojection_errors(
            features1, features2, matches, ransac_result
        )
        
        # 应该返回None，因为没有有效的误差
        assert errors is None

    def test_calculate_reprojection_errors_invalid_calibration(self):
        """测试无效相机内参的情况"""
        # 测试FrameProcessor构造函数会拒绝无效的相机内参
        invalid_calibration = np.array([[800.0, 0.0], [0.0, 800.0]])  # 2x2矩阵

        with pytest.raises(ValueError, match="相机内参矩阵必须是3x3"):
            FrameProcessor(
                extractor=self.mock_extractor,
                matcher=self.mock_matcher,
                estimator=self.mock_estimator,
                calibration=invalid_calibration
            )

    def test_calculate_reprojection_errors_singular_calibration(self):
        """测试奇异相机内参矩阵的情况"""
        # 创建奇异的相机内参矩阵（不可逆）
        singular_calibration = np.array([
            [800.0, 0.0, 320.0],
            [0.0, 0.0, 240.0],  # 第二行第二列为0，使矩阵奇异
            [0.0, 0.0, 1.0]
        ])

        processor = FrameProcessor(
            extractor=self.mock_extractor,
            matcher=self.mock_matcher,
            estimator=self.mock_estimator,
            calibration=singular_calibration
        )

        features1 = FrameFeatures(
            keypoints=[(100.0, 150.0)],
            descriptors=np.random.rand(1, 128),
            scores=[0.8]
        )

        features2 = FrameFeatures(
            keypoints=[(110.0, 160.0)],
            descriptors=np.random.rand(1, 128),
            scores=[0.7]
        )

        matches = FrameMatches(
            matches=[(0, 0)],
            scores=[0.9]
        )

        ransac_result = RANSACResult(
            inlier_mask=[True],
            num_iterations=100,
            fundamental_matrix=np.eye(3),
            essential_matrix=np.eye(3),
            rotation=np.eye(3),
            translation=np.array([0.1, 0.05, 0.0]).reshape(3, 1),
            confidence=0.95,
            ransac_time=0.01,
            min_samples=8
        )

        # 奇异矩阵会导致计算失败
        errors = processor._calculate_reprojection_errors(
            features1, features2, matches, ransac_result
        )

        assert errors is None
