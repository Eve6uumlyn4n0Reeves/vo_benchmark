#
# 功能: 定义API异常处理器。
#
import traceback
import logging
from datetime import datetime
from flask import Flask, jsonify, request, g
from werkzeug.exceptions import HTTPException
from pydantic import ValidationError
from src.api.exceptions.base import VOBenchmarkException
from src.api.schemas.response import ErrorResponse
from src.models.types import ErrorCode

logger = logging.getLogger(__name__)


def register_error_handlers(app: Flask):
    """注册所有错误处理器"""

    @app.errorhandler(VOBenchmarkException)
    def handle_vo_exception(error: VOBenchmarkException):
        """处理自定义VO异常"""
        request_id = getattr(g, "request_id", None)

        logger.error(f"VO异常 [{request_id}]: {error.error_code.value} - {str(error)}")

        response_data = ErrorResponse(
            error_code=error.error_code,
            message=str(error),
            details=error.details,
            timestamp=datetime.utcnow(),
            request_id=request_id,
            suggestions=error.suggestions or None,
        )

        return jsonify(response_data.dict()), error.status_code

    @app.errorhandler(ValidationError)
    def handle_validation_error(error: ValidationError):
        """处理Pydantic验证错误"""
        request_id = getattr(g, "request_id", None)

        logger.warning(f"验证错误 [{request_id}]: {str(error)}")

        # 格式化验证错误信息
        validation_errors = []
        for err in error.errors():
            field = ".".join(str(x) for x in err["loc"])
            validation_errors.append(
                {"field": field, "message": err["msg"], "type": err["type"]}
            )

        response_data = ErrorResponse(
            error_code=ErrorCode.VALIDATION_ERROR,
            message="请求数据验证失败",
            details={"validation_errors": validation_errors},
            timestamp=datetime.utcnow(),
            request_id=request_id,
            suggestions=[
                "请检查请求数据格式是否正确",
                "确保所有必需字段都已提供",
                "验证字段值是否在允许的范围内",
            ],
        )

        return jsonify(response_data.dict()), 400

    @app.errorhandler(404)
    def handle_not_found(error):
        """处理404错误"""
        request_id = getattr(g, "request_id", None)

        logger.warning(f"资源未找到 [{request_id}]: {request.url}")

        response_data = ErrorResponse(
            error_code=ErrorCode.TASK_NOT_FOUND,  # 或其他适当的错误代码
            message="请求的资源不存在",
            details={"url": request.url, "method": request.method},
            timestamp=datetime.utcnow(),
            request_id=request_id,
            suggestions=[
                "请检查URL是否正确",
                "确认资源ID是否有效",
                "查看API文档获取正确的端点信息",
            ],
        )

        return jsonify(response_data.dict()), 404

    @app.errorhandler(405)
    def handle_method_not_allowed(error):
        """处理方法不允许错误"""
        request_id = getattr(g, "request_id", None)

        logger.warning(f"方法不允许 [{request_id}]: {request.method} {request.url}")

        response_data = ErrorResponse(
            error_code=ErrorCode.VALIDATION_ERROR,
            message=f"HTTP方法 {request.method} 不被允许",
            details={
                "method": request.method,
                "url": request.url,
            },
            timestamp=datetime.utcnow(),
            request_id=request_id,
            suggestions=["请使用允许的HTTP方法", "查看API文档确认正确的请求方法"],
        )

        return jsonify(response_data.dict()), 405

    @app.errorhandler(413)
    def handle_request_too_large(error):
        """处理请求过大错误"""
        request_id = getattr(g, "request_id", None)

        logger.warning(f"请求过大 [{request_id}]: {request.content_length} bytes")

        max_size = app.config.get("MAX_CONTENT_LENGTH", 16 * 1024 * 1024)

        response_data = ErrorResponse(
            error_code=ErrorCode.VALIDATION_ERROR,
            message="请求数据过大",
            details={
                "current_size": request.content_length,
                "max_allowed_size": max_size,
            },
            timestamp=datetime.utcnow(),
            request_id=request_id,
            suggestions=[
                f"请确保请求大小不超过 {max_size} 字节",
                "考虑分批上传大文件",
                "压缩数据以减少传输大小",
            ],
        )

        return jsonify(response_data.dict()), 413

    @app.errorhandler(429)
    def handle_rate_limit_exceeded(error):
        """处理速率限制错误"""
        request_id = getattr(g, "request_id", None)

        logger.warning(f"速率限制 [{request_id}]: {request.remote_addr}")

        response_data = ErrorResponse(
            error_code=ErrorCode.RESOURCE_EXHAUSTED,
            message="请求频率过高，请稍后再试",
            details={"client_ip": request.remote_addr},
            timestamp=datetime.utcnow(),
            request_id=request_id,
            suggestions=[
                "请降低请求频率",
                "等待一段时间后重试",
                "考虑实现客户端请求缓存",
            ],
        )

        return jsonify(response_data.dict()), 429

    @app.errorhandler(HTTPException)
    def handle_http_exception(error: HTTPException):
        """处理其他HTTP异常"""
        request_id = getattr(g, "request_id", None)

        logger.warning(f"HTTP异常 [{request_id}]: {error.code} - {error.description}")

        response_data = ErrorResponse(
            error_code=ErrorCode.INTERNAL_ERROR,
            message=error.description or "HTTP错误",
            details={"http_code": error.code},
            timestamp=datetime.utcnow(),
            request_id=request_id,
            suggestions=["检查请求是否符合接口要求"],
        )

        return jsonify(response_data.dict()), int(error.code or 500)

    @app.errorhandler(Exception)
    def handle_generic_exception(error: Exception):
        """处理未捕获的异常"""
        request_id = getattr(g, "request_id", None)

        # 记录完整的错误堆栈
        logger.error(
            f"未处理异常 [{request_id}]: {str(error)}\n{traceback.format_exc()}"
        )

        # 在开发环境中提供更详细的错误信息
        details = {"error_type": type(error).__name__}
        if app.debug:
            details.update(
                {
                    "error_message": str(error),
                    "traceback": "\n".join(traceback.format_exc().split("\n")),
                }
            )

        response_data = ErrorResponse(
            error_code=ErrorCode.INTERNAL_ERROR,
            message="服务器内部错误" if not app.debug else str(error),
            details=details,
            timestamp=datetime.utcnow(),
            request_id=request_id,
            suggestions=[
                "请稍后重试",
                "如果问题持续存在，请联系技术支持",
                "检查请求参数是否正确",
            ],
        )

        return jsonify(response_data.dict()), 500

    # Note: KeyboardInterrupt cannot be registered as Flask error handler
    # It should be handled at the application level, not in Flask routes
