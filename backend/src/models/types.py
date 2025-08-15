#
# 功能: 定义项目范围内的基本类型、枚举和类型别名。
#
from enum import Enum
from typing import Tuple, List, Optional
import numpy as np

# --- Type Aliases ---
Point2D = Tuple[float, float]
Point3D = Tuple[float, float, float]
MatchPair = Tuple[int, int]
Pose = np.ndarray  # 4x4齐次变换矩阵
Rotation = np.ndarray  # 3x3旋转矩阵
Translation = np.ndarray  # 3x1平移向量


# --- Enums ---
class FeatureType(str, Enum):
    SIFT = "SIFT"
    ORB = "ORB"
    AKAZE = "AKAZE"
    BRISK = "BRISK"
    KAZE = "KAZE"
    SURF = "SURF"  # 仅研究/非商用用途


class RANSACType(str, Enum):
    STANDARD = "STANDARD"
    PROSAC = "PROSAC"
    USAC_DEFAULT = "USAC_DEFAULT"
    USAC_MAGSAC = "USAC_MAGSAC"
    USAC_ACCURATE = "USAC_ACCURATE"
    RHO = "RHO"
    LMEDS = "LMEDS"


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ErrorCode(str, Enum):
    VALIDATION_ERROR = "VALIDATION_ERROR"
    DATASET_NOT_FOUND = "DATASET_NOT_FOUND"
    UNSUPPORTED_FEATURE = "UNSUPPORTED_FEATURE"
    UNSUPPORTED_RANSAC = "UNSUPPORTED_RANSAC"
    TASK_NOT_FOUND = "TASK_NOT_FOUND"
    EXPERIMENT_NOT_FOUND = "EXPERIMENT_NOT_FOUND"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    RESOURCE_EXHAUSTED = "RESOURCE_EXHAUSTED"
    PERMISSION_DENIED = "PERMISSION_DENIED"
