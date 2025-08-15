"""
API Documentation Module

This module provides OpenAPI/Swagger documentation for all REST endpoints
in the VO-Benchmark API. It defines request/response models, error schemas,
and comprehensive endpoint documentation.

Author:
    VO-Benchmark Team

Version:
    1.0.0
"""
import warnings
# Suppress DeprecationWarning emitted by flask_restx using jsonschema.RefResolver
warnings.filterwarnings(
    "ignore",
    category=DeprecationWarning,
    module=r"flask_restx(\.|$)",
)
warnings.filterwarnings(
    "ignore",
    message="jsonschema.RefResolver is deprecated",
    category=DeprecationWarning,
)


from flask_restx import Api, Namespace, Resource, fields
from flask import Blueprint
from typing import Dict, Any

# Create API documentation blueprint
doc_bp = Blueprint("api_docs", __name__)

# Initialize Flask-RESTX API with comprehensive configuration
api = Api(
    doc_bp,
    version="1.0.0",
    title="VO-Benchmark API",
    description="""
    **Visual Odometry Feature Matching Evaluation System API**

    This API provides comprehensive endpoints for managing visual odometry experiments,
    monitoring task execution, and retrieving evaluation results. The system supports
    multiple feature extraction algorithms (SIFT, ORB) and RANSAC variants for robust
    pose estimation.

    ## Key Features
    - **Experiment Management**: Create, monitor, and manage feature matching experiments
    - **Real-time Monitoring**: Track experiment progress and performance metrics
    - **Result Analysis**: Retrieve detailed evaluation results and visualizations
    - **Algorithm Comparison**: Compare different algorithm combinations

    ## Authentication
    Currently, the API does not require authentication. This may change in future versions.

    ## Rate Limiting
    API requests are rate-limited to prevent abuse. See individual endpoints for specific limits.

    ## Error Handling
    All endpoints return structured error responses with appropriate HTTP status codes.
    See the Error Models section for detailed error response formats.
    """,
    doc="/docs/",
    contact="VO-Benchmark Team",
    contact_email="team@vo-benchmark.org",
    license="MIT",
    license_url="https://opensource.org/licenses/MIT",
    authorizations={
        "apikey": {
            "type": "apiKey",
            "in": "header",
            "name": "X-API-Key",
            "description": "API key for authentication (future implementation)",
        }
    },
    security="apikey",
)

# Define common error models
error_model = api.model(
    "Error",
    {
        "error_code": fields.String(
            required=True,
            description="Machine-readable error code",
            example="VALIDATION_ERROR",
        ),
        "message": fields.String(
            required=True,
            description="Human-readable error message",
            example="Invalid input parameters provided",
        ),
        "details": fields.Raw(
            description="Additional error details and context",
            example={"field": "dataset_path", "issue": "Path does not exist"},
        ),
        "timestamp": fields.DateTime(
            required=True,
            description="ISO 8601 timestamp when error occurred",
            example="2024-01-15T10:30:00Z",
        ),
    },
)

validation_error_model = api.model(
    "ValidationError",
    {
        "error": fields.String(
            required=True,
            description="Error type identifier",
            example="Validation failed",
        ),
        "details": fields.List(
            fields.Nested(
                api.model(
                    "ValidationDetail",
                    {
                        "field": fields.String(
                            required=True,
                            description="Field that failed validation",
                            example="feature_types",
                        ),
                        "message": fields.String(
                            required=True,
                            description="Validation error message",
                            example="At least one feature type must be specified",
                        ),
                        "type": fields.String(
                            required=True,
                            description="Type of validation error",
                            example="value_error.missing",
                        ),
                    },
                )
            ),
            description="List of validation errors",
        ),
    },
)

# Define pagination model
pagination_model = api.model(
    "Pagination",
    {
        "page": fields.Integer(
            required=True, description="Current page number (1-based)", example=1
        ),
        "limit": fields.Integer(
            required=True, description="Number of items per page", example=20
        ),
        "total": fields.Integer(
            required=True, description="Total number of items", example=150
        ),
        "total_pages": fields.Integer(
            required=True, description="Total number of pages", example=8
        ),
        "has_previous": fields.Boolean(
            required=True, description="Whether there is a previous page", example=False
        ),
        "has_next": fields.Boolean(
            required=True, description="Whether there is a next page", example=True
        ),
    },
)

