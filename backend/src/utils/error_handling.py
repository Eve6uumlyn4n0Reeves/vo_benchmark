#
# 功能: 增强的错误处理工具
#
import time
import logging
import functools
from typing import Any, Callable, Optional, Type, Union, List, Dict
from src.api.exceptions.base import VOBenchmarkException

logger = logging.getLogger(__name__)


class RetryableError(VOBenchmarkException):
    """可重试的错误"""

    pass


class FeatureExtractionError(RetryableError):
    """特征提取错误"""

    pass


class MatchingError(RetryableError):
    """特征匹配错误"""

    pass


class RANSACError(RetryableError):
    """RANSAC估计错误"""

    pass


class DatasetLoadError(VOBenchmarkException):
    """数据集加载错误"""

    pass


class StorageError(RetryableError):
    """存储错误"""

    pass


def retry_on_failure(
    max_retries: int = 3,
    delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: Union[Type[Exception], tuple] = Exception,
    on_retry: Optional[Callable] = None,
):
    """重试装饰器

    Args:
        max_retries: 最大重试次数
        delay: 初始延迟时间（秒）
        backoff_factor: 延迟时间倍增因子
        exceptions: 需要重试的异常类型
        on_retry: 重试时的回调函数
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception: Optional[BaseException] = None
            current_delay = delay

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e

                    if attempt == max_retries:
                        logger.error(
                            f"函数 {func.__name__} 在 {max_retries} 次重试后仍然失败: {e}"
                        )
                        raise

                    logger.warning(
                        f"函数 {func.__name__} 第 {attempt + 1} 次尝试失败: {e}, "
                        f"{current_delay:.1f}秒后重试"
                    )

                    if on_retry:
                        on_retry(attempt + 1, e)

                    time.sleep(current_delay)
                    current_delay *= backoff_factor

            # 理论上不会到达；兜底处理
            if last_exception is not None:
                raise last_exception
            raise RuntimeError("backoff_retry reached unexpected state without exception")

        return wrapper

    return decorator


def safe_execute(
    func: Callable,
    *args,
    default_return: Any = None,
    log_errors: bool = True,
    error_message: Optional[str] = None,
    **kwargs,
) -> Any:
    """安全执行函数，捕获异常并返回默认值

    Args:
        func: 要执行的函数
        *args: 函数参数
        default_return: 异常时的默认返回值
        log_errors: 是否记录错误日志
        error_message: 自定义错误消息
        **kwargs: 函数关键字参数
    """
    try:
        return func(*args, **kwargs)
    except Exception as e:
        if log_errors:
            message = error_message or f"执行函数 {func.__name__} 失败"
            logger.error(f"{message}: {e}")
        return default_return


def validate_input(
    value: Any,
    validators: List[Callable[[Any], bool]],
    error_message: str = "输入验证失败",
) -> None:
    """输入验证

    Args:
        value: 要验证的值
        validators: 验证函数列表
        error_message: 验证失败时的错误消息
    """
    for validator in validators:
        if not validator(value):
            raise ValueError(f"{error_message}: {value}")


def handle_cv_error(func: Callable) -> Callable:
    """OpenCV错误处理装饰器"""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            error_msg = str(e).lower()

            if "sift" in error_msg or "feature" in error_msg:
                raise FeatureExtractionError(f"特征提取失败: {e}")
            elif "match" in error_msg:
                raise MatchingError(f"特征匹配失败: {e}")
            elif "ransac" in error_msg or "homography" in error_msg:
                raise RANSACError(f"RANSAC估计失败: {e}")
            else:
                # 透明传播输入验证错误，便于上层用例捕获 ValueError
                if isinstance(e, ValueError):
                    raise
                raise VOBenchmarkException(f"OpenCV操作失败: {e}")

    return wrapper


def handle_io_error(func: Callable) -> Callable:
    """I/O错误处理装饰器"""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except (IOError, OSError, FileNotFoundError) as e:
            if "dataset" in str(e).lower():
                raise DatasetLoadError(f"数据集加载失败: {e}")
            else:
                raise StorageError(f"存储操作失败: {e}")
        except PermissionError as e:
            raise StorageError(f"权限不足: {e}")

    return wrapper


class ErrorContext:
    """错误上下文管理器"""

    def __init__(self, operation: str, log_level: int = logging.ERROR):
        self.operation = operation
        self.log_level = log_level
        self.start_time = None

    def __enter__(self):
        self.start_time = time.time()
        logger.debug(f"开始执行: {self.operation}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time

        if exc_type is None:
            logger.debug(f"成功完成: {self.operation} (耗时: {duration:.3f}s)")
        else:
            logger.log(
                self.log_level,
                f"执行失败: {self.operation} (耗时: {duration:.3f}s), 错误: {exc_val}",
            )

        return False  # 不抑制异常


def create_error_summary(errors: List[Exception]) -> dict:
    """创建错误摘要"""
    error_counts: Dict[str, int] = {}
    error_details = []

    for error in errors:
        error_type = type(error).__name__
        error_counts[error_type] = error_counts.get(error_type, 0) + 1
        error_details.append(
            {"type": error_type, "message": str(error), "timestamp": time.time()}
        )

    return {
        "total_errors": len(errors),
        "error_counts": error_counts,
        "error_details": error_details[-10:],  # 只保留最近10个错误的详细信息
    }


# 常用验证器
def is_not_none(value: Any) -> bool:
    """验证值不为None"""
    return value is not None


def is_positive(value: Union[int, float]) -> bool:
    """验证值为正数"""
    return isinstance(value, (int, float)) and value > 0


def is_valid_image_shape(shape: tuple) -> bool:
    """验证图像形状"""
    return len(shape) >= 2 and all(dim > 0 for dim in shape)


def is_valid_path(path: str) -> bool:
    """验证路径格式"""
    from pathlib import Path

    try:
        Path(path)
        return True
    except (TypeError, ValueError):
        return False
