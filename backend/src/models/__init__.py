"""数据模型模块 - 定义核心数据结构

包含整个应用中使用的数据类型、枚举和数据类。
"""

from .types import (
    Point2D,
    Point3D,
    MatchPair,
    Pose,
    Rotation,
    Translation,
    FeatureType,
    RANSACType,
    TaskStatus,
    ErrorCode,
)
from .frame import FrameFeatures, FrameMatches, RANSACResult, FrameResult
from .experiment import ExperimentConfig, AlgorithmRun, ExperimentSummary
from .evaluation import (
    PRCurveData,
    TrajectoryMetrics,
    MatchingMetrics,
    RANSACMetrics,
    AlgorithmMetrics,
)

__all__ = [
    # types.py
    "Point2D",
    "Point3D",
    "MatchPair",
    "Pose",
    "Rotation",
    "Translation",
    "FeatureType",
    "RANSACType",
    "TaskStatus",
    "ErrorCode",
    # frame.py
    "FrameFeatures",
    "FrameMatches",
    "RANSACResult",
    "FrameResult",
    # experiment.py
    "ExperimentConfig",
    "AlgorithmRun",
    "ExperimentSummary",
    # evaluation.py
    "PRCurveData",
    "TrajectoryMetrics",
    "MatchingMetrics",
    "RANSACMetrics",
    "AlgorithmMetrics",
]