# Define experiment configuration model
experiment_config_model = api.model(
    "ExperimentConfig",
    {
        "name": fields.String(
            required=True,
            description="Human-readable experiment name",
            example="sift_orb_comparison_tum_rgbd",
            min_length=1,
            max_length=100,
        ),
        "dataset_path": fields.String(
            required=True,
            description="Absolute path to dataset root directory",
            example="/data/datasets/TUM_RGBD/rgbd_dataset_freiburg1_xyz",
        ),
        "output_dir": fields.String(
            required=True,
            description="Directory where experiment results will be saved",
            example="/data/experiments/exp_001_results",
        ),
        "feature_types": fields.List(
            fields.String(enum=["SIFT", "ORB", "AKAZE", "BRISK", "KAZE", "SURF"]),
            required=True,
            description="List of feature extraction algorithms to evaluate",
            example=["SIFT", "ORB", "AKAZE"],
            min_items=1,
        ),
        "ransac_types": fields.List(
            fields.String(enum=[
                "STANDARD", "PROSAC", "USAC_DEFAULT", "USAC_MAGSAC", "USAC_ACCURATE", "RHO", "LMEDS"
            ]),
            required=True,
            description="List of RANSAC variants to evaluate",
            example=["STANDARD", "USAC_MAGSAC"],
            min_items=1,
        ),
        "sequences": fields.List(
            fields.String,
            description="Dataset sequences to process (empty = all sequences)",
            example=["sequence01", "sequence02"],
        ),
        "num_runs": fields.Integer(
            default=1,
            description="Number of runs per algorithm combination for statistical analysis",
            example=3,
            min=1,
            max=10,
        ),
        "max_features": fields.Integer(
            default=5000,
            description="Maximum number of features to extract per image",
            example=5000,
            min=100,
            max=20000,
        ),
        "parallel_jobs": fields.Integer(
            default=4,
            description="Number of parallel processing jobs",
            example=4,
            min=1,
            max=16,
        ),
    },
)

# Define task status model
task_model = api.model(
    "Task",
    {
        "task_id": fields.String(
            required=True,
            description="Unique task identifier",
            example="task_001_20240115_103000",
        ),
        "experiment_id": fields.String(
            required=True,
            description="Associated experiment identifier",
            example="exp_001",
        ),
        "status": fields.String(
            required=True,
            enum=["PENDING", "RUNNING", "COMPLETED", "FAILED", "CANCELLED"],
            description="Current task status",
            example="RUNNING",
        ),
        "progress": fields.Float(
            required=True,
            description="Task completion progress (0.0 to 1.0)",
            example=0.65,
            min=0.0,
            max=1.0,
        ),
        "created_at": fields.DateTime(
            required=True,
            description="Task creation timestamp",
            example="2024-01-15T10:30:00Z",
        ),
        "started_at": fields.DateTime(
            description="Task start timestamp", example="2024-01-15T10:30:05Z"
        ),
        "completed_at": fields.DateTime(
            description="Task completion timestamp", example="2024-01-15T11:15:30Z"
        ),
        "error_message": fields.String(
            description="Error message if task failed",
            example="Dataset not found at specified path",
        ),
        "current_step": fields.String(
            description="Current processing step description",
            example="Processing sequence02 with SIFT features",
        ),
        "estimated_remaining_time": fields.Integer(
            description="Estimated remaining time in seconds", example=1800
        ),
    },
)

# Define experiment response model
experiment_model = api.model(
    "Experiment",
    {
        "experiment_id": fields.String(
            required=True, description="Unique experiment identifier", example="exp_001"
        ),
        "name": fields.String(
            required=True,
            description="Experiment name",
            example="sift_orb_comparison_tum_rgbd",
        ),
        "status": fields.String(
            required=True,
            enum=["CREATED", "RUNNING", "COMPLETED", "FAILED", "CANCELLED"],
            description="Current experiment status",
            example="COMPLETED",
        ),
        "config": fields.Nested(
            experiment_config_model,
            required=True,
            description="Experiment configuration parameters",
        ),
        "created_at": fields.DateTime(
            required=True,
            description="Experiment creation timestamp",
            example="2024-01-15T10:30:00Z",
        ),
        "started_at": fields.DateTime(
            description="Experiment start timestamp", example="2024-01-15T10:30:05Z"
        ),
        "completed_at": fields.DateTime(
            description="Experiment completion timestamp",
            example="2024-01-15T11:15:30Z",
        ),
        "summary": fields.Raw(
            description="Experiment summary statistics",
            example={
                "total_runs": 6,
                "successful_runs": 5,
                "failed_runs": 1,
                "total_processing_time": 2730.5,
                "average_fps": 12.3,
            },
        ),
        "algorithms": fields.List(
            fields.String,
            description="List of algorithm combinations tested",
            example=["SIFT_STANDARD", "SIFT_PROSAC", "ORB_STANDARD", "ORB_PROSAC"],
        ),
    },
)

# Export models for use in route definitions
__all__ = [
    "api",
    "doc_bp",
    "error_model",
    "validation_error_model",
    "pagination_model",
    "experiment_config_model",
    "task_model",
    "experiment_model",
]
