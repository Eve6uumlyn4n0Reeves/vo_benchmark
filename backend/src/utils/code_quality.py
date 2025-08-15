#
# 功能: 代码质量改进工具
#
import logging
import functools
import inspect
from typing import Any, Callable, Dict, List, Optional, Union, Tuple, Type
from enum import Enum

# 统一的类型别名
Point2D = Tuple[float, float]
Point3D = Tuple[float, float, float]
Matrix3x3 = List[List[float]]
Matrix4x4 = List[List[float]]
ImageArray = Any  # numpy.ndarray
DescriptorArray = Any  # numpy.ndarray


class LogLevel(Enum):
    """日志级别枚举"""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class StandardLogger:
    """标准化日志记录器"""

    def __init__(self, name: str):
        self.logger = logging.getLogger(name)

    def debug(self, message: str, **kwargs) -> None:
        """调试信息"""
        self.logger.debug(self._format_message(message, **kwargs))

    def info(self, message: str, **kwargs) -> None:
        """一般信息"""
        self.logger.info(self._format_message(message, **kwargs))

    def warning(self, message: str, **kwargs) -> None:
        """警告信息"""
        self.logger.warning(self._format_message(message, **kwargs))

    def error(self, message: str, error: Optional[Exception] = None, **kwargs) -> None:
        """错误信息"""
        if error:
            message = f"{message}: {error}"
        self.logger.error(self._format_message(message, **kwargs))

    def critical(
        self, message: str, error: Optional[Exception] = None, **kwargs
    ) -> None:
        """严重错误"""
        if error:
            message = f"{message}: {error}"
        self.logger.critical(self._format_message(message, **kwargs))

    def _format_message(self, message: str, **kwargs) -> str:
        """格式化日志消息"""
        if kwargs:
            context = ", ".join(f"{k}={v}" for k, v in kwargs.items())
            return f"{message} [{context}]"
        return message


def get_standard_logger(name: str) -> StandardLogger:
    """获取标准化日志记录器"""
    return StandardLogger(name)


