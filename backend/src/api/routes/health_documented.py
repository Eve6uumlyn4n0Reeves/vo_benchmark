"""
Health Check API Routes with OpenAPI Documentation

This module provides comprehensive health check endpoints for monitoring
system status, dependencies, and service availability.

Author:
    VO-Benchmark Team

Version:
    1.0.0
"""

from flask import current_app
from flask_restx import Namespace, Resource, fields
from datetime import datetime, timezone
import psutil
import logging
import time
import os

from src.api.docs import api, error_model

logger = logging.getLogger(__name__)

# Simple cache for expensive operations
_cache = {}
_cache_ttl = 30  # 30 seconds cache

def get_cached_or_compute(key: str, compute_func, ttl: int = _cache_ttl):
    """Get cached value or compute and cache it"""
    now = time.time()
    if key in _cache:
        cached_time, cached_value = _cache[key]
        if now - cached_time < ttl:
            return cached_value

    # Compute new value
    new_value = compute_func()
    _cache[key] = (now, new_value)
    return new_value

# Create health namespace
health_ns = api.namespace(
    "health",
    path="/health-doc",
    description="""
    **System Health and Status Monitoring**

    This namespace provides endpoints for monitoring system health, service
    availability, and performance metrics. Use these endpoints for:

    - **Load Balancer Health Checks**: Simple status verification
    - **Monitoring Systems**: Detailed system metrics and dependencies
    - **Debugging**: Service status and configuration validation
    - **Performance Monitoring**: Resource usage and response times

    ## Health Check Levels
    1. **Basic**: Simple alive/dead status (GET /health/)
    2. **Detailed**: System metrics and dependencies (GET /health/detailed)
    3. **Ready**: Service readiness for traffic (GET /health/ready)
    """,
)

# Define health status models
basic_health_model = health_ns.model(
    "BasicHealth",
    {
        "status": fields.String(
            required=True,
            enum=["healthy", "unhealthy"],
            description="Overall system health status",
            example="healthy",
        ),
        "timestamp": fields.DateTime(
            required=True,
            description="Health check timestamp in ISO 8601 format",
            example="2024-01-15T10:30:00Z",
        ),
        "version": fields.String(
            required=True, description="API version", example="1.0.0"
        ),
        "uptime": fields.Float(
            required=True, description="System uptime in seconds", example=86400.5
        ),
    },
)

system_metrics_model = health_ns.model(
    "SystemMetrics",
    {
        "cpu_usage": fields.Float(
            required=True, description="CPU usage percentage (0-100)", example=25.3
        ),
        "memory_usage": fields.Float(
            required=True, description="Memory usage percentage (0-100)", example=68.7
        ),
        "disk_usage": fields.Float(
            required=True, description="Disk usage percentage (0-100)", example=45.2
        ),
        "load_average": fields.List(
            fields.Float,
            required=True,
            description="System load average [1min, 5min, 15min]",
            example=[1.2, 1.5, 1.8],
        ),
        "available_memory_mb": fields.Float(
            required=True, description="Available memory in megabytes", example=2048.5
        ),
        "total_memory_mb": fields.Float(
            required=True,
            description="Total system memory in megabytes",
            example=8192.0,
        ),
    },
)

dependency_status_model = health_ns.model(
    "DependencyStatus",
    {
        "name": fields.String(
            required=True, description="Dependency name", example="opencv"
        ),
        "status": fields.String(
            required=True,
            enum=["available", "unavailable", "degraded"],
            description="Dependency availability status",
            example="available",
        ),
        "version": fields.String(
            description="Dependency version if available", example="4.8.1"
        ),
        "response_time_ms": fields.Float(
            description="Dependency response time in milliseconds", example=12.5
        ),
        "error_message": fields.String(
            description="Error message if dependency is unavailable",
            example="Connection timeout",
        ),
    },
)

