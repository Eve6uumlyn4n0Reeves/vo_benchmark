#
# 功能: 实现标准RANSAC算法。
#
from typing import Dict, Any, List, Tuple
import numpy as np
import cv2
import time
import logging
from src.core.ransac.base import RANSACEstimator
from src.models.types import Point2D
from src.models.frame import FrameMatches, RANSACResult

logger = logging.getLogger(__name__)


class StandardRANSAC(RANSACEstimator):
    """标准RANSAC本质矩阵估计器"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化标准RANSAC估计器

        config 参数:
        {
            "threshold": 1.0,  # RANSAC 内点阈值 (像素)
            "confidence": 0.999,  # 置信度
            "max_iters": 2000,  # 最大迭代次数
            "method": cv2.RANSAC  # RANSAC方法
        }
        """
        # 设置默认参数
        default_config = {
            "threshold": 1.0,
            "confidence": 0.999,
            "max_iters": 2000,
            "method": cv2.RANSAC,
        }

        self.config = {**default_config, **config}

        # 验证参数
        assert 0.0 < self.config["threshold"], "阈值必须大于0"
        assert 0.0 < self.config["confidence"] < 1.0, "置信度必须在(0,1)范围内"
        assert self.config["max_iters"] > 0, "最大迭代次数必须大于0"

        logger.info(f"初始化标准RANSAC估计器，配置: {self.config}")

    def estimate(
        self,
        keypoints1: List[Point2D],
        keypoints2: List[Point2D],
        matches: FrameMatches,
        K: np.ndarray,
    ) -> RANSACResult:
        """
        使用标准RANSAC从匹配点对中估计本质矩阵和位姿

        Args:
            keypoints1: 第一帧的关键点坐标
            keypoints2: 第二帧的关键点坐标
            matches: 特征匹配结果
            K: 相机内参矩阵 (3x3)

        Returns:
            RANSACResult: RANSAC估计结果
        """
        start_time = time.time()

        try:
            # 检查输入有效性
            if len(matches.matches) < self.get_min_samples():
                logger.warning(
                    f"匹配点数量({len(matches.matches)})少于最小样本数({self.get_min_samples()})"
                )
                return self._create_failed_result(start_time, "insufficient_matches")

            # 提取匹配的点对
            pts1, pts2 = self._extract_matched_points(keypoints1, keypoints2, matches)

            if len(pts1) < self.get_min_samples():
                logger.warning("有效匹配点对不足")
                return self._create_failed_result(
                    start_time, "insufficient_valid_matches"
                )

            # 验证相机内参矩阵
            if K.shape != (3, 3):
                raise ValueError(f"相机内参矩阵形状必须是(3,3)，当前是{K.shape}")

            # 使用OpenCV的findEssentialMat进行RANSAC估计
            essential_mat, mask = cv2.findEssentialMat(
                pts1,
                pts2,
                K,
                method=self.config["method"],
                prob=self.config["confidence"],
                threshold=self.config["threshold"],
                maxIters=self.config["max_iters"],
            )

            ransac_time = time.time() - start_time

            if essential_mat is None or mask is None:
                logger.warning("本质矩阵估计失败")
                return self._create_failed_result(start_time, "estimation_failed")

            # 计算内点掩码
            inlier_mask = [bool(m[0]) for m in mask]
            num_inliers = sum(inlier_mask)

            if num_inliers < self.get_min_samples():
                logger.warning(f"内点数量({num_inliers})少于最小样本数")
                return self._create_failed_result(start_time, "insufficient_inliers")

            # 从本质矩阵恢复位姿
            rotation, translation = self._recover_pose(
                essential_mat, pts1, pts2, K, mask
            )

            # 计算置信度
            confidence = num_inliers / len(matches.matches)

            # 估计迭代次数（基于内点比例）
            inlier_ratio = confidence
            estimated_iters = self._estimate_iterations(inlier_ratio)

            logger.debug(
                f"RANSAC估计成功: 内点数={num_inliers}/{len(matches.matches)}, "
                f"置信度={confidence:.3f}, 时间={ransac_time:.3f}s"
            )

            return RANSACResult(
                inlier_mask=inlier_mask,
                num_iterations=min(estimated_iters, self.config["max_iters"]),
                fundamental_matrix=None,  # 标准RANSAC不计算基础矩阵
                essential_matrix=essential_mat,
                rotation=rotation,
                translation=translation,
                confidence=confidence,
                ransac_time=ransac_time,
                min_samples=self.get_min_samples(),
            )

        except Exception as e:
            logger.error(f"RANSAC估计过程中发生错误: {e}")
            return self._create_failed_result(start_time, f"error: {str(e)}")

    def get_min_samples(self) -> int:
        """返回5点法所需的最小样本数"""
        return 5

    def _extract_matched_points(
        self,
        keypoints1: List[Point2D],
        keypoints2: List[Point2D],
        matches: FrameMatches,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """提取匹配的点对"""
        pts1 = []
        pts2 = []

        for match_pair in matches.matches:
            idx1, idx2 = match_pair
            if 0 <= idx1 < len(keypoints1) and 0 <= idx2 < len(keypoints2):
                pts1.append(keypoints1[idx1])
                pts2.append(keypoints2[idx2])

        return np.array(pts1, dtype=np.float32), np.array(pts2, dtype=np.float32)

    def _recover_pose(
        self,
        essential_mat: np.ndarray,
        pts1: np.ndarray,
        pts2: np.ndarray,
        K: np.ndarray,
        mask: np.ndarray,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """从本质矩阵恢复相机位姿"""
        try:
            # 提取内点
            inlier_pts1 = pts1[mask.ravel() == 1]
            inlier_pts2 = pts2[mask.ravel() == 1]

            # 使用recoverPose恢复位姿
            num_pose_inliers, R, t, pose_mask = cv2.recoverPose(
                essential_mat, inlier_pts1, inlier_pts2, K
            )

            if num_pose_inliers < 10:  # 需要足够的内点来保证位姿稳定
                logger.warning(f"位姿恢复的内点数({num_pose_inliers})过少")
                return np.eye(3), np.zeros((3, 1))

            return R, t

        except Exception as e:
            logger.error(f"位姿恢复失败: {e}")
            return np.eye(3), np.zeros((3, 1))

    def _estimate_iterations(self, inlier_ratio: float) -> int:
        """根据内点比例估计所需的迭代次数，避免数值边界导致的 log(0) 警告"""
        # 数值夹取，避免 w=0 或 w=1 导致分母为 0
        eps = 1e-12
        w = float(np.clip(inlier_ratio, eps, 1.0 - eps))
        if w <= 0.0:
            return self.config["max_iters"]

        # 使用RANSAC理论公式估计迭代次数
        # N = log(1-p) / log(1-w^k)
        # p: 置信度, w: 内点比例, k: 最小样本数
        p = self.config["confidence"]
        k = self.get_min_samples()

        try:
            denom = np.log(1.0 - w**k)
            if denom >= 0.0:  # 避免除以0或非负
                return self.config["max_iters"]
            iterations = int(np.log(1.0 - p) / denom)
            return max(1, min(iterations, self.config["max_iters"]))
        except Exception:
            return self.config["max_iters"]

    def _create_failed_result(self, start_time: float, reason: str) -> RANSACResult:
        """创建失败的RANSAC结果"""
        ransac_time = time.time() - start_time
        logger.debug(f"RANSAC估计失败: {reason}")

        return RANSACResult(
            inlier_mask=[],
            num_iterations=0,
            fundamental_matrix=None,
            essential_matrix=None,
            rotation=None,
            translation=None,
            confidence=0.0,
            ransac_time=ransac_time,
            min_samples=self.get_min_samples(),
        )
