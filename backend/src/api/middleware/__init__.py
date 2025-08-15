"""
API Middleware Package

This package contains middleware components for the Flask application,
including error handling, request validation, and security features.

Author:
    VO-Benchmark Team

Version:
    1.0.0
"""

from .error_handler import error_handler, setup_error_handling, input_validator


def setup_middleware(app):
    """Setup middleware for Flask application"""
    # This function can be used to setup additional middleware
    # Currently, error handling is set up separately
    pass


__all__ = [
    "error_handler",
    "setup_error_handling",
    "input_validator",
    "setup_middleware",
]
