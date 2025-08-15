"""API模式定义模块 - 请求响应模型

提供Pydantic模型用于API请求验证和响应序列化。
"""

from .request import CreateExperimentRequest
from .response import (
    TaskResponse,
    ExperimentResponse,
    AlgorithmResultResponse,
    FrameResultsResponse,
    PaginationInfo,
    ErrorResponse,
)

__all__ = [
    "CreateExperimentRequest",
    "TaskResponse",
    "ExperimentResponse",
    "AlgorithmResultResponse",
    "FrameResultsResponse",
    "PaginationInfo",
    "ErrorResponse",
]
