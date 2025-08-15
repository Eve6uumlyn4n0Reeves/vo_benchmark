#
# 功能: 定义实验配置和摘要的数据模型。
#
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, TYPE_CHECKING
from pathlib import Path
from .types import FeatureType, RANSACType

if TYPE_CHECKING:
    from .metrics import TrajectoryMetrics, MatchingMetrics, RANSACMetrics


@dataclass(frozen=True)
class ExperimentConfig:
    """实验配置参数"""

    name: str
    dataset_path: Path
    output_dir: Path
    feature_types: List[FeatureType]
    ransac_types: List[RANSACType]
    sequences: List[str]
    num_runs: int
    parallel_jobs: int
    random_seed: int
    save_frame_data: bool
    save_descriptors: bool
    compute_pr_curves: bool
    analyze_ransac: bool
    ransac_success_threshold: float
    max_features: int
    feature_params: Dict[str, Any]
    ransac_threshold: float
    ransac_confidence: float
    ransac_max_iters: int

    def __post_init__(self):
        """验证配置参数的有效性"""
        assert self.name.strip(), "实验名称不能为空"
        assert self.dataset_path.exists(), f"数据集路径不存在: {self.dataset_path}"
        assert self.num_runs > 0, "运行次数必须大于0"
        assert self.parallel_jobs > 0, "并行作业数必须大于0"
        assert self.random_seed >= 0, "随机种子不能为负"
        assert (
            0.0 < self.ransac_success_threshold <= 1.0
        ), "RANSAC成功阈值必须在(0,1]范围内"
        assert self.max_features > 0, "最大特征数必须大于0"
        assert 0.0 < self.ransac_threshold, "RANSAC阈值必须大于0"
        assert 0.0 < self.ransac_confidence < 1.0, "RANSAC置信度必须在(0,1)范围内"
        assert self.ransac_max_iters > 0, "RANSAC最大迭代次数必须大于0"
        assert len(self.feature_types) > 0, "必须指定至少一个特征类型"
        assert len(self.ransac_types) > 0, "必须指定至少一个RANSAC类型"
        assert len(self.sequences) > 0, "必须指定至少一个序列"

    @property
    def total_algorithm_combinations(self) -> int:
        """算法组合总数"""
        return (
            len(self.feature_types)
            * len(self.ransac_types)
            * len(self.sequences)
            * self.num_runs
        )

    def validate_dataset_sequences(self, available_sequences: List[str]) -> None:
        """验证指定的序列是否在数据集中可用"""
        missing_sequences = set(self.sequences) - set(available_sequences)
        if missing_sequences:
            raise ValueError(f"以下序列在数据集中不可用: {missing_sequences}")


@dataclass(frozen=True)
class AlgorithmRun:
    """单个算法运行配置"""

    experiment_id: str
    algorithm_key: str
    feature_type: FeatureType
    ransac_type: RANSACType
    sequence: str
    run_number: int
    random_seed: Optional[int] = None

    def __post_init__(self):
        """验证运行配置"""
        assert self.experiment_id.strip(), "实验ID不能为空"
        assert self.algorithm_key.strip(), "算法键不能为空"
        assert self.sequence.strip(), "序列名不能为空"
        assert self.run_number >= 0, "运行编号不能为负"


@dataclass(frozen=True)
class ExperimentSummary:
    """实验执行结果摘要"""

    experiment_id: str
    timestamp: str
    config: ExperimentConfig
    total_runs: int
    successful_runs: int
    failed_runs: int
    algorithms_tested: List[str]
    sequences_processed: List[str]

    def __post_init__(self):
        """验证摘要数据"""
        assert self.experiment_id.strip(), "实验ID不能为空"
        assert self.total_runs >= 0, "总运行数不能为负"
        assert self.successful_runs >= 0, "成功运行数不能为负"
        assert self.failed_runs >= 0, "失败运行数不能为负"
        assert (
            self.successful_runs + self.failed_runs == self.total_runs
        ), "成功和失败运行数之和必须等于总运行数"

    @property
    def success_rate(self) -> float:
        """计算成功率"""
        if self.total_runs == 0:
            return 0.0
        return self.successful_runs / self.total_runs

    @property
    def failure_rate(self) -> float:
        """计算失败率"""
        return 1.0 - self.success_rate


@dataclass
class AlgorithmMetrics:
    """算法性能指标"""

    algorithm_key: str  # 算法运行的唯一标识
    feature_type: str  # 特征类型字符串值
    ransac_type: str  # RANSAC类型字符串值
    trajectory: "TrajectoryMetrics"  # 轨迹指标
    matching: "MatchingMetrics"  # 匹配指标
    ransac: "RANSACMetrics"  # RANSAC指标
    avg_frame_time_ms: float  # 平均帧处理时间(毫秒)
    total_time_s: float  # 总处理时间(秒)
    fps: float  # 帧率
    success_rate: float  # 成功率
    failure_reasons: Dict[str, int]  # 失败原因统计
    total_frames: int  # 总帧数
    successful_frames: int  # 成功帧数
    failed_frames: int  # 失败帧数
