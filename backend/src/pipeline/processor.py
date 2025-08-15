#
# 功能: 封装处理一对连续帧的完整流程。
#
import time
import logging
from typing import Optional, Tuple
import numpy as np
from src.core.features.base import FeatureExtractor
from src.core.features.matcher import FeatureMatcher
from src.core.ransac.base import RANSACEstimator
from src.models.frame import FrameResult, FrameFeatures, FrameMatches, RANSACResult
from src.models.types import Point2D, Pose

logger = logging.getLogger(__name__)


class FrameProcessor:
    """帧对处理器 - 执行完整的视觉里程计处理流程"""

    def __init__(
        self,
        extractor: FeatureExtractor,
        matcher: FeatureMatcher,
        estimator: RANSACEstimator,
        calibration: np.ndarray,
    ):
        """
        初始化帧处理器

        Args:
            extractor: 特征提取器
            matcher: 特征匹配器
            estimator: RANSAC位姿估计器
            calibration: 相机内参矩阵 (3x3)
        """
        self.extractor = extractor
        self.matcher = matcher
        self.estimator = estimator
        self.calibration = calibration.copy()

        # 验证相机内参
        if calibration.shape != (3, 3):
            raise ValueError(f"相机内参矩阵必须是3x3，当前形状: {calibration.shape}")

        # 存储前一帧的特征用于匹配
        self._prev_features: Optional[FrameFeatures] = None
        self._prev_frame_id: Optional[int] = None

        # 累积位姿（从第一帧开始的累积变换）
        self._cumulative_pose = np.eye(4)

        logger.info("初始化帧处理器完成")

    def process_frame_pair(
        self,
        frame1: np.ndarray,
        frame2: np.ndarray,
        frame_id: int,
        timestamp: float,
        ground_truth_pose: Optional[Pose] = None,
    ) -> FrameResult:
        """
        处理一对连续帧

        Args:
            frame1: 前一帧图像 (H, W, C) 或 (H, W)
            frame2: 当前帧图像 (H, W, C) 或 (H, W)
            frame_id: 当前帧ID
            timestamp: 时间戳
            ground_truth_pose: 地面真值位姿（可选）

        Returns:
            FrameResult: 完整的帧处理结果
        """
        start_time = time.perf_counter()

        try:
            # 步骤1: 提取当前帧特征
            logger.debug(f"处理帧 {frame_id}: 开始特征提取")
            current_features = self._extract_features(frame2, frame_id)

            # 如果没有前一帧特征，初始化并返回
            if self._prev_features is None:
                if current_features is None:
                    processing_time = max(time.perf_counter() - start_time, 1e-6)
                    return self._create_failed_frame_result(
                        frame_id, timestamp, "FEATURE_EXTRACTION_FAILED", processing_time, ground_truth_pose
                    )
                self._prev_features = current_features
                self._prev_frame_id = frame_id
                return self._create_initial_frame_result(
                    frame_id, timestamp, current_features, ground_truth_pose, start_time
                )

            # 步骤2: 特征匹配（含稳健后处理）
            logger.debug(f"处理帧 {frame_id}: 开始特征匹配")
            if self._prev_features is None or current_features is None:
                # 无法匹配，返回失败帧
                processing_time = max(time.perf_counter() - start_time, 1e-6)
                return self._create_failed_frame_result(
                    frame_id, timestamp, "FEATURE_EXTRACTION_FAILED", processing_time, ground_truth_pose
                )
            matches = self._match_features(
                self._prev_features, current_features, frame_id
            )
            # 稳健匹配后处理（GMS优先；失败则对称+MAD）
            try:
                if matches and len(matches.matches) > 0:
                    from src.core.features.post_filter import apply_gms_filter
                    # 估计图像尺寸：若无法获取，使用 keypoint 最大坐标近似
                    h1 = h2 = w1 = w2 = 0
                    # 无图像对象可用，近似处理：用关键点边界估计
                    def _estimate_shape(kps):
                        if not kps:
                            return (480, 640)
                        xs = [p[0] for p in kps]; ys = [p[1] for p in kps]
                        return (int(max(ys) + 1), int(max(xs) + 1))
                    shape1 = _estimate_shape(self._prev_features.keypoints)
                    shape2 = _estimate_shape(current_features.keypoints)
                    # 从统一配置读取后处理参数
                    try:
                        from src.config.manager import get_config
                        pf = get_config().experiment.post_filter
                        gms_params = pf.get("gms", {}) if pf.get("enabled", True) else {}
                    except Exception:
                        gms_params = {"with_rotation": False, "with_scale": False, "threshold_factor": 6}
                    matches = apply_gms_filter(
                        shape1, shape2,
                        self._prev_features.keypoints,
                        current_features.keypoints,
                        matches,
                        with_rotation=bool(gms_params.get("with_rotation", False)),
                        with_scale=bool(gms_params.get("with_scale", False)),
                        threshold_factor=int(gms_params.get("threshold_factor", 6)),
                    )
            except Exception as _e:
                logger.debug(f"匹配后处理跳过: {_e}")

            # 步骤3: RANSAC位姿估计
            logger.debug(f"处理帧 {frame_id}: 开始位姿估计")
            ransac_result = None
            estimated_pose = None
            if matches is not None and self._prev_features is not None:
                ransac_result, estimated_pose = self._estimate_pose(
                    self._prev_features, current_features, matches, frame_id
                )

            # 步骤4: 计算性能指标
            processing_time = max(time.perf_counter() - start_time, 1e-6)
            pose_error = self._calculate_pose_error(estimated_pose, ground_truth_pose)

            # 步骤5: 更新累积位姿
            if estimated_pose is not None:
                self._cumulative_pose = self._cumulative_pose @ estimated_pose

            # 步骤6: 构建完整结果
            result = FrameResult(
                frame_id=frame_id,
                timestamp=timestamp,
                features=current_features,
                matches=matches,
                ransac=ransac_result,
                num_matches=len(matches.matches) if matches else 0,
                num_inliers=ransac_result.num_inliers if ransac_result else 0,
                inlier_ratio=ransac_result.inlier_ratio if ransac_result else 0.0,
                estimated_pose=(
                    self._cumulative_pose.copy() if estimated_pose is not None else None
                ),
                ground_truth_pose=(
                    ground_truth_pose.copy() if ground_truth_pose is not None else None
                ),
                processing_time=processing_time,
                status="SUCCESS" if estimated_pose is not None else "RANSAC_FAILED",
                pose_error=pose_error,
                reprojection_errors=(
                    self._calculate_reprojection_errors(
                        self._prev_features, current_features, matches, ransac_result
                    )
                    if (self._prev_features is not None and current_features is not None and matches is not None)
                    else None
                ),
                error=None,
            )

            # 更新前一帧信息
            self._prev_features = current_features
            self._prev_frame_id = frame_id

            logger.debug(
                f"处理帧 {frame_id} 完成: {result.status}, 耗时 {processing_time:.3f}s"
            )
            return result

        except Exception as e:
            processing_time = max(time.perf_counter() - start_time, 1e-6)
            logger.error(f"处理帧 {frame_id} 失败: {e}")

            return self._create_failed_frame_result(
                frame_id, timestamp, str(e), processing_time, ground_truth_pose
            )

    def process_single_frame(
        self,
        frame: np.ndarray,
        frame_id: int,
        timestamp: float,
        ground_truth_pose: Optional[Pose] = None,
    ) -> FrameResult:
        """
        处理单帧（用于序列处理）

        Args:
            frame: 当前帧图像
            frame_id: 帧ID
            timestamp: 时间戳
            ground_truth_pose: 地面真值位姿（可选）

        Returns:
            FrameResult: 处理结果
        """
        if self._prev_features is None or self._prev_frame_id is None:
            # 第一帧，只提取特征
            start_time = time.perf_counter()
            features = self._extract_features(frame, frame_id)
            if features is None:
                processing_time = max(time.perf_counter() - start_time, 1e-6)
                return self._create_failed_frame_result(
                    frame_id, timestamp, "FEATURE_EXTRACTION_FAILED", processing_time, ground_truth_pose
                )
            self._prev_features = features
            self._prev_frame_id = frame_id

            return self._create_initial_frame_result(
                frame_id, timestamp, features, ground_truth_pose, start_time
            )
        else:
            # 使用虚拟的前一帧（实际上使用存储的特征）
            return self.process_frame_pair(
                np.zeros_like(frame), frame, frame_id, timestamp, ground_truth_pose
            )

    def reset(self):
        """重置处理器状态"""
        self._prev_features = None
        self._prev_frame_id = None
        self._cumulative_pose = np.eye(4)
        logger.info("帧处理器状态已重置")

    def get_cumulative_pose(self) -> np.ndarray:
        """获取累积位姿"""
        return self._cumulative_pose.copy()

    def _extract_features(
        self, image: np.ndarray, frame_id: int
    ) -> Optional[FrameFeatures]:
        """提取图像特征"""
        try:
            features = self.extractor.extract(image)
            if len(features.keypoints) == 0:
                logger.warning(f"帧 {frame_id} 未检测到特征点")
            return features
        except Exception as e:
            logger.error(f"帧 {frame_id} 特征提取失败: {e}")
            return None

    def _match_features(
        self, features1: FrameFeatures, features2: FrameFeatures, frame_id: int
    ) -> Optional[FrameMatches]:
        """匹配两帧特征"""
        try:
            matches = self.matcher.match(features1, features2)
            if len(matches.matches) == 0:
                logger.warning(f"帧 {frame_id} 未找到特征匹配")
            return matches
        except Exception as e:
            logger.error(f"帧 {frame_id} 特征匹配失败: {e}")
            return None

    def _estimate_pose(
        self,
        features1: FrameFeatures,
        features2: FrameFeatures,
        matches: FrameMatches,
        frame_id: int,
    ) -> Tuple[Optional[RANSACResult], Optional[np.ndarray]]:
        """使用RANSAC估计位姿"""
        if not matches or len(matches.matches) == 0:
            return None, None

        try:
            ransac_result = self.estimator.estimate(
                features1.keypoints, features2.keypoints, matches, self.calibration
            )

            # 从RANSAC结果构造相对位姿
            if (
                ransac_result.rotation is not None
                and ransac_result.translation is not None
            ):
                relative_pose = np.eye(4)
                relative_pose[:3, :3] = ransac_result.rotation
                relative_pose[:3, 3] = ransac_result.translation.flatten()
                return ransac_result, relative_pose
            else:
                logger.warning(f"帧 {frame_id} RANSAC未能估计有效位姿")
                return ransac_result, None

        except Exception as e:
            logger.error(f"帧 {frame_id} 位姿估计失败: {e}")
            return None, None

    def _calculate_pose_error(
        self,
        estimated_pose: Optional[np.ndarray],
        ground_truth_pose: Optional[np.ndarray],
    ) -> Optional[float]:
        """计算位姿误差（平移距离）"""
        if estimated_pose is None or ground_truth_pose is None:
            return None

        try:
            est_translation = estimated_pose[:3, 3]
            gt_translation = ground_truth_pose[:3, 3]
            error = np.linalg.norm(est_translation - gt_translation)
            return float(error)
        except Exception as e:
            logger.warning(f"位姿误差计算失败: {e}")
            return None

    def _calculate_reprojection_errors(
        self,
        features1: FrameFeatures,
        features2: FrameFeatures,
        matches: FrameMatches,
        ransac_result: Optional[RANSACResult],
    ) -> Optional[list]:
        """计算真实的几何重投影误差"""
        if (
            not matches
            or not ransac_result
            or len(matches.matches) == 0
            or ransac_result.rotation is None
            or ransac_result.translation is None
        ):
            return None

        try:
            # 验证相机内参
            if self.calibration.shape != (3, 3):
                logger.warning("相机内参矩阵形状不正确")
                return None

            # 获取旋转和平移
            R = ransac_result.rotation
            t = ransac_result.translation

            # 确保平移向量是列向量 (3, 1)
            if t.shape == (3,):
                t = t.reshape(3, 1)
            elif t.shape != (3, 1):
                logger.warning(f"平移向量形状不正确: {t.shape}")
                return None

            # 相机内参
            K = self.calibration
            K_inv = np.linalg.inv(K)

            errors = []
            for i, (idx1, idx2) in enumerate(matches.matches):
                try:
                    # 边界检查
                    if idx1 >= len(features1.keypoints) or idx2 >= len(features2.keypoints):
                        logger.warning(f"匹配索引越界: {idx1}, {idx2}")
                        errors.append(float('inf'))  # 标记为无效
                        continue

                    # 获取匹配点坐标
                    p1 = np.array([features1.keypoints[idx1][0], features1.keypoints[idx1][1], 1.0])
                    p2 = np.array([features2.keypoints[idx2][0], features2.keypoints[idx2][1], 1.0])

                    # 将第一帧点转换为归一化坐标
                    p1_norm = K_inv @ p1

                    # 使用R和t将点投影到第二帧的归一化坐标系
                    # p2_norm = R @ p1_norm + t
                    p2_proj_norm = R @ p1_norm + t.flatten()

                    # 检查深度是否为正
                    if p2_proj_norm[2] <= 0:
                        errors.append(float('inf'))  # 点在相机后方
                        continue

                    # 投影到第二帧的像素坐标
                    p2_proj_norm_homogeneous = p2_proj_norm / p2_proj_norm[2]  # 归一化
                    p2_proj_pixel = K @ p2_proj_norm_homogeneous

                    # 计算重投影误差（欧几里得距离）
                    error = np.sqrt((p2_proj_pixel[0] - p2[0])**2 + (p2_proj_pixel[1] - p2[1])**2)
                    errors.append(float(error))

                except Exception as e:
                    logger.debug(f"计算匹配对 {i} 的重投影误差失败: {e}")
                    errors.append(float('inf'))  # 标记为无效

            # 过滤无效误差并返回
            valid_errors = [e for e in errors if not np.isinf(e) and not np.isnan(e)]
            if not valid_errors:
                logger.warning("没有有效的重投影误差")
                return None

            return valid_errors

        except Exception as e:
            logger.warning(f"重投影误差计算失败: {e}")
            return None

    def _create_initial_frame_result(
        self,
        frame_id: int,
        timestamp: float,
        features: FrameFeatures,
        ground_truth_pose: Optional[np.ndarray],
        start_time: float,
    ) -> FrameResult:
        """创建初始帧结果（第一帧）"""
        processing_time = max(time.perf_counter() - start_time, 1e-6)

        return FrameResult(
            frame_id=frame_id,
            timestamp=timestamp,
            features=features,
            matches=None,
            ransac=None,
            num_matches=0,
            num_inliers=0,
            inlier_ratio=0.0,
            estimated_pose=self._cumulative_pose.copy(),  # 初始位姿为单位矩阵
            ground_truth_pose=(
                ground_truth_pose.copy() if ground_truth_pose is not None else None
            ),
            processing_time=processing_time,
            status="SUCCESS",
            pose_error=self._calculate_pose_error(
                self._cumulative_pose, ground_truth_pose
            ),
            reprojection_errors=None,
            error=None,
        )

    def _create_failed_frame_result(
        self,
        frame_id: int,
        timestamp: float,
        error_msg: str,
        processing_time: float,
        ground_truth_pose: Optional[np.ndarray],
    ) -> FrameResult:
        """创建失败的帧结果"""
        return FrameResult(
            frame_id=frame_id,
            timestamp=timestamp,
            features=None,
            matches=None,
            ransac=None,
            num_matches=0,
            num_inliers=0,
            inlier_ratio=0.0,
            estimated_pose=None,
            ground_truth_pose=(
                ground_truth_pose.copy() if ground_truth_pose is not None else None
            ),
            processing_time=processing_time,
            status="FEATURE_EXTRACTION_FAILED",
            pose_error=None,
            reprojection_errors=None,
            error=error_msg,
        )
