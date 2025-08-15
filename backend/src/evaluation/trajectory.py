#
# 功能: 定义轨迹评估函数。
#
from typing import List, Optional, Tuple
import numpy as np
import logging
from src.models.types import Pose
from src.models.evaluation import TrajectoryMetrics

logger = logging.getLogger(__name__)


class TrajectoryEvaluator:
    """轨迹评估器

    实现轨迹评估的各种指标，包括：
    - ATE (Absolute Trajectory Error) - 绝对轨迹误差
    - RPE (Relative Pose Error) - 相对位姿误差
    - 轨迹长度和统计信息
    """

    def __init__(self, align_trajectories: bool = True, scale_estimation: bool = False):
        """
        初始化轨迹评估器

        Args:
            align_trajectories: 是否对齐轨迹（使用Umeyama算法）
            scale_estimation: 是否估计尺度因子
        """
        self.align_trajectories = align_trajectories
        self.scale_estimation = scale_estimation

    def compute_metrics(
        self, ground_truth: List[Optional[Pose]], estimated: List[Optional[Pose]]
    ) -> Optional[TrajectoryMetrics]:
        """
        计算轨迹评估指标

        Args:
            ground_truth: 地面真值轨迹
            estimated: 估计轨迹

        Returns:
            轨迹评估指标，如果无法计算则返回None
        """
        try:
            # 过滤有效的位姿对
            valid_pairs = self._filter_valid_poses(ground_truth, estimated)

            if len(valid_pairs) < 2:
                logger.warning("有效位姿对数量不足，无法计算轨迹指标")
                return None

            gt_poses_tuple, est_poses_tuple = zip(*valid_pairs)
            gt_poses = list(gt_poses_tuple)
            est_poses = list(est_poses_tuple)

            # 对齐轨迹（如果启用）
            if self.align_trajectories:
                est_poses = self._align_trajectories(gt_poses, est_poses)

            # 计算ATE指标
            ate_errors = self._compute_ate(gt_poses, est_poses)

            # 计算RPE指标
            rpe_errors = self._compute_rpe(gt_poses, est_poses)

            # 计算轨迹长度
            trajectory_length = self._compute_trajectory_length(gt_poses)

            # 构造评估结果
            return TrajectoryMetrics(
                ate_rmse=np.sqrt(np.mean(ate_errors**2)),
                ate_mean=np.mean(ate_errors),
                ate_median=np.median(ate_errors),
                ate_std=np.std(ate_errors),
                ate_min=np.min(ate_errors),
                ate_max=np.max(ate_errors),
                rpe_rmse=(
                    np.sqrt(np.mean(rpe_errors**2)) if len(rpe_errors) > 0 else 0.0
                ),
                rpe_mean=np.mean(rpe_errors) if len(rpe_errors) > 0 else 0.0,
                rpe_median=np.median(rpe_errors) if len(rpe_errors) > 0 else 0.0,
                rpe_std=np.std(rpe_errors) if len(rpe_errors) > 0 else 0.0,
                trajectory_length=trajectory_length,
                num_valid_poses=len(valid_pairs),
            )

        except Exception as e:
            logger.error(f"计算轨迹指标失败: {e}")
            return None

    def _filter_valid_poses(
        self, ground_truth: List[Optional[Pose]], estimated: List[Optional[Pose]]
    ) -> List[Tuple[Pose, Pose]]:
        """过滤有效的位姿对"""
        valid_pairs = []

        min_length = min(len(ground_truth), len(estimated))

        for i in range(min_length):
            gt_i = ground_truth[i]
            est_i = estimated[i]
            if gt_i is not None and est_i is not None:
                # 验证位姿矩阵的有效性
                if self._is_valid_pose(gt_i) and self._is_valid_pose(est_i):
                    valid_pairs.append((gt_i, est_i))

        return valid_pairs

    def _is_valid_pose(self, pose: Pose) -> bool:
        """检查位姿矩阵是否有效"""
        if pose.shape != (4, 4):
            return False

        # 检查旋转矩阵是否正交
        R = pose[:3, :3]
        if not np.allclose(np.dot(R, R.T), np.eye(3), atol=1e-3):
            return False

        # 检查行列式是否为1
        if not np.allclose(np.linalg.det(R), 1.0, atol=1e-3):
            return False

        # 检查最后一行是否为[0, 0, 0, 1]
        if not np.allclose(pose[3, :], [0, 0, 0, 1], atol=1e-6):
            return False

        return True

    def _align_trajectories(
        self, gt_poses: List[Pose], est_poses: List[Pose]
    ) -> List[Pose]:
        """
        使用Umeyama算法对齐轨迹

        Args:
            gt_poses: 地面真值位姿列表
            est_poses: 估计位姿列表

        Returns:
            对齐后的估计位姿列表
        """
        try:
            # 提取位置信息
            gt_positions = np.array([pose[:3, 3] for pose in gt_poses])
            est_positions = np.array([pose[:3, 3] for pose in est_poses])

            # 计算质心
            gt_centroid = np.mean(gt_positions, axis=0)
            est_centroid = np.mean(est_positions, axis=0)

            # 去质心
            gt_centered = gt_positions - gt_centroid
            est_centered = est_positions - est_centroid

            # 计算协方差矩阵
            H = np.dot(est_centered.T, gt_centered)

            # SVD分解
            U, S, Vt = np.linalg.svd(H)

            # 计算旋转矩阵
            R = np.dot(Vt.T, U.T)

            # 确保旋转矩阵的行列式为正
            if np.linalg.det(R) < 0:
                Vt[-1, :] *= -1
                R = np.dot(Vt.T, U.T)

            # 计算尺度因子（如果启用）
            scale = 1.0
            if self.scale_estimation:
                num = np.sum(
                    np.linalg.norm(gt_centered, axis=1)
                    * np.linalg.norm(est_centered, axis=1)
                )
                den = np.sum(np.linalg.norm(est_centered, axis=1) ** 2)
                if den > 1e-8:
                    scale = num / den

            # 计算平移
            t = gt_centroid - scale * np.dot(R, est_centroid)

            # 构造变换矩阵
            T = np.eye(4)
            T[:3, :3] = scale * R
            T[:3, 3] = t

            # 应用变换到所有估计位姿
            aligned_poses = []
            for pose in est_poses:
                aligned_pose = np.dot(T, pose)
                aligned_poses.append(aligned_pose)

            return aligned_poses

        except Exception as e:
            logger.error(f"轨迹对齐失败: {e}")
            return est_poses  # 返回原始轨迹

    def _compute_ate(self, gt_poses: List[Pose], est_poses: List[Pose]) -> np.ndarray:
        """
        计算绝对轨迹误差 (ATE)

        ATE测量估计轨迹与真值轨迹之间的绝对位置差异
        """
        errors = []

        for gt_pose, est_pose in zip(gt_poses, est_poses):
            # 提取位置
            gt_pos = gt_pose[:3, 3]
            est_pos = est_pose[:3, 3]

            # 计算欧几里得距离
            error = np.linalg.norm(gt_pos - est_pos)
            errors.append(error)

        return np.array(errors)

    def _compute_rpe(
        self, gt_poses: List[Pose], est_poses: List[Pose], delta: int = 1
    ) -> np.ndarray:
        """
        计算相对位姿误差 (RPE)

        RPE测量相邻帧之间的相对运动误差

        Args:
            gt_poses: 地面真值位姿
            est_poses: 估计位姿
            delta: 帧间隔
        """
        errors = []

        for i in range(len(gt_poses) - delta):
            # 计算真值相对运动
            gt_rel = np.dot(np.linalg.inv(gt_poses[i]), gt_poses[i + delta])

            # 计算估计相对运动
            est_rel = np.dot(np.linalg.inv(est_poses[i]), est_poses[i + delta])

            # 计算相对误差
            error_pose = np.dot(np.linalg.inv(gt_rel), est_rel)

            # 提取平移误差
            trans_error = np.linalg.norm(error_pose[:3, 3])
            errors.append(trans_error)

        return np.array(errors)

    def _compute_trajectory_length(self, poses: List[Pose]) -> float:
        """计算轨迹总长度"""
        total_length: float = 0.0

        for i in range(1, len(poses)):
            pos1 = poses[i - 1][:3, 3]
            pos2 = poses[i][:3, 3]
            distance = float(np.linalg.norm(pos2 - pos1))
            total_length += distance

        return float(total_length)