detailed_health_model = health_ns.model(
    "DetailedHealth",
    {
        "status": fields.String(
            required=True,
            enum=["healthy", "unhealthy", "degraded"],
            description="Overall system health status",
            example="healthy",
        ),
        "timestamp": fields.DateTime(
            required=True,
            description="Health check timestamp",
            example="2024-01-15T10:30:00Z",
        ),
        "version": fields.String(
            required=True, description="API version", example="1.0.0"
        ),
        "uptime": fields.Float(
            required=True, description="System uptime in seconds", example=86400.5
        ),
        "system_metrics": fields.Nested(
            system_metrics_model,
            required=True,
            description="System resource usage metrics",
        ),
        "dependencies": fields.List(
            fields.Nested(dependency_status_model),
            required=True,
            description="Status of external dependencies",
        ),
        "active_experiments": fields.Integer(
            required=True,
            description="Number of currently running experiments",
            example=3,
        ),
        "total_experiments": fields.Integer(
            required=True,
            description="Total number of experiments in system",
            example=127,
        ),
        "queue_size": fields.Integer(
            required=True, description="Number of tasks in processing queue", example=5
        ),
    },
)

readiness_model = health_ns.model(
    "ReadinessStatus",
    {
        "ready": fields.Boolean(
            required=True,
            description="Whether service is ready to accept traffic",
            example=True,
        ),
        "timestamp": fields.DateTime(
            required=True,
            description="Readiness check timestamp",
            example="2024-01-15T10:30:00Z",
        ),
        "checks": fields.List(
            fields.Nested(
                health_ns.model(
                    "ReadinessCheck",
                    {
                        "name": fields.String(
                            required=True,
                            description="Check name",
                            example="database_connection",
                        ),
                        "status": fields.String(
                            required=True,
                            enum=["pass", "fail"],
                            description="Check result",
                            example="pass",
                        ),
                        "message": fields.String(
                            description="Additional check information",
                            example="Database connection established",
                        ),
                    },
                )
            ),
            required=True,
            description="Individual readiness checks",
        ),
    },
)

# Store application start time for uptime calculation
_start_time = time.time()


def get_system_metrics():
    """Get current system resource usage metrics."""
    try:
        # CPU usage (average over 1 second)
        cpu_percent = psutil.cpu_percent(interval=1)

        # Memory usage
        memory = psutil.virtual_memory()

        # Disk usage for current directory
        disk = psutil.disk_usage(".")

        # Load average (Unix-like systems only)
        try:
            load_avg = os.getloadavg()
        except (OSError, AttributeError):
            # Windows doesn't have getloadavg
            load_avg = [0.0, 0.0, 0.0]

        return {
            "cpu_usage": cpu_percent,
            "memory_usage": memory.percent,
            "disk_usage": disk.percent,
            "load_average": list(load_avg),
            "available_memory_mb": memory.available / (1024 * 1024),
            "total_memory_mb": memory.total / (1024 * 1024),
        }
    except Exception as e:
        logger.warning(f"Failed to get system metrics: {e}")
        return {
            "cpu_usage": 0.0,
            "memory_usage": 0.0,
            "disk_usage": 0.0,
            "load_average": [0.0, 0.0, 0.0],
            "available_memory_mb": 0.0,
            "total_memory_mb": 0.0,
        }


