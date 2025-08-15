#
# 功能: 定义匹配和RANSAC度量计算函数。
#
from typing import List, Optional
import numpy as np
import logging
from src.models.frame import FrameResult
from src.models.experiment import AlgorithmRun
from src.models.evaluation import (
    MatchingMetrics,
    RANSACMetrics,
    TrajectoryMetrics,
    AlgorithmMetrics,
)

logger = logging.getLogger(__name__)


class MetricsCalculator:
    """指标计算器 - 计算各种性能指标"""

    def calculate_algorithm_metrics_streaming(
        self, algorithm_run: AlgorithmRun, frame_results_generator, frame_count: int
    ) -> AlgorithmMetrics:
        """流式计算算法指标，避免内存溢出"""
        try:
            # 初始化累积变量
            total_frames = 0
            successful_frames = 0
            total_time = 0.0
            failure_reasons: dict[str, int] = {}

            # 累积指标数据
            all_matches = []
            all_inlier_ratios = []
            all_pose_errors = []
            all_reprojection_errors = []

            # RANSAC相关数据
            all_iterations = []
            all_processing_times = []
            successful_ransac = 0
            total_ransac_attempts = 0

            # 流式处理每一帧
            for frame_result in frame_results_generator:
                total_frames += 1
                total_time += frame_result.processing_time

                if frame_result.status == "SUCCESS":
                    successful_frames += 1

                    # 收集匹配数据
                    if frame_result.num_matches > 0:
                        all_matches.append(frame_result.num_matches)
                    if frame_result.inlier_ratio is not None:
                        all_inlier_ratios.append(frame_result.inlier_ratio)

                    # 收集位姿误差数据
                    if frame_result.pose_error is not None:
                        all_pose_errors.append(frame_result.pose_error)
                    if frame_result.reprojection_errors is not None:
                        all_reprojection_errors.extend(frame_result.reprojection_errors)

                # 收集RANSAC数据（无论成功失败）
                if frame_result.ransac is not None:
                    total_ransac_attempts += 1
                    all_iterations.append(frame_result.ransac.num_iterations)
                    all_processing_times.append(frame_result.ransac.ransac_time * 1000)  # 转换为毫秒

                    if frame_result.ransac.confidence > 0.5:  # 简单的成功判断
                        successful_ransac += 1

                # 统计失败原因（对于所有非成功状态的帧）
                if frame_result.status != "SUCCESS":
                    reason = frame_result.status
                    failure_reasons[reason] = failure_reasons.get(reason, 0) + 1

            # 计算基本统计
            failed_frames = total_frames - successful_frames
            avg_frame_time = (
                (total_time / total_frames * 1000) if total_frames > 0 else 0
            )  # 转换为毫秒
            fps = 1.0 / (total_time / total_frames) if total_time > 0 else 0
            success_rate = successful_frames / total_frames if total_frames > 0 else 0

            # 计算各种指标
            matching_metrics = (
                self._compute_matching_metrics_from_data(all_matches, all_inlier_ratios)
                if hasattr(self, "_compute_matching_metrics_from_data")
                else self.compute_matching_metrics([])
            )
            ransac_metrics = self._compute_ransac_metrics_from_data(
                all_inlier_ratios, all_iterations, all_processing_times,
                successful_ransac, total_ransac_attempts
            )
            trajectory_metrics = self._compute_trajectory_metrics_from_data(
                all_pose_errors
            )

            return AlgorithmMetrics(
                algorithm_key=algorithm_run.algorithm_key,
                feature_type=algorithm_run.feature_type.value,
                ransac_type=algorithm_run.ransac_type.value,
                trajectory=trajectory_metrics,
                matching=matching_metrics,
                ransac=ransac_metrics,
                avg_frame_time_ms=avg_frame_time,
                total_time_s=total_time,
                fps=fps,
                success_rate=success_rate,
                failure_reasons=failure_reasons,
                total_frames=total_frames,
                successful_frames=successful_frames,
                failed_frames=failed_frames,
            )

        except Exception as e:
            logger.error(f"流式计算算法指标失败: {e}")
            raise

    def calculate_algorithm_metrics(
        self, algorithm_run: AlgorithmRun, frame_results: List[FrameResult]
    ) -> AlgorithmMetrics:
        """计算算法的完整指标"""
        try:
            # 过滤有效的帧结果
            valid_frames = [f for f in frame_results if f.status == "SUCCESS"]

            # 计算基本统计
            total_frames = len(frame_results)
            successful_frames = len(valid_frames)
            failed_frames = total_frames - successful_frames

            # 计算时间指标
            total_time = sum(f.processing_time for f in frame_results)
            avg_frame_time = (
                (total_time / total_frames * 1000) if total_frames > 0 else 0
            )  # 转换为毫秒
            fps = 1.0 / (total_time / total_frames) if total_time > 0 else 0

            # 计算成功率
            success_rate = successful_frames / total_frames if total_frames > 0 else 0

            # 计算各种指标
            matching_metrics = self.compute_matching_metrics(valid_frames)
            ransac_metrics = self.compute_ransac_metrics(valid_frames)
            trajectory_metrics = self.compute_trajectory_metrics(valid_frames)

            # 统计失败原因
            failure_reasons: dict[str, int] = {}
            for frame in frame_results:
                if frame.status != "SUCCESS":
                    reason = frame.status
                    failure_reasons[reason] = failure_reasons.get(reason, 0) + 1

            return AlgorithmMetrics(
                algorithm_key=algorithm_run.algorithm_key,
                feature_type=algorithm_run.feature_type.value,
                ransac_type=algorithm_run.ransac_type.value,
                trajectory=trajectory_metrics,
                matching=matching_metrics,
                ransac=ransac_metrics,
                avg_frame_time_ms=avg_frame_time,
                total_time_s=total_time,
                fps=fps,
                success_rate=success_rate,
                failure_reasons=failure_reasons,
                total_frames=total_frames,
                successful_frames=successful_frames,
                failed_frames=failed_frames,
            )

        except Exception as e:
            logger.error(f"计算算法指标失败: {e}")
            raise

    def compute_matching_metrics(
        self, frame_results: List[FrameResult]
    ) -> MatchingMetrics:
        """计算匹配指标"""
        if not frame_results:
            return MatchingMetrics(
                avg_matches=0.0,
                avg_inliers=0.0,
                avg_inlier_ratio=0.0,
                avg_match_score=0.0,
                avg_reprojection_error=0.0,
            )

        try:
            # 收集匹配数据
            matches_counts = []
            inliers_counts = []
            inlier_ratios = []
            match_scores = []
            reprojection_errors = []

            for frame in frame_results:
                if frame.matches and frame.ransac:
                    matches_counts.append(frame.num_matches)
                    inliers_counts.append(frame.num_inliers)
                    inlier_ratios.append(frame.inlier_ratio)

                    # 计算平均匹配分数
                    if frame.matches.scores:
                        match_scores.extend(frame.matches.scores)

                    # 收集重投影误差
                    if frame.reprojection_errors:
                        reprojection_errors.extend(frame.reprojection_errors)

            return MatchingMetrics(
                avg_matches=float(np.mean(matches_counts)) if matches_counts else 0.0,
                avg_inliers=float(np.mean(inliers_counts)) if inliers_counts else 0.0,
                avg_inlier_ratio=float(np.mean(inlier_ratios)) if inlier_ratios else 0.0,
                avg_match_score=float(np.mean(match_scores)) if match_scores else 0.0,
                avg_reprojection_error=(
                    float(np.mean(reprojection_errors)) if reprojection_errors else 0.0
                ),
            )

        except Exception as e:
            logger.error(f"计算匹配指标失败: {e}")
            return MatchingMetrics(
                avg_matches=0.0,
                avg_inliers=0.0,
                avg_inlier_ratio=0.0,
                avg_match_score=0.0,
                avg_reprojection_error=0.0,
            )

    def compute_ransac_metrics(self, frame_results: List[FrameResult]) -> RANSACMetrics:
        """计算RANSAC指标"""
        if not frame_results:
            return RANSACMetrics(
                avg_iterations=0.0,
                std_iterations=0.0,
                min_iterations=0,
                max_iterations=0,
                convergence_rate=0.0,
                avg_inlier_ratio=0.0,
                success_rate=0.0,
                avg_processing_time_ms=0.0,
            )

        try:
            # 收集RANSAC数据
            iterations = []
            inlier_ratios = []
            processing_times = []
            successful_ransac = 0

            for frame in frame_results:
                if frame.ransac:
                    iterations.append(frame.ransac.num_iterations)
                    inlier_ratios.append(frame.inlier_ratio)
                    processing_times.append(
                        frame.ransac.ransac_time * 1000
                    )  # 转换为毫秒

                    if frame.ransac.confidence > 0.5:  # 简单的成功判断
                        successful_ransac += 1

            total_ransac_attempts = len(
                [f for f in frame_results if f.ransac is not None]
            )

            return RANSACMetrics(
                avg_iterations=float(np.mean(iterations)) if iterations else 0.0,
                std_iterations=float(np.std(iterations)) if iterations else 0.0,
                min_iterations=int(np.min(iterations)) if iterations else 0,
                max_iterations=int(np.max(iterations)) if iterations else 0,
                convergence_rate=(
                    float(successful_ransac) / float(total_ransac_attempts)
                    if total_ransac_attempts > 0
                    else 0.0
                ),
                avg_inlier_ratio=float(np.mean(inlier_ratios)) if inlier_ratios else 0.0,
                success_rate=(
                    float(successful_ransac) / float(len(frame_results)) if frame_results else 0.0
                ),
                avg_processing_time_ms=(
                    float(np.mean(processing_times)) if processing_times else 0.0
                ),
            )

        except Exception as e:
            logger.error(f"计算RANSAC指标失败: {e}")
            return RANSACMetrics(
                avg_iterations=0.0,
                std_iterations=0.0,
                min_iterations=0,
                max_iterations=0,
                convergence_rate=0.0,
                avg_inlier_ratio=0.0,
                success_rate=0.0,
                avg_processing_time_ms=0.0,
            )

    def compute_trajectory_metrics(
        self, frame_results: List[FrameResult]
    ) -> Optional[TrajectoryMetrics]:
        """计算轨迹指标"""
        # 过滤有地面真值的帧
        frames_with_gt = [
            f
            for f in frame_results
            if f.estimated_pose is not None and f.ground_truth_pose is not None
        ]

        if len(frames_with_gt) < 2:
            logger.warning("没有足够的地面真值数据来计算轨迹指标")
            return None

        try:
            # 计算ATE (Absolute Trajectory Error)
            ate_errors = []
            for frame in frames_with_gt:
                est_pose = frame.estimated_pose
                gt_pose = frame.ground_truth_pose
                if est_pose is None or gt_pose is None:
                    continue
                est_pos = est_pose[:3, 3]
                gt_pos = gt_pose[:3, 3]
                ate_error = float(np.linalg.norm(est_pos - gt_pos))
                ate_errors.append(ate_error)

            # 计算RPE (Relative Pose Error) - 简化版本
            rpe_errors = []
            for i in range(1, len(frames_with_gt)):
                # 计算相对位姿误差
                prev_frame = frames_with_gt[i - 1]
                curr_frame = frames_with_gt[i]

                # 估计的相对位姿（前置判空保证非 None）
                prev_est = prev_frame.estimated_pose
                curr_est = curr_frame.estimated_pose
                prev_gt = prev_frame.ground_truth_pose
                curr_gt = curr_frame.ground_truth_pose
                if prev_est is None or curr_est is None or prev_gt is None or curr_gt is None:
                    continue

                est_rel = (np.linalg.inv(prev_est) @ curr_est)
                gt_rel = (np.linalg.inv(prev_gt) @ curr_gt)

                # 计算相对位姿误差
                rel_error = float(np.linalg.norm((est_rel - gt_rel)[:3, 3]))
                rpe_errors.append(rel_error)

            # 计算轨迹长度
            trajectory_length = 0.0
            for i in range(1, len(frames_with_gt)):
                prev_gt = frames_with_gt[i - 1].ground_truth_pose
                curr_gt = frames_with_gt[i].ground_truth_pose
                if prev_gt is None or curr_gt is None:
                    continue
                prev_pos = prev_gt[:3, 3]
                curr_pos = curr_gt[:3, 3]
                trajectory_length += float(np.linalg.norm(curr_pos - prev_pos))

            return TrajectoryMetrics(
                ate_rmse=float(np.sqrt(np.mean(np.square(ate_errors)))),
                ate_mean=float(np.mean(ate_errors)),
                ate_median=float(np.median(ate_errors)),
                ate_std=float(np.std(ate_errors)),
                ate_min=float(np.min(ate_errors)),
                ate_max=float(np.max(ate_errors)),
                rpe_rmse=float(np.sqrt(np.mean(np.square(rpe_errors)))) if rpe_errors else 0.0,
                rpe_mean=float(np.mean(rpe_errors)) if rpe_errors else 0.0,
                rpe_median=float(np.median(rpe_errors)) if rpe_errors else 0.0,
                rpe_std=float(np.std(rpe_errors)) if rpe_errors else 0.0,
                trajectory_length=float(trajectory_length),
                num_valid_poses=len(frames_with_gt),
            )

        except Exception as e:
            logger.error(f"计算轨迹指标失败: {e}")
            return None

    def _compute_matching_metrics_from_data(
        self, all_matches: List[int], all_inlier_ratios: List[float]
    ) -> MatchingMetrics:
        """从累积数据计算匹配指标"""
        try:
            if not all_matches:
                return MatchingMetrics(
                    avg_matches=0.0,
                    avg_inliers=0.0,
                    avg_inlier_ratio=0.0,
                    avg_match_score=0.0,
                    avg_reprojection_error=0.0,
                )

            # 将扩展字段折叠为基本指标，兼容当前 MatchingMetrics 定义
            avg_matches = float(np.mean(all_matches)) if all_matches else 0.0
            avg_inlier_ratio = float(np.mean(all_inlier_ratios)) if all_inlier_ratios else 0.0
            return MatchingMetrics(
                avg_matches=avg_matches,
                avg_inliers=float(avg_matches * avg_inlier_ratio),
                avg_inlier_ratio=avg_inlier_ratio,
                avg_match_score=0.0,
                avg_reprojection_error=0.0,
            )
        except Exception as e:
            logger.error(f"计算匹配指标失败: {e}")
            return MatchingMetrics(
                avg_matches=0.0,
                avg_inliers=0.0,
                avg_inlier_ratio=0.0,
                avg_match_score=0.0,
                avg_reprojection_error=0.0,
            )

    def _compute_ransac_metrics_from_data(
        self,
        all_inlier_ratios: List[float],
        all_iterations: List[int],
        all_processing_times: List[float],
        successful_ransac: int,
        total_ransac_attempts: int
    ) -> RANSACMetrics:
        """从累积数据计算RANSAC指标"""
        try:
            if not all_inlier_ratios and not all_iterations:
                return RANSACMetrics(
                    avg_iterations=0.0,
                    std_iterations=0.0,
                    min_iterations=0,
                    max_iterations=0,
                    convergence_rate=0.0,
                    avg_inlier_ratio=0.0,
                    success_rate=0.0,
                    avg_processing_time_ms=0.0,
                )

            # 基于真实数据计算RANSAC指标
            return RANSACMetrics(
                avg_iterations=float(np.mean(all_iterations)) if all_iterations else 0.0,
                std_iterations=float(np.std(all_iterations)) if all_iterations else 0.0,
                min_iterations=int(np.min(all_iterations)) if all_iterations else 0,
                max_iterations=int(np.max(all_iterations)) if all_iterations else 0,
                convergence_rate=(
                    float(successful_ransac) / float(total_ransac_attempts)
                    if total_ransac_attempts > 0
                    else 0.0
                ),
                avg_inlier_ratio=float(np.mean(all_inlier_ratios)) if all_inlier_ratios else 0.0,
                success_rate=(
                    float(successful_ransac) / float(total_ransac_attempts)
                    if total_ransac_attempts > 0
                    else 0.0
                ),
                avg_processing_time_ms=(
                    float(np.mean(all_processing_times)) if all_processing_times else 0.0
                ),
            )
        except Exception as e:
            logger.error(f"计算RANSAC指标失败: {e}")
            return RANSACMetrics(
                avg_iterations=0.0,
                std_iterations=0.0,
                min_iterations=0,
                max_iterations=0,
                convergence_rate=0.0,
                avg_inlier_ratio=0.0,
                success_rate=0.0,
                avg_processing_time_ms=0.0,
            )

    def _compute_trajectory_metrics_from_data(
        self, all_pose_errors: List[float]
    ) -> Optional[TrajectoryMetrics]:
        """从累积数据计算轨迹指标"""
        try:
            if len(all_pose_errors) < 2:
                return None

            return TrajectoryMetrics(
                ate_rmse=float(np.sqrt(np.mean(np.square(all_pose_errors)))),
                ate_mean=float(np.mean(all_pose_errors)),
                ate_median=float(np.median(all_pose_errors)),
                ate_std=float(np.std(all_pose_errors)),
                ate_min=float(np.min(all_pose_errors)),
                ate_max=float(np.max(all_pose_errors)),
                rpe_rmse=float(np.sqrt(np.mean(np.square(all_pose_errors)))),  # 简化计算
                rpe_mean=float(np.mean(all_pose_errors)),  # 简化计算
                rpe_median=float(np.median(all_pose_errors)),  # 简化计算
                rpe_std=float(np.std(all_pose_errors)),  # 简化计算
                trajectory_length=float(len(all_pose_errors) * 0.1),  # 简化计算
                num_valid_poses=len(all_pose_errors),
            )
        except Exception as e:
            logger.error(f"计算轨迹指标失败: {e}")
            return None
