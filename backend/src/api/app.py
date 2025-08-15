"""
Flask Application Factory

This module provides the main Flask application factory with comprehensive
configuration, middleware setup, and API documentation integration.

Features:
- Environment-based configuration
- OpenAPI/Swagger documentation
- CORS configuration
- Error handling and logging
- Request/response middleware

Author:
    VO-Benchmark Team

Version:
    1.0.0
"""

import os
import logging
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_compress import Compress
from datetime import datetime, UTC
import traceback

from typing import Optional
from src.config.manager import get_config
from src.api.routes import tasks_bp, results_bp, events_bp, datasets_bp, health_bp, experiments_bp
from src.api.routes.manifest import manifest_bp

# Import documented API components
from src.api.docs import doc_bp, api
from src.api.routes.experiments_documented import experiments_ns
from src.api.routes.health_documented import health_ns

# Import optional modules (decoupled; import failures won't disable others)
errors = None
config = None
_HAS_ERRORS = False
_HAS_CONFIG_NS = False

logger_opt = logging.getLogger(__name__)

try:
    from src.api.routes import errors as _errors

    errors = _errors
    _HAS_ERRORS = True
except ImportError as e:
    logger_opt.warning(f"Optional route 'errors' not available: {e}")

try:
    from src.api.routes import config as _config
    from src.api.routes.config import config_ns  # noqa: F401

    config = _config
    _HAS_CONFIG_NS = True
except ImportError as e:
    logger_opt.warning(f"Optional route 'config' not available: {e}")

# Removed optional namespaces: datasets, monitoring, comparison, match_viz, batch

# Fallback import for config endpoints (ensure diagnostics available even if other optional modules fail)
try:
    from src.api.routes.config import (
        config_ns as standalone_config_ns,
        bp as standalone_config_bp,
    )

    _CONFIG_STANDALONE_AVAILABLE = True
except ImportError as e:
    logging.getLogger(__name__).warning(
        f"Standalone config endpoints not available: {e}. Diagnostics may be disabled if optional modules fail."
    )
    _CONFIG_STANDALONE_AVAILABLE = False

try:
    # 仅启用统一的中间件错误处理
    from src.api.middleware import setup_middleware
    from src.api.middleware.error_handler import setup_error_handling

    _MIDDLEWARE_AVAILABLE = True
except ImportError as e:
    logging.getLogger(__name__).warning(
        f"Middleware modules not available: {e}. Error handling or middleware may be partially disabled."
    )
    _MIDDLEWARE_AVAILABLE = False


def create_app(config_name: Optional[str] = None) -> Flask:
    """
    Create and configure Flask application instance

    This factory function creates a Flask application with comprehensive
    configuration including API documentation, middleware, error handling,
    and environment-specific settings.

    Args:
        config_name: Configuration environment name ('development', 'production', 'testing')
                    If None, uses FLASK_ENV environment variable or defaults to 'development'

    Returns:
        Flask: Fully configured Flask application instance with:
            - OpenAPI/Swagger documentation
            - CORS configuration
            - Request/response middleware
            - Error handling
            - API route registration

    Example:
        >>> app = create_app('development')
        >>> app.run(host='0.0.0.0', port=5000, debug=True)
    """
    app = Flask(__name__)

    # Load configuration based on environment
    if config_name is None:
        config_name = os.getenv("FLASK_ENV", "development")

    # Get unified configuration from config.manager
    unified_config = get_config()

    # Convert to Flask configuration format
    app.config.update(
        {
            "SECRET_KEY": unified_config.secret_key,
            "DEBUG": unified_config.debug,
            "TESTING": config_name == "testing",
            "DATABASE_URL": unified_config.database.url,
            "REDIS_URL": unified_config.redis.url,
            "CORS_ORIGINS": unified_config.cors.origins,
            "LOG_LEVEL": unified_config.logging.level,
            "LOG_TO_STDOUT": unified_config.logging.to_stdout,
            "DATASETS_ROOT": unified_config.storage.datasets_root,
            "RESULTS_ROOT": unified_config.storage.results_root,
            "TEMP_ROOT": unified_config.storage.temp_root,
            "DEFAULT_NUM_RUNS": unified_config.experiment.default_num_runs,
            "DEFAULT_PARALLEL_JOBS": unified_config.experiment.default_parallel_jobs,
            "DEFAULT_MAX_FEATURES": unified_config.experiment.default_max_features,
            "DEFAULT_RANSAC_THRESHOLD": unified_config.experiment.default_ransac_threshold,
            "DEFAULT_RANSAC_CONFIDENCE": unified_config.experiment.default_ransac_confidence,
            "DEFAULT_RANSAC_MAX_ITERS": unified_config.experiment.default_ransac_max_iters,
            "SUPPORTED_FEATURE_TYPES": unified_config.experiment.supported_feature_types,
            "SUPPORTED_RANSAC_TYPES": unified_config.experiment.supported_ransac_types,
        }
    )

    # Store API version in config for health checks
    app.config["API_VERSION"] = "1.0.0"

    # Configure logging
    setup_logging(app)

    # Configure CORS
    setup_cors(app)

    # Configure compression
    setup_compression(app)

    # Setup middleware (only if available)
    if _MIDDLEWARE_AVAILABLE:
        setup_middleware(app)
        setup_error_handling(app)

    # Register unified API with documentation
    register_api(app)

    # 添加请求钩子
    setup_request_hooks(app)

    # 添加 WebSocket 端点处理（暂时返回 404，提示使用轮询）
    @app.route("/ws")
    def websocket_not_implemented():
        return (
            jsonify(
                {
                    "error": "WebSocket not implemented",
                    "message": "Please use polling endpoints for real-time updates",
                    "polling_endpoints": {
                        "experiments": "/api/v1/experiments-doc",
                        "tasks": "/api/v1/tasks"
                    },
                }
            ),
            404,
        )

    app.logger.info(f"Flask应用已创建，环境: {config_name}")
    return app