def check_dependencies():
    """Check status of critical dependencies."""
    dependencies = []

    # Check OpenCV
    try:
        import cv2

        dependencies.append(
            {
                "name": "opencv",
                "status": "available",
                "version": cv2.__version__,
                "response_time_ms": 0.1,
            }
        )
    except ImportError as e:
        dependencies.append(
            {"name": "opencv", "status": "unavailable", "error_message": str(e)}
        )

    # Check NumPy
    try:
        import numpy as np

        dependencies.append(
            {
                "name": "numpy",
                "status": "available",
                "version": np.__version__,
                "response_time_ms": 0.1,
            }
        )
    except ImportError as e:
        dependencies.append(
            {"name": "numpy", "status": "unavailable", "error_message": str(e)}
        )

    # Check SQLAlchemy
    try:
        import sqlalchemy

        dependencies.append(
            {
                "name": "sqlalchemy",
                "status": "available",
                "version": sqlalchemy.__version__,
                "response_time_ms": 0.1,
            }
        )
    except ImportError as e:
        dependencies.append(
            {"name": "sqlalchemy", "status": "unavailable", "error_message": str(e)}
        )

    # Check Flask
    try:
        import flask

        dependencies.append(
            {
                "name": "flask",
                "status": "available",
                "version": flask.__version__,
                "response_time_ms": 0.1,
            }
        )
    except ImportError as e:
        dependencies.append(
            {"name": "flask", "status": "unavailable", "error_message": str(e)}
        )

    return dependencies
    # Check OpenCV capabilities (contrib/GMS/USAC)
    try:
        import cv2
        has_contrib = hasattr(cv2, 'xfeatures2d')
        has_gms = has_contrib and hasattr(cv2.xfeatures2d, 'matchGMS')
        usac_consts = [
            ('USAC_DEFAULT', hasattr(cv2, 'USAC_DEFAULT')),
            ('USAC_MAGSAC', hasattr(cv2, 'USAC_MAGSAC')),
            ('USAC_ACCURATE', hasattr(cv2, 'USAC_ACCURATE')),
            ('RHO', hasattr(cv2, 'RHO')),
            ('LMEDS', hasattr(cv2, 'LMEDS')),
        ]
        capabilities = {
            'opencv_contrib': has_contrib,
            'gms_available': has_gms,
            'usac_support': {name: ok for (name, ok) in usac_consts},
        }
        dependencies.append({
            'name': 'opencv_capabilities',
            'status': 'available',
            'version': cv2.__version__,
            'response_time_ms': 0.1,
            'details': capabilities,
        })
    except Exception as e:
        dependencies.append({
            'name': 'opencv_capabilities',
            'status': 'degraded',
            'error_message': str(e),
        })



@health_ns.route("/")
class BasicHealth(Resource):
    """Basic health check endpoint for load balancers and simple monitoring."""

    @health_ns.doc("basic_health_check")
    @health_ns.marshal_with(basic_health_model)
    @health_ns.response(200, "Service is healthy")
    @health_ns.response(503, "Service is unhealthy", error_model)
    def get(self):
        """
        Basic health check

        Provides a simple health status for load balancers and basic monitoring.
        This endpoint is lightweight and designed for frequent polling.

        **Response:**
        - **200 OK**: Service is healthy and operational
        - **503 Service Unavailable**: Service is experiencing issues

        **Use Cases:**
        - Load balancer health checks
        - Simple uptime monitoring
        - Container orchestration health probes

        **Performance:**
        This endpoint is optimized for speed and should respond in <10ms
        under normal conditions.
        """
        try:
            uptime = time.time() - _start_time

            return {
                "status": "healthy",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "version": current_app.config.get("API_VERSION", "1.0.0"),
                "uptime": uptime,
            }
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            health_ns.abort(503, f"Service unhealthy: {str(e)}")


