#
# 功能: 定义评估指标和结果的数据模型。
#
from dataclasses import dataclass
from typing import List, Dict, Optional


@dataclass(frozen=True)
class PRCurveData:
    """精度-召回曲线数据"""

    algorithm: str
    precisions: List[float]
    recalls: List[float]
    thresholds: List[float]
    auc_score: float
    optimal_threshold: float
    optimal_precision: float
    optimal_recall: float
    f1_scores: List[float]
    max_f1_score: float

    def __post_init__(self):
        """验证PR曲线数据一致性"""
        assert self.algorithm.strip(), "算法名称不能为空"
        assert (
            len(self.precisions)
            == len(self.recalls)
            == len(self.thresholds)
            == len(self.f1_scores)
        ), "所有数组长度必须相等"
        assert 0.0 <= self.auc_score <= 1.0, "AUC分数必须在[0,1]范围内"
        assert 0.0 <= self.optimal_precision <= 1.0, "最优精度必须在[0,1]范围内"
        assert 0.0 <= self.optimal_recall <= 1.0, "最优召回率必须在[0,1]范围内"
        assert 0.0 <= self.max_f1_score <= 1.0, "最大F1分数必须在[0,1]范围内"

        # 验证数组值范围
        for p in self.precisions:
            assert 0.0 <= p <= 1.0, f"精度值{p}超出范围[0,1]"
        for r in self.recalls:
            assert 0.0 <= r <= 1.0, f"召回率{r}超出范围[0,1]"
        for f1 in self.f1_scores:
            assert 0.0 <= f1 <= 1.0, f"F1分数{f1}超出范围[0,1]"


@dataclass(frozen=True)
class TrajectoryMetrics:
    """轨迹评估指标"""

    ate_rmse: float  # 绝对轨迹误差 RMSE
    ate_mean: float  # 绝对轨迹误差均值
    ate_median: float  # 绝对轨迹误差中位数
    ate_std: float  # 绝对轨迹误差标准差
    ate_min: float  # 绝对轨迹误差最小值
    ate_max: float  # 绝对轨迹误差最大值
    rpe_rmse: float  # 相对位姿误差 RMSE
    rpe_mean: float  # 相对位姿误差均值
    rpe_median: float  # 相对位姿误差中位数
    rpe_std: float  # 相对位姿误差标准差
    trajectory_length: float  # 轨迹总长度
    num_valid_poses: int  # 有效位姿数量

    def __post_init__(self):
        """验证轨迹指标数据有效性"""
        assert self.ate_rmse >= 0.0, "ATE RMSE不能为负"
        assert self.ate_std >= 0.0, "ATE标准差不能为负"
        assert self.ate_min >= 0.0, "ATE最小值不能为负"
        assert self.ate_max >= self.ate_min, "ATE最大值必须大于等于最小值"
        assert self.rpe_rmse >= 0.0, "RPE RMSE不能为负"
        assert self.rpe_std >= 0.0, "RPE标准差不能为负"
        assert self.trajectory_length >= 0.0, "轨迹长度不能为负"
        assert self.num_valid_poses >= 0, "有效位姿数不能为负"


@dataclass(frozen=True)
class MatchingMetrics:
    """特征匹配指标"""

    avg_matches: float
    avg_inliers: float
    avg_inlier_ratio: float
    avg_match_score: float
    avg_reprojection_error: float

    def __post_init__(self):
        """验证匹配指标数据有效性"""
        assert self.avg_matches >= 0.0, "平均匹配数不能为负"
        assert self.avg_inliers >= 0.0, "平均内点数不能为负"
        assert 0.0 <= self.avg_inlier_ratio <= 1.0, "平均内点比例必须在[0,1]范围内"
        assert self.avg_match_score >= 0.0, "平均匹配分数不能为负"
        assert self.avg_reprojection_error >= 0.0, "平均重投影误差不能为负"


@dataclass(frozen=True)
class RANSACMetrics:
    """RANSAC算法指标"""

    avg_iterations: float
    std_iterations: float
    min_iterations: int
    max_iterations: int
    convergence_rate: float
    avg_inlier_ratio: float
    success_rate: float
    avg_processing_time_ms: float

    def __post_init__(self):
        """验证RANSAC指标数据有效性"""
        assert self.avg_iterations >= 0.0, "平均迭代次数不能为负"
        assert self.std_iterations >= 0.0, "迭代次数标准差不能为负"
        assert self.min_iterations >= 0, "最小迭代次数不能为负"
        assert (
            self.max_iterations >= self.min_iterations
        ), "最大迭代次数必须大于等于最小迭代次数"
        assert 0.0 <= self.convergence_rate <= 1.0, "收敛率必须在[0,1]范围内"
        assert 0.0 <= self.avg_inlier_ratio <= 1.0, "平均内点比例必须在[0,1]范围内"
        assert 0.0 <= self.success_rate <= 1.0, "成功率必须在[0,1]范围内"
        assert self.avg_processing_time_ms >= 0.0, "平均处理时间不能为负"


@dataclass(frozen=True)
class AlgorithmMetrics:
    """单个算法的综合指标"""

    algorithm_key: str  # e.g., "SIFT_STANDARD_sequence01"
    feature_type: str
    ransac_type: str
    trajectory: Optional[TrajectoryMetrics]
    matching: MatchingMetrics
    ransac: RANSACMetrics
    avg_frame_time_ms: float
    total_time_s: float
    fps: float
    success_rate: float
    failure_reasons: Dict[str, int]
    total_frames: int
    successful_frames: int
    failed_frames: int

    def __post_init__(self):
        """验证算法指标数据有效性"""
        assert self.algorithm_key.strip(), "算法键不能为空"
        assert self.feature_type.strip(), "特征类型不能为空"
        assert self.ransac_type.strip(), "RANSAC类型不能为空"
        assert self.avg_frame_time_ms >= 0.0, "平均帧处理时间不能为负"
        assert self.total_time_s >= 0.0, "总时间不能为负"
        assert self.fps >= 0.0, "帧率不能为负"
        assert 0.0 <= self.success_rate <= 1.0, "成功率必须在[0,1]范围内"
        assert self.total_frames >= 0, "总帧数不能为负"
        assert self.successful_frames >= 0, "成功帧数不能为负"
        assert self.failed_frames >= 0, "失败帧数不能为负"
        assert (
            self.successful_frames + self.failed_frames == self.total_frames
        ), "成功和失败帧数之和必须等于总帧数"

        # 验证失败原因计数
        total_failures = sum(self.failure_reasons.values())
        if total_failures > 0:
            assert total_failures <= self.failed_frames, "失败原因统计不能超过失败帧数"

    @property
    def efficiency_score(self) -> float:
        """计算效率分数（成功率 * 帧率）"""
        return self.success_rate * self.fps

    @property
    def has_trajectory_evaluation(self) -> bool:
        """是否包含轨迹评估"""
        return self.trajectory is not None
