"""API异常处理模块

提供自定义异常类和统一的错误处理机制。
"""

from .base import (
    VOBenchmarkException,
    ValidationError,
    DatasetNotFoundError,
    ExperimentNotFoundError,
    TaskNotFoundError,
    ResourceExhaustedError,
    UnsupportedFeatureError,
    UnsupportedRANSACError,
)

from typing import Optional, Callable, Any

try:
    from .handlers import register_error_handlers as _register_error_handlers
    register_error_handlers: Optional[Callable[..., Any]] = _register_error_handlers
except ImportError:
    # handlers module may not exist yet
    register_error_handlers = None

__all__ = [
    "VOBenchmarkException",
    "ValidationError",
    "DatasetNotFoundError",
    "ExperimentNotFoundError",
    "TaskNotFoundError",
    "ResourceExhaustedError",
    "UnsupportedFeatureError",
    "UnsupportedRANSACError",
    "register_error_handlers",
]
