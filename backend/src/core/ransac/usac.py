# USAC/MAGSAC/LO-RANSAC variants built on OpenCV
from typing import Dict, Any, List
import numpy as np
import cv2
import time
import logging
from src.core.ransac.base import RANSACEstimator
from src.models.frame import FrameMatches, RANSACResult
from src.models.types import Point2D

logger = logging.getLogger(__name__)


class USACEstimator(RANSACEstimator):
    """USAC family (USAC_DEFAULT, USAC_MAGSAC, USAC_ACCURATE, RHO, LMEDS).

    为了兼容不同 OpenCV 版本并获得更一致的内点掩码，本实现优先在基础矩阵 F 上运行
    （cv2.findFundamentalMat 支持 USAC/MAGSAC 等），随后通过 E = K^T F K 恢复姿态。
    """

    def __init__(self, config: Dict[str, Any]):
        # threshold 设置为像素重投影阈值（对 F 的 RANSAC 有效）；confidence/max_iters 直传
        default_method = getattr(cv2, "USAC_DEFAULT", 8)  # 兜底值不会被用到（仅防止属性不存在）
        base = {
            "threshold": 1.0,
            "confidence": 0.999,
            "max_iters": 2000,
            "method": config.get("method", default_method),
        }
        self.config = {**base, **(config or {})}
        logger.info(f"Initialized USAC estimator with config: {self.config}")

    def estimate(self, keypoints1: List[Point2D], keypoints2: List[Point2D], matches: FrameMatches, K: np.ndarray) -> RANSACResult:
        start = time.time()
        try:
            if len(matches.matches) < self.get_min_samples():
                return self._failed(start, "insufficient_matches")
            pts1, pts2 = self._extract_pts(keypoints1, keypoints2, matches)

            # 1) 估计基础矩阵 F（优先使用 USAC/MAGSAC 等方法）
            F, mask = cv2.findFundamentalMat(
                pts1,
                pts2,
                method=self.config["method"],
                ransacReprojThreshold=self.config["threshold"],
                confidence=self.config["confidence"],
                maxIters=self.config["max_iters"],
            )

            # 某些旧 OpenCV 若不支持 USAC 常量，回退到 RANSAC
            if F is None or mask is None:
                logger.warning("findFundamentalMat returned None; falling back to RANSAC")
                F, mask = cv2.findFundamentalMat(
                    pts1,
                    pts2,
                    method=cv2.FM_RANSAC,
                    ransacReprojThreshold=self.config["threshold"],
                    confidence=self.config["confidence"],
                    maxIters=self.config["max_iters"],
                )

            t = time.time() - start
            if F is None or mask is None:
                return self._failed(start, "estimation_failed")

            inlier_mask = [bool(int(m[0])) for m in mask]
            num_inliers = sum(inlier_mask)
            if num_inliers < self.get_min_samples():
                return self._failed(start, "insufficient_inliers")

            # 2) 从 F 计算 E 并恢复位姿
            try:
                E = K.T @ F @ K
            except Exception:
                E = None
            R, tvec = self._recover_pose_from_F_or_E(E, F, pts1, pts2, K, mask)

            conf = num_inliers / len(matches.matches)
            return RANSACResult(
                inlier_mask=inlier_mask,
                num_iterations=min(self.config["max_iters"], self._estimate_iters(conf)),
                fundamental_matrix=F,
                essential_matrix=E,
                rotation=R,
                translation=tvec,
                confidence=conf,
                ransac_time=t,
                min_samples=self.get_min_samples(),
            )
        except Exception as e:
            logger.error(f"USAC estimate error: {e}")
            return self._failed(start, f"error: {e}")

    def get_min_samples(self) -> int:
        # F 的 8 点算法最少样本（USAC 内部可能使用更小样本算法，但此处用于基本验证）
        return 8

    def _recover_pose_from_F_or_E(self, E, F, pts1, pts2, K, mask):
        try:
            in1 = pts1[mask.ravel() == 1]
            in2 = pts2[mask.ravel() == 1]
            if E is not None:
                _, R, t, _ = cv2.recoverPose(E, in1, in2, K)
                return R, t
            # 如果 E 不可用，尝试通过本质矩阵重估计
            E2, _ = cv2.findEssentialMat(in1, in2, K, method=cv2.RANSAC, prob=self.config["confidence"], threshold=self.config["threshold"], maxIters=self.config["max_iters"])
            if E2 is not None:
                _, R, t, _ = cv2.recoverPose(E2, in1, in2, K)
                return R, t
            return np.eye(3), np.zeros((3, 1))
        except Exception as e:
            logger.error(f"recoverPose failed: {e}")
            return np.eye(3), np.zeros((3, 1))

    def _extract_pts(self, k1, k2, matches: FrameMatches):
        pts1, pts2 = [], []
        for q, t in matches.matches:
            if 0 <= q < len(k1) and 0 <= t < len(k2):
                pts1.append(k1[q]); pts2.append(k2[t])
        return np.array(pts1, dtype=np.float32), np.array(pts2, dtype=np.float32)

    def _recover_pose(self, E, pts1, pts2, K, mask):
        try:
            in1 = pts1[mask.ravel() == 1]
            in2 = pts2[mask.ravel() == 1]
            _, R, t, _ = cv2.recoverPose(E, in1, in2, K)
            return R, t
        except Exception as e:
            logger.error(f"recoverPose failed: {e}")
            return np.eye(3), np.zeros((3, 1))

    def _estimate_iters(self, inlier_ratio: float) -> int:
        if inlier_ratio <= 0:
            return self.config["max_iters"]
        p = self.config["confidence"]; w = inlier_ratio; k = self.get_min_samples()
        try:
            denom = np.log(1 - w ** k)
            if denom >= 0:
                return self.config["max_iters"]
            return max(1, min(int(np.log(1 - p) / denom), self.config["max_iters"]))
        except Exception:
            return self.config["max_iters"]

    def _failed(self, start: float, reason: str) -> RANSACResult:
        dt = time.time() - start
        return RANSACResult(
            inlier_mask=[],
            num_iterations=0,
            fundamental_matrix=None,
            essential_matrix=None,
            rotation=None,
            translation=None,
            confidence=0.0,
            ransac_time=dt,
            min_samples=self.get_min_samples(),
        )