def setup_logging(app: Flask) -> None:
    """配置应用日志"""
    if not app.debug and not app.testing:
        # 生产环境日志配置
        if app.config.get("LOG_TO_STDOUT"):
            stream_handler = logging.StreamHandler()
            stream_handler.setLevel(logging.INFO)
            app.logger.addHandler(stream_handler)
        else:
            # 文件日志
            if not os.path.exists("logs"):
                os.mkdir("logs")
            file_handler = logging.FileHandler("logs/vo-benchmark.log")
            file_handler.setFormatter(
                logging.Formatter(
                    "%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]"
                )
            )
            file_handler.setLevel(logging.INFO)
            app.logger.addHandler(file_handler)

        app.logger.setLevel(logging.INFO)
        app.logger.info("VO-Benchmark API启动")


def get_cors_origins(app: Flask) -> list:
    """动态获取CORS允许的源"""
    # 直接从配置获取
    origins = app.config.get("CORS_ORIGINS", [])

    # 如果配置中包含 '*'，直接返回
    if "*" in origins:
        return ["*"]

    # 开发环境添加默认前端地址
    if app.config.get("DEBUG"):
        # 兼容 Vite 的环境变量命名（VITE_FRONTEND_PORT）
        frontend_port = (
            os.environ.get("FRONTEND_PORT")
            or os.environ.get("VITE_FRONTEND_PORT")
            or "3000"
        )
        dev_origins = [
            f"http://localhost:{frontend_port}",
            f"http://127.0.0.1:{frontend_port}",
        ]
        # 避免重复添加
        for origin in dev_origins:
            if origin not in origins:
                origins.append(origin)

    return origins