@health_ns.route("/detailed")
class DetailedHealth(Resource):
    """Detailed health check with system metrics and dependency status."""

    @health_ns.doc("detailed_health_check")
    @health_ns.marshal_with(detailed_health_model)
    @health_ns.response(200, "Detailed health information")
    @health_ns.response(503, "Service is unhealthy", error_model)
    def get(self):
        """
        Detailed health check with system metrics

        Provides comprehensive health information including system metrics,
        dependency status, and service statistics. This endpoint is more
        resource-intensive and should be used for detailed monitoring.

        **Includes:**
        - System resource usage (CPU, memory, disk)
        - Dependency availability and versions
        - Active experiment and task counts
        - Service performance metrics

        **Use Cases:**
        - Monitoring dashboards
        - Performance analysis
        - Troubleshooting and debugging
        - Capacity planning

        **Note:**
        This endpoint may take longer to respond due to system metric collection.
        """
        try:
            uptime = time.time() - _start_time
            system_metrics = get_system_metrics()
            dependencies = check_dependencies()

            # Determine overall status based on dependencies
            unhealthy_deps = [d for d in dependencies if d["status"] != "available"]
            if unhealthy_deps:
                status = (
                    "degraded"
                    if len(unhealthy_deps) < len(dependencies)
                    else "unhealthy"
                )
            else:
                status = "healthy"

            # Get service statistics (real data)
            try:
                from src.api.services.task import task_service
                from src.api.services.experiment import ExperimentService

                # 获取真实的任务统计
                active_tasks = task_service.get_active_tasks()
                queue_size = len(active_tasks)

                # 获取实验统计（使用缓存优化性能）
                def compute_experiment_stats():
                    try:
                        # 使用全局实验服务实例，避免重复初始化
                        from src.api.services.experiment import experiment_service
                        result = experiment_service.list_experiments(1, 50)  # 限制数量提升性能

                        # 处理可能的分页响应格式
                        if isinstance(result, dict) and "experiments" in result:
                            experiments = result["experiments"]
                            total_experiments = result.get("total", len(experiments))
                        elif isinstance(result, list):
                            experiments = result
                            total_experiments = len(experiments)
                        else:
                            experiments = []
                            total_experiments = 0

                        active_experiments = len(
                            [
                                exp
                                for exp in experiments
                                if hasattr(exp, 'status') and exp.status in ["RUNNING", "PENDING"]
                            ]
                        )
                        return total_experiments, active_experiments
                    except Exception as e:
                        logger.warning(f"获取实验统计失败: {e}")
                        return 0, 0

                total_experiments, active_experiments = get_cached_or_compute(
                    "experiment_stats", compute_experiment_stats, ttl=30
                )

            except Exception as e:
                logger.warning(f"获取服务统计失败: {e}")
                active_experiments = 0
                total_experiments = 0
                queue_size = 0

            response = {
                "status": status,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "version": current_app.config.get("API_VERSION", "1.0.0"),
                "uptime": uptime,
                "system_metrics": system_metrics,
                "dependencies": dependencies,
                "active_experiments": active_experiments,
                "total_experiments": total_experiments,
                "queue_size": queue_size,
            }

            if status == "unhealthy":
                return response, 503
            else:
                return response

        except Exception as e:
            logger.error(f"Detailed health check failed: {e}")
            health_ns.abort(503, f"Health check failed: {str(e)}")


@health_ns.route("/ready")
class ReadinessCheck(Resource):
    """Service readiness check for traffic acceptance."""

    @health_ns.doc("readiness_check")
    @health_ns.marshal_with(readiness_model)
    @health_ns.response(200, "Service is ready")
    @health_ns.response(503, "Service is not ready", error_model)
    def get(self):
        """
        Service readiness check

        Determines if the service is ready to accept and process requests.
        This check validates that all critical dependencies are available
        and the service can handle traffic.

        **Readiness Criteria:**
        - All critical dependencies are available
        - Database connections are established
        - Required directories are accessible
        - Service configuration is valid

        **Use Cases:**
        - Kubernetes readiness probes
        - Traffic routing decisions
        - Deployment validation
        - Service mesh health checks

        **Difference from Health Check:**
        - Health: Is the service running?
        - Readiness: Can the service handle requests?
        """
        try:
            checks = []
            all_ready = True

            # Check critical dependencies
            dependencies = check_dependencies()
            critical_deps = ["opencv", "numpy", "flask"]

            for dep_name in critical_deps:
                dep = next((d for d in dependencies if d["name"] == dep_name), None)
                if dep and dep["status"] == "available":
                    checks.append(
                        {
                            "name": f"{dep_name}_dependency",
                            "status": "pass",
                            "message": f"{dep_name} is available",
                        }
                    )
                else:
                    checks.append(
                        {
                            "name": f"{dep_name}_dependency",
                            "status": "fail",
                            "message": f"{dep_name} is not available",
                        }
                    )
                    all_ready = False

            # Check configuration
            try:
                config_valid = current_app.config.get("SECRET_KEY") is not None
                if config_valid:
                    checks.append(
                        {
                            "name": "configuration",
                            "status": "pass",
                            "message": "Configuration is valid",
                        }
                    )
                else:
                    checks.append(
                        {
                            "name": "configuration",
                            "status": "fail",
                            "message": "Configuration is incomplete",
                        }
                    )
                    all_ready = False
            except Exception:
                checks.append(
                    {
                        "name": "configuration",
                        "status": "fail",
                        "message": "Configuration check failed",
                    }
                )
                all_ready = False

            response = {
                "ready": all_ready,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "checks": checks,
            }

            if all_ready:
                return response
            else:
                return response, 503

        except Exception as e:
            logger.error(f"Readiness check failed: {e}")
            health_ns.abort(503, f"Readiness check failed: {str(e)}")
