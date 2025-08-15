#
# 功能: 定义单帧处理结果的数据模型。
#
from dataclasses import dataclass
from typing import List, Optional, Tuple
import numpy as np
from .types import Point2D, MatchPair, Pose


@dataclass
class FrameFeatures:
    """单帧特征提取结果"""

    keypoints: List[Point2D]
    descriptors: Optional[np.ndarray]
    scores: Optional[List[float]]

    def __post_init__(self):
        """验证数据一致性"""
        if self.descriptors is not None:
            assert (
                len(self.keypoints) == self.descriptors.shape[0]
            ), "关键点数量与描述子数量不一致"
        if self.scores is not None:
            assert len(self.keypoints) == len(self.scores), "关键点数量与分数数量不一致"


@dataclass
class FrameMatches:
    """两帧之间的特征匹配结果"""

    matches: List[MatchPair]
    scores: List[float]

    def __post_init__(self):
        """验证数据一致性"""
        assert len(self.matches) == len(self.scores), "匹配对数量与分数数量不一致"

    @property
    def num_matches(self) -> int:
        """匹配点对数量"""
        return len(self.matches)


@dataclass
class RANSACResult:
    """RANSAC位姿估计结果"""

    inlier_mask: List[bool]
    num_iterations: int
    fundamental_matrix: Optional[np.ndarray]
    essential_matrix: Optional[np.ndarray]
    rotation: Optional[np.ndarray]
    translation: Optional[np.ndarray]
    confidence: float
    ransac_time: float
    min_samples: int

    def __post_init__(self):
        """验证数据一致性和范围"""
        assert 0.0 <= self.confidence <= 1.0, "置信度必须在[0,1]范围内"
        assert self.ransac_time >= 0.0, "RANSAC时间不能为负"
        assert self.num_iterations >= 0, "迭代次数不能为负"
        assert self.min_samples > 0, "最小样本数必须大于0"

        if self.essential_matrix is not None:
            assert self.essential_matrix.shape == (3, 3), "本质矩阵必须是3x3"
        if self.fundamental_matrix is not None:
            assert self.fundamental_matrix.shape == (3, 3), "基础矩阵必须是3x3"
        if self.rotation is not None:
            assert self.rotation.shape == (3, 3), "旋转矩阵必须是3x3"
        if self.translation is not None:
            assert self.translation.shape == (3, 1) or self.translation.shape == (
                3,
            ), "平移向量必须是3x1或(3,)"

    @property
    def num_inliers(self) -> int:
        """内点数量"""
        return sum(self.inlier_mask)

    @property
    def inlier_ratio(self) -> float:
        """内点比例"""
        if not self.inlier_mask:
            return 0.0
        return self.num_inliers / len(self.inlier_mask)


@dataclass
class FrameResult:
    """单帧处理的完整结果"""

    frame_id: int
    timestamp: float
    features: Optional[FrameFeatures]
    matches: Optional[FrameMatches]
    ransac: Optional[RANSACResult]
    num_matches: int
    num_inliers: int
    inlier_ratio: float
    estimated_pose: Optional[Pose]
    ground_truth_pose: Optional[Pose]
    processing_time: float
    status: str  # "SUCCESS", "NO_MATCHES", "RANSAC_FAILED", "FEATURE_EXTRACTION_FAILED"
    pose_error: Optional[float]
    reprojection_errors: Optional[List[float]]
    error: Optional[str]

    def __post_init__(self):
        """验证数据一致性和范围"""
        assert self.frame_id >= 0, "帧ID不能为负"
        assert self.timestamp >= 0.0, "时间戳不能为负"
        assert self.processing_time >= 0.0, "处理时间不能为负"
        assert 0.0 <= self.inlier_ratio <= 1.0, "内点比例必须在[0,1]范围内"
        assert self.num_matches >= 0, "匹配数不能为负"
        assert self.num_inliers >= 0, "内点数不能为负"
        assert self.num_inliers <= self.num_matches, "内点数不能超过总匹配数"

        # 验证状态值
        valid_statuses = {
            "SUCCESS",
            "NO_MATCHES",
            "RANSAC_FAILED",
            "FEATURE_EXTRACTION_FAILED",
        }
        assert self.status in valid_statuses, f"无效的状态值: {self.status}"

        # 验证位姿矩阵尺寸
        if self.estimated_pose is not None:
            assert self.estimated_pose.shape == (4, 4), "估计位姿必须是4x4齐次变换矩阵"
        if self.ground_truth_pose is not None:
            assert self.ground_truth_pose.shape == (
                4,
                4,
            ), "真值位姿必须是4x4齐次变换矩阵"

    @property
    def is_successful(self) -> bool:
        """判断帧处理是否成功"""
        return self.status == "SUCCESS" and self.estimated_pose is not None

    @property
    def has_ground_truth(self) -> bool:
        """是否有真值数据"""
        return self.ground_truth_pose is not None
