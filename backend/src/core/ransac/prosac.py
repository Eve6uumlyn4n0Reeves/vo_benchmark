#
# 功能: 实现PROSAC算法。
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


class PROSACRANSAC(RANSACEstimator):
    """PROSAC (Progressive Sample Consensus) 本质矩阵估计器"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化PROSAC估计器

        config 参数:
        {
            "threshold": 1.0,  # RANSAC 内点阈值 (像素)
            "confidence": 0.999,  # 置信度
            "max_iters": 2000,  # 最大迭代次数
            "method": cv2.USAC_PROSAC  # PROSAC方法
        }
        """
        # 设置默认参数
        default_config = {
            "threshold": 1.0,
            "confidence": 0.999,
            "max_iters": 2000,
            "method": cv2.USAC_PROSAC,  # 使用OpenCV的PROSAC实现
        }

        self.config = {**default_config, **config}

        # 验证参数
        assert 0.0 < self.config["threshold"], "阈值必须大于0"
        assert 0.0 < self.config["confidence"] < 1.0, "置信度必须在(0,1)范围内"
        assert self.config["max_iters"] > 0, "最大迭代次数必须大于0"

        logger.info(f"初始化PROSAC估计器，配置: {self.config}")

    def estimate(
        self,
        keypoints1: List[Point2D],
        keypoints2: List[Point2D],
        matches: FrameMatches,
        K: np.ndarray,
    ) -> RANSACResult:
        """
        使用PROSAC从匹配点对中估计本质矩阵和位姿

        PROSAC利用特征匹配的置信度分数，优先采样高质量的匹配点，
        从而提高收敛速度和精度。

        Args:
            keypoints1: 第一帧的关键点坐标
            keypoints2: 第二帧的关键点坐标
            matches: 特征匹配结果（包含匹配分数）
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

            # 提取并排序匹配点对（根据匹配分数）
            pts1, pts2, sorted_indices = self._extract_and_sort_matched_points(
                keypoints1, keypoints2, matches
            )

            if len(pts1) < self.get_min_samples():
                logger.warning("有效匹配点对不足")
                return self._create_failed_result(
                    start_time, "insufficient_valid_matches"
                )

            # 验证相机内参矩阵
            if K.shape != (3, 3):
                raise ValueError(f"相机内参矩阵形状必须是(3,3)，当前是{K.shape}")

            # 使用OpenCV的findEssentialMat with PROSAC
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
                logger.warning("PROSAC本质矩阵估计失败")
                return self._create_failed_result(start_time, "estimation_failed")

            # 将内点掩码映射回原始匹配顺序
            original_inlier_mask = self._map_mask_to_original_order(
                mask, sorted_indices, len(matches.matches)
            )
            num_inliers = sum(original_inlier_mask)

            if num_inliers < self.get_min_samples():
                logger.warning(f"内点数量({num_inliers})少于最小样本数")
                return self._create_failed_result(start_time, "insufficient_inliers")

            # 从本质矩阵恢复位姿
            rotation, translation = self._recover_pose(
                essential_mat, pts1, pts2, K, mask
            )

            # 计算置信度
            confidence = num_inliers / len(matches.matches)

            # 估计迭代次数（PROSAC通常比标准RANSAC收敛更快）
            inlier_ratio = confidence
            estimated_iters = self._estimate_prosac_iterations(inlier_ratio)

            logger.debug(
                f"PROSAC估计成功: 内点数={num_inliers}/{len(matches.matches)}, "
                f"置信度={confidence:.3f}, 时间={ransac_time:.3f}s"
            )

            return RANSACResult(
                inlier_mask=original_inlier_mask,
                num_iterations=min(estimated_iters, self.config["max_iters"]),
                fundamental_matrix=None,
                essential_matrix=essential_mat,
                rotation=rotation,
                translation=translation,
                confidence=confidence,
                ransac_time=ransac_time,
                min_samples=self.get_min_samples(),
            )

        except Exception as e:
            logger.error(f"PROSAC估计过程中发生错误: {e}")
            return self._create_failed_result(start_time, f"error: {str(e)}")

    def get_min_samples(self) -> int:
        """返回5点法所需的最小样本数"""
        return 5

    def _extract_and_sort_matched_points(
        self,
        keypoints1: List[Point2D],
        keypoints2: List[Point2D],
        matches: FrameMatches,
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        提取匹配的点对并根据匹配分数排序

        Returns:
            pts1: 排序后的第一帧点
            pts2: 排序后的第二帧点
            sorted_indices: 排序后的原始索引
        """
        pts1 = []
        pts2 = []
        scores = []
        valid_indices = []

        for i, (match_pair, score) in enumerate(zip(matches.matches, matches.scores)):
            idx1, idx2 = match_pair
            if 0 <= idx1 < len(keypoints1) and 0 <= idx2 < len(keypoints2):
                pts1.append(keypoints1[idx1])
                pts2.append(keypoints2[idx2])
                scores.append(score)
                valid_indices.append(i)

        # 根据匹配分数降序排序（高质量匹配优先）
        sorted_indices = np.argsort(scores)[::-1]  # 降序排序

        pts1_array = np.array(pts1, dtype=np.float32)
        pts2_array = np.array(pts2, dtype=np.float32)

        # 重新排序
        pts1_sorted = pts1_array[sorted_indices]
        pts2_sorted = pts2_array[sorted_indices]
        original_indices = np.array(valid_indices)[sorted_indices]

        return pts1_sorted, pts2_sorted, original_indices

    def _map_mask_to_original_order(
        self, mask: np.ndarray, sorted_indices: np.ndarray, total_matches: int
    ) -> List[bool]:
        """将排序后的掩码映射回原始匹配顺序"""
        original_mask = [False] * total_matches

        for i, original_idx in enumerate(sorted_indices):
            if i < len(mask) and mask[i][0]:
                original_mask[original_idx] = True

        return original_mask

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

            if num_pose_inliers < 10:
                logger.warning(f"位姿恢复的内点数({num_pose_inliers})过少")
                return np.eye(3), np.zeros((3, 1))

            return R, t

        except Exception as e:
            logger.error(f"位姿恢复失败: {e}")
            return np.eye(3), np.zeros((3, 1))

    def _estimate_prosac_iterations(self, inlier_ratio: float) -> int:
        """
        根据内点比例估计PROSAC所需的迭代次数

        PROSAC通常比标准RANSAC收敛更快，因为它优先采样高质量匹配
        """
        if inlier_ratio <= 0:
            return self.config["max_iters"]

        # PROSAC的迭代次数通常比标准RANSAC少30-50%
        standard_iters = self._estimate_standard_iterations(inlier_ratio)
        prosac_speedup = 0.6  # PROSAC通常能提供40%的速度提升

        estimated_iters = int(standard_iters * prosac_speedup)
        return max(1, min(estimated_iters, self.config["max_iters"]))

    def _estimate_standard_iterations(self, inlier_ratio: float) -> int:
        """估计标准RANSAC的迭代次数作为参考，避免数值边界导致的 log(0) 警告"""
        # 数值夹取，避免 w=0 或 w=1 导致分母为 0
        eps = 1e-12
        w = float(np.clip(inlier_ratio, eps, 1.0 - eps))
        p = self.config["confidence"]
        k = self.get_min_samples()

        try:
            denom = np.log(1.0 - w**k)
            if denom >= 0.0:
                return self.config["max_iters"]
            iterations = int(np.log(1.0 - p) / denom)
            return max(1, min(iterations, self.config["max_iters"]))
        except Exception:
            return self.config["max_iters"]

    def _create_failed_result(self, start_time: float, reason: str) -> RANSACResult:
        """创建失败的RANSAC结果"""
        ransac_time = time.time() - start_time
        logger.debug(f"PROSAC估计失败: {reason}")

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


# Alias for backward compatibility
PROSAC = PROSACRANSAC
