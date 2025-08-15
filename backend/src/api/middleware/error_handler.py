"""
Comprehensive Error Handling Middleware

This module provides centralized error handling for the Flask application,
including validation errors, business logic errors, and system errors.

Author:
    VO-Benchmark Team

Version:
    1.0.0
"""

import logging
import traceback
from typing import Dict, Any, Optional, Tuple
from flask import Flask, request, jsonify, Response
from werkzeug.exceptions import HTTPException
from typing import Tuple as _TupleType  # type: ignore[unused-ignore]
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError

from src.api.exceptions.base import VOBenchmarkException, ErrorCode

logger = logging.getLogger(__name__)


class ErrorHandler:
    """Centralized error handler for the Flask application"""

    def __init__(self, app: Optional[Flask] = None):
        self.app = app
        if app is not None:
            self.init_app(app)

    def init_app(self, app: Flask) -> None:
        """Initialize error handling for Flask app"""
        self.app = app

        # Register error handlers
        app.errorhandler(ValidationError)(self.handle_validation_error)
        app.errorhandler(VOBenchmarkException)(self.handle_business_error)
        app.errorhandler(SQLAlchemyError)(self.handle_database_error)
        app.errorhandler(HTTPException)(self.handle_http_error)
        app.errorhandler(Exception)(self.handle_generic_error)

        # Register request hooks for error context
        app.before_request(self.before_request)
        app.after_request(self.after_request)

    def before_request(self):
        """Set up error context before request"""
        # Store request start time for performance monitoring
        import time

        request.start_time = time.time()

        # Log request details in debug mode
        if self.app.debug:
            logger.debug(f"Request: {request.method} {request.url}")

    def after_request(self, response):
        """Clean up after request"""
        # Log response time
        if hasattr(request, "start_time"):
            import time
            from datetime import datetime

            # 确保 start_time 是时间戳格式
            if isinstance(request.start_time, datetime):
                start_timestamp = request.start_time.timestamp()
            else:
                start_timestamp = request.start_time

            duration = time.time() - start_timestamp

            # Log slow requests
            if duration > 1.0:  # Log requests taking more than 1 second
                logger.warning(
                    f"Slow request: {request.method} {request.url} "
                    f"took {duration:.3f}s"
                )

        return response

    def handle_validation_error(
        self, error: ValidationError
    ) -> Tuple[Response, int]:
        """Handle Pydantic validation errors"""
        logger.warning(f"Validation error: {error}")

        # Format validation errors for API response
        formatted_errors = []
        for err in error.errors():
            formatted_errors.append(
                {
                    "field": ".".join(str(loc) for loc in err["loc"]),
                    "message": err["msg"],
                    "type": err["type"],
                    "input": err.get("input"),
                }
            )

        return (
            jsonify(
                {
                    "error": "Validation failed",
                    "error_code": ErrorCode.VALIDATION_ERROR.value,
                    "details": formatted_errors,
                    "timestamp": self._get_timestamp(),
                    "request_id": self._get_request_id(),
                }
            ),
            400,
        )

    def handle_business_error(
        self, error: VOBenchmarkException
    ) -> Tuple[Response, int]:
        """Handle business logic errors"""
        logger.error(f"Business error: {error}")

        status_code = self._get_status_code_for_error(error.error_code)

        return (
            jsonify(
                {
                    "error": error.message,
                    "error_code": error.error_code.value,
                    "details": error.details,
                    "timestamp": self._get_timestamp(),
                    "request_id": self._get_request_id(),
                }
            ),
            status_code,
        )

    def handle_database_error(
        self, error: SQLAlchemyError
    ) -> Tuple[Response, int]:
        """Handle database errors"""
        logger.error(f"Database error: {error}")

        # Don't expose internal database errors to clients
        return (
            jsonify(
                {
                    "error": "Database operation failed",
                    "error_code": ErrorCode.INTERNAL_ERROR.value,
                    "timestamp": self._get_timestamp(),
                    "request_id": self._get_request_id(),
                }
            ),
            500,
        )

    def handle_http_error(self, error: HTTPException) -> Tuple[Response, int]:
        """Handle HTTP errors (404, 405, etc.)"""
        logger.warning(f"HTTP error: {error}")

        code = error.code or 500
        return (
            jsonify(
                {
                    "error": error.description,
                    "message": error.description,
                    "error_code": f"HTTP_{code}",
                    "timestamp": self._get_timestamp(),
                    "request_id": self._get_request_id(),
                }
            ),
            int(code),
        )

    def handle_generic_error(self, error: Exception) -> Tuple[Response, int]:
        """Handle unexpected errors"""
        logger.error(f"Unexpected error: {error}")
        logger.error(f"Traceback: {traceback.format_exc()}")

        # In production, don't expose internal error details
        if self.app and getattr(self.app, "config", None) and self.app.config.get("FLASK_ENV") == "production":
            error_message = "Internal server error"
            details = None
        else:
            error_message = str(error)
            details = {
                "type": type(error).__name__,
                "traceback": traceback.format_exc().split("\n"),
            }

        return (
            jsonify(
                {
                    "error": error_message,
                    "error_code": ErrorCode.INTERNAL_ERROR.value,
                    "details": details,
                    "timestamp": self._get_timestamp(),
                    "request_id": self._get_request_id(),
                }
            ),
            500,
        )

    def _get_status_code_for_error(self, error_code: ErrorCode) -> int:
        """Map error codes to HTTP status codes"""
        mapping = {
            ErrorCode.VALIDATION_ERROR: 400,
            ErrorCode.DATASET_NOT_FOUND: 404,
            ErrorCode.EXPERIMENT_NOT_FOUND: 404,
            ErrorCode.TASK_NOT_FOUND: 404,
            ErrorCode.UNSUPPORTED_FEATURE: 400,
            ErrorCode.UNSUPPORTED_RANSAC: 400,
            ErrorCode.PERMISSION_DENIED: 403,
            ErrorCode.RESOURCE_EXHAUSTED: 429,
            ErrorCode.INTERNAL_ERROR: 500,
        }
        return mapping.get(error_code, 500)

    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format"""
        from datetime import datetime, timezone

        return datetime.now(timezone.utc).isoformat()

    def _get_request_id(self) -> str:
        """Get or generate request ID for tracing"""
        # Try to get request ID from headers first
        request_id = request.headers.get("X-Request-ID")
        if not request_id:
            # Generate a simple request ID
            import uuid

            request_id = str(uuid.uuid4())[:8]
        return request_id


# Global error handler instance
error_handler = ErrorHandler()


def setup_error_handling(app: Flask) -> None:
    """Setup error handling for Flask application"""
    error_handler.init_app(app)
    logger.info("Error handling middleware initialized")


class InputValidator:
    """Input validation utilities"""

    @staticmethod
    def validate_pagination(
        page: int, limit: int, max_limit: int = 100
    ) -> Tuple[bool, Optional[str]]:
        """Validate pagination parameters"""
        if page < 1:
            return False, "Page number must be greater than 0"

        if limit < 1:
            return False, "Limit must be greater than 0"

        if limit > max_limit:
            return False, f"Limit cannot exceed {max_limit}"

        return True, None

    @staticmethod
    def validate_experiment_id(experiment_id: str) -> Tuple[bool, Optional[str]]:
        """Validate experiment ID format"""
        if not experiment_id:
            return False, "Experiment ID cannot be empty"

        if len(experiment_id) < 3:
            return False, "Experiment ID must be at least 3 characters long"

        if len(experiment_id) > 100:
            return False, "Experiment ID cannot exceed 100 characters"

        # Check for valid characters (alphanumeric, hyphens, underscores)
        import re

        if not re.match(r"^[a-zA-Z0-9_-]+$", experiment_id):
            return (
                False,
                "Experiment ID can only contain letters, numbers, hyphens, and underscores",
            )

        return True, None

    @staticmethod
    def validate_file_path(file_path: str) -> Tuple[bool, Optional[str]]:
        """Validate file path for security"""
        if not file_path:
            return False, "File path cannot be empty"

        # Check for path traversal attempts
        if ".." in file_path or file_path.startswith("/"):
            return False, "Invalid file path: path traversal not allowed"

        # Check for valid file extensions (if needed)
        import os

        allowed_extensions = {".txt", ".json", ".csv", ".xlsx", ".png", ".jpg", ".jpeg"}
        ext = os.path.splitext(file_path)[1].lower()
        if ext and ext not in allowed_extensions:
            return False, f"File extension {ext} not allowed"

        return True, None


# Export validation utilities
input_validator = InputValidator()