def setup_cors(app: Flask) -> None:
    """配置跨域资源共享"""
    allowed_origins = get_cors_origins(app)

    cors_config = {
        "origins": allowed_origins or ["*"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization", "X-Requested-With"],
        "supports_credentials": True,
        "always_send": True,
    }

    # Apply CORS to all API routes including legacy and documented
    CORS(app, resources={r"/api/*": cors_config})

    # Ensure OPTIONS preflight returns proper headers
    @app.after_request
    def add_cors_headers(response):
        # 如果已由 Flask-CORS 设置，则保持；否则补齐基础CORS头（兼容测试用例）
        if "Access-Control-Allow-Origin" not in response.headers:
            response.headers["Access-Control-Allow-Origin"] = (
                ",".join(allowed_origins) if allowed_origins else "*"
            )
            response.headers["Access-Control-Allow-Methods"] = (
                "GET, POST, PUT, DELETE, OPTIONS"
            )
            response.headers["Access-Control-Allow-Headers"] = (
                "Content-Type, Authorization, X-Requested-With"
            )
        return response

    app.logger.info(f"CORS configured for origins: {allowed_origins}")


def setup_compression(app: Flask) -> None:
    """配置HTTP压缩"""
    try:
        compress = Compress()
        compress.init_app(app)

        # 配置压缩选项
        app.config['COMPRESS_MIMETYPES'] = [
            'text/html',
            'text/css',
            'text/xml',
            'text/javascript',
            'application/json',
            'application/javascript',
            'application/xml+rss',
            'application/atom+xml',
            'application/octet-stream',  # Arrow文件
            'application/vnd.apache.arrow.stream',  # Arrow IPC
            'application/gzip',  # 已压缩的文件
        ]
        app.config['COMPRESS_LEVEL'] = 6  # 平衡压缩率和速度
        app.config['COMPRESS_MIN_SIZE'] = 1024  # 只压缩大于1KB的响应
        app.config['COMPRESS_ALGORITHM'] = 'gzip'  # 使用gzip算法

        app.logger.info("HTTP压缩已启用")
    except Exception as e:
        app.logger.warning(f"HTTP压缩配置失败: {e}")


def register_api(app: Flask) -> None:
    """
    Register unified API endpoints with OpenAPI documentation

    This function registers the Flask-RESTX API with comprehensive
    OpenAPI/Swagger documentation. All endpoints are unified under
    the documented API to avoid conflicts and provide consistent
    API experience.

    Features:
    - Interactive API explorer at /docs/
    - Complete request/response schemas
    - Error response documentation
    - Example usage patterns
    - Unified endpoint structure

    Args:
        app: Flask application instance
    """
    # Register the documentation blueprint
    app.register_blueprint(doc_bp, url_prefix="/api/v1")

    # Add essential namespaces to the unified API
    api.add_namespace(experiments_ns)
    api.add_namespace(health_ns)

    # Config endpoints: prefer unified RESTX namespace only to avoid duplicate blueprints
    if _CONFIG_STANDALONE_AVAILABLE:
        try:
            api.add_namespace(standalone_config_ns)
        except Exception as _e:
            app.logger.warning(f"Failed to register config namespace: {_e}")

    # Optional namespaces removed (datasets, monitoring, comparison, match_viz, batch)
    try:
        if _HAS_CONFIG_NS:
            api.add_namespace(config_ns)
    except Exception as _e:
        app.logger.warning(f"Failed to register config namespace: {_e}")

    # Register primary blueprints (include legacy endpoints for tests compatibility)
    app.register_blueprint(tasks_bp, name="main_tasks")
    app.register_blueprint(results_bp, name="main_results")
    app.register_blueprint(events_bp, name="main_events")
    app.register_blueprint(datasets_bp, name="main_datasets")
    app.register_blueprint(manifest_bp, name="manifest")
    if health_bp is not None:
        app.register_blueprint(health_bp, name="legacy_health")
    if experiments_bp is not None:
        app.register_blueprint(experiments_bp, name="legacy_experiments")

    # Optionally register additional blueprints
    # Optionally register additional blueprints if available
    try:
        if _HAS_ERRORS and errors is not None and hasattr(errors, "bp"):
            app.register_blueprint(errors.bp, url_prefix="/api/v1")
    except Exception as _e:
        app.logger.warning(f"Failed to register errors blueprint: {_e}")
    # Do not register config.bp separately to avoid duplicate blueprint names
    # The documented namespace under /api/v1/docs/ already exposes config endpoints

    # Log API information
    try:
        app.logger.info("Unified API registered with documentation at /api/v1/docs/")
        app.logger.info(
            "Primary API endpoints available through documented namespaces:"
        )
        app.logger.info("  - /api/v1/experiments-doc (documented)")
        app.logger.info("  - /api/v1/health-doc (documented)")
        app.logger.info("  - /api/v1/config (documented)")
        app.logger.info("Error collection API registered at /api/v1/errors")
    except Exception as log_err:
        app.logger.debug(f"API registration logging skipped due to: {log_err}")


def setup_request_hooks(app: Flask) -> None:
    """设置请求钩子"""

    @app.before_request
    def before_request():
        """请求前处理"""
        # 记录请求信息
        if app.config.get("LOG_REQUESTS", False):
            app.logger.info(f"请求: {request.method} {request.url}")

        # 设置请求开始时间
        request.start_time = datetime.now(UTC)

    @app.after_request
    def after_request(response):
        """请求后处理"""
        # 添加响应头
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # 记录响应时间
        if hasattr(request, "start_time") and app.config.get("LOG_REQUESTS", False):
            duration = (datetime.now(UTC) - request.start_time).total_seconds()
            app.logger.info(f"响应: {response.status_code} - {duration:.3f}s")

        return response

    @app.teardown_appcontext
    def teardown_db(error):
        """清理应用上下文"""
        if error:
            app.logger.error(f"应用上下文错误: {error}")


# 用于开发环境的便捷函数
def create_dev_app() -> Flask:
    """创建开发环境应用"""
    return create_app("development")


def create_prod_app() -> Flask:
    """创建生产环境应用"""
    return create_app("production")


def create_test_app() -> Flask:
    """创建测试环境应用"""
    return create_app("testing")