def validate_types(*type_checks: Tuple[str, Any, Type]) -> Callable:
    """类型验证装饰器

    Args:
        type_checks: (参数名, 值, 期望类型) 的元组列表
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 获取函数签名
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()

            # 验证类型
            for param_name, expected_type in type_checks:
                if param_name in bound_args.arguments:
                    value = bound_args.arguments[param_name]
                    if value is not None and not isinstance(value, expected_type):
                        raise TypeError(
                            f"参数 {param_name} 期望类型 {expected_type.__name__}, "
                            f"实际类型 {type(value).__name__}"
                        )

            return func(*args, **kwargs)

        return wrapper

    return decorator


def deprecated(reason: str = "", version: str = "") -> Callable:
    """废弃功能装饰器"""

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            warning_msg = f"函数 {func.__name__} 已废弃"
            if version:
                warning_msg += f" (自版本 {version})"
            if reason:
                warning_msg += f": {reason}"

            logging.warning(warning_msg)
            return func(*args, **kwargs)

        return wrapper

    return decorator


def ensure_not_none(*param_names: str) -> Callable:
    """确保参数不为None的装饰器"""

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 获取函数签名
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()

            # 检查指定参数
            for param_name in param_names:
                if param_name in bound_args.arguments:
                    value = bound_args.arguments[param_name]
                    if value is None:
                        raise ValueError(f"参数 {param_name} 不能为None")

            return func(*args, **kwargs)

        return wrapper

    return decorator


class CodeMetrics:
    """代码质量指标"""

    def __init__(self):
        self.function_calls = {}
        self.error_counts = {}
        self.performance_data = {}

    def record_function_call(self, func_name: str) -> None:
        """记录函数调用"""
        self.function_calls[func_name] = self.function_calls.get(func_name, 0) + 1

    def record_error(self, error_type: str) -> None:
        """记录错误"""
        self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1

    def record_performance(self, func_name: str, duration: float) -> None:
        """记录性能数据"""
        if func_name not in self.performance_data:
            self.performance_data[func_name] = []
        self.performance_data[func_name].append(duration)

    def get_summary(self) -> Dict[str, Any]:
        """获取指标摘要"""
        return {
            "total_function_calls": sum(self.function_calls.values()),
            "unique_functions": len(self.function_calls),
            "total_errors": sum(self.error_counts.values()),
            "error_types": len(self.error_counts),
            "monitored_functions": len(self.performance_data),
        }


# 全局代码指标实例
code_metrics = CodeMetrics()


def track_calls(func: Callable) -> Callable:
    """跟踪函数调用的装饰器"""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        code_metrics.record_function_call(func.__name__)
        return func(*args, **kwargs)

    return wrapper


def standardize_docstring(
    description: str,
    args: Optional[Dict[str, str]] = None,
    returns: Optional[str] = None,
    raises: Optional[Dict[str, str]] = None,
    examples: Optional[List[str]] = None,
) -> Callable:
    """标准化文档字符串装饰器"""

    def decorator(func: Callable) -> Callable:
        # 构建标准文档字符串
        docstring_parts = [description]

        if args:
            docstring_parts.append("\nArgs:")
            for arg_name, arg_desc in args.items():
                docstring_parts.append(f"    {arg_name}: {arg_desc}")

        if returns:
            docstring_parts.append(f"\nReturns:\n    {returns}")

        if raises:
            docstring_parts.append("\nRaises:")
            for exc_name, exc_desc in raises.items():
                docstring_parts.append(f"    {exc_name}: {exc_desc}")

        if examples:
            docstring_parts.append("\nExamples:")
            for example in examples:
                docstring_parts.append(f"    {example}")

        func.__doc__ = "\n".join(docstring_parts)
        return func

    return decorator


class ParameterValidator:
    """参数验证器"""

    @staticmethod
    def validate_image_array(image: Any) -> bool:
        """验证图像数组"""
        try:
            import numpy as np

            return (
                isinstance(image, np.ndarray)
                and len(image.shape) in [2, 3]
                and image.size > 0
            )
        except ImportError:
            return hasattr(image, "shape") and hasattr(image, "size")

    @staticmethod
    def validate_positive_number(value: Union[int, float]) -> bool:
        """验证正数"""
        return isinstance(value, (int, float)) and value > 0

    @staticmethod
    def validate_non_empty_string(value: str) -> bool:
        """验证非空字符串"""
        return isinstance(value, str) and len(value.strip()) > 0

    @staticmethod
    def validate_list_not_empty(value: List[Any]) -> bool:
        """验证非空列表"""
        return isinstance(value, list) and len(value) > 0


def validate_parameters(**validators: Callable[[Any], bool]) -> Callable:
    """参数验证装饰器"""

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 获取函数签名
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()

            # 验证参数
            for param_name, validator in validators.items():
                if param_name in bound_args.arguments:
                    value = bound_args.arguments[param_name]
                    if not validator(value):
                        raise ValueError(f"参数 {param_name} 验证失败: {value}")

            return func(*args, **kwargs)

        return wrapper

    return decorator


def format_error_message(
    operation: str, error: Exception, context: Optional[Dict[str, Any]] = None
) -> str:
    """格式化错误消息"""
    message = f"{operation} 失败: {type(error).__name__}: {error}"

    if context:
        context_str = ", ".join(f"{k}={v}" for k, v in context.items())
        message += f" [上下文: {context_str}]"

    return message


def create_type_hint_checker() -> Callable:
    """创建类型提示检查器"""

    def check_type_hints(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 实现运行时类型检查逻辑
            try:
                import inspect
                from typing import get_type_hints

                # 获取函数的类型提示
                type_hints = get_type_hints(func)

                # 获取函数签名
                sig = inspect.signature(func)
                bound_args = sig.bind(*args, **kwargs)
                bound_args.apply_defaults()

                # 检查参数类型
                for param_name, param_value in bound_args.arguments.items():
                    if param_name in type_hints:
                        expected_type = type_hints[param_name]

                        # 简单类型检查（不处理复杂的泛型）
                        if hasattr(expected_type, "__origin__"):
                            # 处理泛型类型（如List[str], Dict[str, int]等）
                            origin = expected_type.__origin__
                            if not isinstance(param_value, origin):
                                logger.warning(
                                    f"类型检查警告: 函数 {func.__name__} 的参数 {param_name} "
                                    f"期望类型 {expected_type}, 实际类型 {type(param_value)}"
                                )
                        else:
                            # 处理简单类型
                            if not isinstance(param_value, expected_type):
                                logger.warning(
                                    f"类型检查警告: 函数 {func.__name__} 的参数 {param_name} "
                                    f"期望类型 {expected_type}, 实际类型 {type(param_value)}"
                                )

                # 执行原函数
                result = func(*args, **kwargs)

                # 检查返回值类型
                if "return" in type_hints:
                    expected_return_type = type_hints["return"]
                    if hasattr(expected_return_type, "__origin__"):
                        origin = expected_return_type.__origin__
                        if not isinstance(result, origin):
                            logger.warning(
                                f"类型检查警告: 函数 {func.__name__} 的返回值 "
                                f"期望类型 {expected_return_type}, 实际类型 {type(result)}"
                            )
                    else:
                        if not isinstance(result, expected_return_type):
                            logger.warning(
                                f"类型检查警告: 函数 {func.__name__} 的返回值 "
                                f"期望类型 {expected_return_type}, 实际类型 {type(result)}"
                            )

                return result

            except Exception as e:
                # 如果类型检查失败，记录警告但不影响函数执行
                logger.debug(f"类型检查失败 {func.__name__}: {e}")
                return func(*args, **kwargs)

        return wrapper

    return check_type_hints


# 常用的验证器实例
image_validator = ParameterValidator.validate_image_array
positive_number_validator = ParameterValidator.validate_positive_number
non_empty_string_validator = ParameterValidator.validate_non_empty_string
non_empty_list_validator = ParameterValidator.validate_list_not_empty
