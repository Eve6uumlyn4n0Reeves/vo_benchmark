#
# 功能: 定义API基础异常类。
#
from typing import Dict, Any, Optional, List
from src.models.types import ErrorCode


class VOBenchmarkException(Exception):
    """VO-Benchmark基础异常类"""

    error_code: ErrorCode = ErrorCode.INTERNAL_ERROR
    status_code: int = 500

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        suggestions: Optional[List[str]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.details = details or {}
        self.suggestions = suggestions or []

    def __str__(self) -> str:
        return self.message

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "error_code": self.error_code.value,
            "message": self.message,
            "details": self.details,
            "suggestions": self.suggestions,
        }


class ValidationError(VOBenchmarkException):
    """验证错误"""

    error_code = ErrorCode.VALIDATION_ERROR
    status_code = 400

    def __init__(self, message: str = "数据验证失败", **kwargs):
        super().__init__(message, **kwargs)


class DatasetNotFoundError(VOBenchmarkException):
    """数据集未找到错误"""

    error_code = ErrorCode.DATASET_NOT_FOUND
    status_code = 404

    def __init__(self, dataset_path: Optional[str] = None, **kwargs):
        message = f"数据集未找到: {dataset_path}" if dataset_path else "数据集未找到"
        suggestions = [
            "检查数据集路径是否正确",
            "确认数据集文件是否存在",
            "验证数据集格式是否支持",
        ]
        super().__init__(message, suggestions=suggestions, **kwargs)


class ExperimentNotFoundError(VOBenchmarkException):
    """实验未找到错误"""

    error_code = ErrorCode.EXPERIMENT_NOT_FOUND
    status_code = 404

    def __init__(self, experiment_id: Optional[str] = None, **kwargs):
        message = f"实验未找到: {experiment_id}" if experiment_id else "实验未找到"
        suggestions = [
            "检查实验ID是否正确",
            "确认实验是否已被删除",
            "使用GET /experiments查看可用实验",
        ]
        super().__init__(message, suggestions=suggestions, **kwargs)


class TaskNotFoundError(VOBenchmarkException):
    """任务未找到错误"""

    error_code = ErrorCode.TASK_NOT_FOUND
    status_code = 404

    def __init__(self, task_id: Optional[str] = None, **kwargs):
        message = f"任务未找到: {task_id}" if task_id else "任务未找到"
        suggestions = [
            "检查任务ID是否正确",
            "确认任务是否已完成或被取消",
            "使用GET /tasks查看可用任务",
        ]
        super().__init__(message, suggestions=suggestions, **kwargs)


class ResourceExhaustedError(VOBenchmarkException):
    """资源耗尽错误"""

    error_code = ErrorCode.RESOURCE_EXHAUSTED
    status_code = 429

    def __init__(self, resource_type: str = "系统资源", **kwargs):
        message = f"{resource_type}已耗尽"
        suggestions = [
            "等待一段时间后重试",
            "减少并发请求数量",
            "联系管理员增加资源配额",
        ]
        super().__init__(message, suggestions=suggestions, **kwargs)


class UnsupportedFeatureError(VOBenchmarkException):
    """不支持的特征类型错误"""

    error_code = ErrorCode.UNSUPPORTED_FEATURE
    status_code = 400

    def __init__(self, feature_type: Optional[str] = None, **kwargs):
        message = (
            f"不支持的特征类型: {feature_type}" if feature_type else "不支持的特征类型"
        )
        suggestions = [
            "使用支持的特征类型: SIFT, ORB",
            "检查特征类型拼写是否正确",
            "查看API文档获取支持的特征类型列表",
        ]
        super().__init__(message, suggestions=suggestions, **kwargs)


class UnsupportedRANSACError(VOBenchmarkException):
    """不支持的RANSAC类型错误"""

    error_code = ErrorCode.UNSUPPORTED_RANSAC
    status_code = 400

    def __init__(self, ransac_type: Optional[str] = None, **kwargs):
        message = (
            f"不支持的RANSAC类型: {ransac_type}"
            if ransac_type
            else "不支持的RANSAC类型"
        )
        suggestions = [
            "使用支持的RANSAC类型: STANDARD, PROSAC",
            "检查RANSAC类型拼写是否正确",
            "查看API文档获取支持的RANSAC类型列表",
        ]
        super().__init__(message, suggestions=suggestions, **kwargs)


class PermissionDeniedError(VOBenchmarkException):
    """权限拒绝错误"""

    error_code = ErrorCode.PERMISSION_DENIED
    status_code = 403

    def __init__(self, operation: Optional[str] = None, **kwargs):
        message = f"没有权限执行操作: {operation}" if operation else "权限不足"
        suggestions = [
            "检查用户权限设置",
            "联系管理员获取必要权限",
            "确认操作是否被允许",
        ]
        super().__init__(message, suggestions=suggestions, **kwargs)


class ConfigurationError(VOBenchmarkException):
    """配置错误"""

    error_code = ErrorCode.VALIDATION_ERROR
    status_code = 400

    def __init__(self, config_key: Optional[str] = None, **kwargs):
        message = f"配置错误: {config_key}" if config_key else "配置错误"
        suggestions = [
            "检查配置参数是否正确",
            "验证配置值是否在允许范围内",
            "查看配置文档获取正确格式",
        ]
        super().__init__(message, suggestions=suggestions, **kwargs)


class ProcessingError(VOBenchmarkException):
    """处理错误"""

    error_code = ErrorCode.INTERNAL_ERROR
    status_code = 500

    def __init__(self, stage: Optional[str] = None, **kwargs):
        message = f"处理失败: {stage}" if stage else "处理失败"
        suggestions = [
            "检查输入数据是否正确",
            "稍后重试操作",
            "如果问题持续存在，请联系技术支持",
        ]
        super().__init__(message, suggestions=suggestions, **kwargs)


class StorageError(VOBenchmarkException):
    """存储错误"""

    error_code = ErrorCode.INTERNAL_ERROR
    status_code = 500

    def __init__(self, operation: Optional[str] = None, **kwargs):
        message = f"存储操作失败: {operation}" if operation else "存储操作失败"
        suggestions = [
            "检查磁盘空间是否充足",
            "验证文件权限设置",
            "确认存储路径是否可访问",
        ]
        super().__init__(message, suggestions=suggestions, **kwargs)


class NetworkError(VOBenchmarkException):
    """网络错误"""

    error_code = ErrorCode.INTERNAL_ERROR
    status_code = 503

    def __init__(self, service: Optional[str] = None, **kwargs):
        message = f"网络连接失败: {service}" if service else "网络连接失败"
        suggestions = ["检查网络连接是否正常", "稍后重试操作", "确认服务是否可用"]
        super().__init__(message, suggestions=suggestions, **kwargs)
