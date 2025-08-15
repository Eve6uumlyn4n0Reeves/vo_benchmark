"""
Experiments API Routes with OpenAPI Documentation

This module provides fully documented REST endpoints for experiment management
using Flask-RESTX for automatic OpenAPI/Swagger documentation generation.

All endpoints include comprehensive request/response documentation, error handling,
and example usage patterns.

Author:
    VO-Benchmark Team

Version:
    1.0.0
"""

from flask import jsonify
from src.utils.output_manager import output_manager

from flask import request, g
from flask_restx import Namespace, Resource, fields
from pydantic import ValidationError
from typing import Dict, Any, List
import logging

from src.api.docs import (
    api,
    experiment_config_model,
    experiment_model,
    task_model,
    error_model,
    validation_error_model,
    pagination_model,
)
from src.api.services.experiment import ExperimentService
from src.api.schemas.request import CreateExperimentRequest
from src.api.exceptions.base import VOBenchmarkException

logger = logging.getLogger(__name__)

# Create experiments namespace
experiments_ns = api.namespace(
    "experiments",
    path="/experiments-doc",
    description="""
    **Experiment Management Operations**

    This namespace provides endpoints for creating, monitoring, and managing
    visual odometry experiments. Experiments define the algorithms to test,
    datasets to process, and evaluation parameters.

    ## Workflow
    1. **Create Experiment**: POST /experiments/ with configuration
    2. **Monitor Progress**: GET /experiments/{id} for status updates
    3. **List Experiments**: GET /experiments/ for overview
    4. **Cancel Experiment**: DELETE /experiments/{id} if needed

    ## Algorithm Combinations
    Each experiment tests combinations of:
    - **Feature Types**: SIFT, ORB
    - **RANSAC Types**: STANDARD, PROSAC
    - **Sequences**: Dataset-specific sequences

    Results are automatically saved and can be retrieved via the results endpoints.
    """,
)

# Do not initialize service at import time to avoid wrong config context.
# Always create a fresh service inside request handlers to pick up correct app config.
# experiment_service = ExperimentService()  # removed

# Define request parser for query parameters
experiment_list_parser = experiments_ns.parser()
experiment_list_parser.add_argument(
    "page",
    type=int,
    default=1,
    help="Page number for pagination (1-based)",
    location="args",
)
experiment_list_parser.add_argument(
    "per_page",
    type=int,
    default=20,
    help="Number of experiments per page (max 100)",
    location="args",
)
experiment_list_parser.add_argument(
    "status",
    type=str,
    choices=["CREATED", "RUNNING", "COMPLETED", "FAILED", "CANCELLED"],
    help="Filter experiments by status",
    location="args",
)
experiment_list_parser.add_argument(
    "sort_by",
    type=str,
    choices=["created_at", "name", "status"],
    default="created_at",
    help="Sort experiments by field",
    location="args",
)
experiment_list_parser.add_argument(
    "sort_order",
    type=str,
    choices=["asc", "desc"],
    default="desc",
    help="Sort order",
    location="args",
)

# Define response models
experiment_list_response = experiments_ns.model(
    "ExperimentListResponse",
    {
        "experiments": fields.List(
            fields.Nested(experiment_model),
            required=True,
            description="List of experiments",
        ),
        "pagination": fields.Nested(
            pagination_model, required=True, description="Pagination information"
        ),
    },
)

task_response = experiments_ns.model(
    "TaskResponse",
    {
        "task": fields.Nested(
            task_model, required=True, description="Created task information"
        ),
        "experiment": fields.Nested(
            experiment_model,
            required=True,
            description="Associated experiment information",
        ),
    },
)


@experiments_ns.route("/")
class ExperimentList(Resource):
    """Experiment collection endpoint for listing and creating experiments."""

    @experiments_ns.doc("list_experiments")
    @experiments_ns.expect(experiment_list_parser)
    @experiments_ns.marshal_with(experiment_list_response)
    @experiments_ns.response(400, "Invalid query parameters", error_model)
    @experiments_ns.response(500, "Internal server error", error_model)
    def get(self):
        """
        List all experiments with filtering and pagination

        Retrieves a paginated list of experiments with optional filtering by status
        and sorting options. Supports comprehensive pagination metadata for
        building user interfaces.

        **Query Parameters:**
        - `page`: Page number (1-based, default: 1)
        - `per_page`: Items per page (1-100, default: 20)
        - `status`: Filter by experiment status
        - `sort_by`: Sort field (created_at, name, status)
        - `sort_order`: Sort direction (asc, desc)

        **Example Request:**
        ```
        GET /api/v1/experiments/?page=1&per_page=10&status=COMPLETED&sort_by=created_at&sort_order=desc
        ```

        **Response includes:**
        - List of experiments with full details
        - Pagination metadata for navigation
        - Total counts and page information
        """
        try:
            args = experiment_list_parser.parse_args()

            # Validate pagination parameters
            page = max(1, args.get("page", 1))
            per_page = min(100, max(1, args.get("per_page", 20)))

            # Create service per request to ensure correct config context
            service = ExperimentService()

            # Get experiments with filtering and pagination
            result = service.list_experiments(
                page=page,
                per_page=per_page,
                status=args.get("status"),
                sort_by=args.get("sort_by", "created_at"),
                sort_order=args.get("sort_order", "desc"),
            )

            return {
                "experiments": [
                    exp.model_dump() if hasattr(exp, "model_dump") else exp.dict()
                    for exp in result["experiments"]
                ],
                "pagination": result["pagination"],
            }

        except Exception as e:
            import traceback
            logger.error(f"Failed to list experiments: {e}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            experiments_ns.abort(500, f"Failed to retrieve experiments: {str(e)}")

    @experiments_ns.doc("create_experiment")
    @experiments_ns.expect(experiment_config_model, validate=True)
    @experiments_ns.marshal_with(task_response, code=201)
    @experiments_ns.response(400, "Validation error", validation_error_model)
    @experiments_ns.response(409, "Experiment name already exists", error_model)
    @experiments_ns.response(500, "Internal server error", error_model)
    def post(self):
        """
        Create a new experiment

        Creates and initializes a new visual odometry experiment with the specified
        configuration. The experiment will be queued for execution and can be
        monitored via the returned task ID.

        **Request Body:**
        The request must include a complete experiment configuration with:
        - Algorithm combinations to test
        - Dataset path and sequences
        - Output directory and processing parameters

        **Processing:**
        1. Validates all configuration parameters
        2. Checks dataset accessibility and format
        3. Creates experiment record in database
        4. Queues processing task for execution
        5. Returns task and experiment information

        **Example Request:**
        ```json
        {
          "name": "sift_orb_comparison_tum",
          "dataset_path": "/data/TUM_RGBD/rgbd_dataset_freiburg1_xyz",
          "output_dir": "/data/experiments/exp_001",
          "feature_types": ["SIFT", "ORB"],
          "ransac_types": ["STANDARD", "PROSAC"],
          "sequences": ["sequence01", "sequence02"],
          "num_runs": 3,
          "max_features": 5000,
          "parallel_jobs": 4
        }
        ```

        **Success Response:**
        Returns HTTP 201 with task and experiment details for monitoring progress.

        **Error Responses:**
        - 400: Invalid configuration parameters
        - 409: Experiment name already exists
        - 500: Internal processing error
        """
        try:
            # Get and validate request data
            data = request.get_json(force=True)
            if not data:
                experiments_ns.abort(400, "Request body cannot be empty")

            # Validate using Pydantic model
            try:
                request_model = CreateExperimentRequest(**data)
            except ValidationError as e:
                # Convert Pydantic errors to structured format
                error_details = []
                for error in e.errors():
                    error_details.append(
                        {
                            "field": ".".join(str(loc) for loc in error["loc"]),
                            "message": error["msg"],
                            "type": error["type"],
                        }
                    )
                return {"error": "Validation failed", "details": error_details}, 400

            # Create experiment through service (returns TaskResponse)
            service = ExperimentService()
            task = service.create_experiment(request_model)

            # Log successful creation
            logger.info(
                f"Experiment created successfully: {request_model.name} "
                f"(ID: {task.experiment_id}, Task: {task.task_id})"
            )

            # 构建响应 - 使用 task 中的信息，避免依赖可能尚未保存的实验数据
            task_data = task.model_dump() if hasattr(task, "model_dump") else task.dict()

            # 构建基本的实验信息响应
            experiment_data = {
                "experiment_id": task.experiment_id,
                "name": request_model.name,
                "status": task_data.get("status"),
                "config": {
                    "name": request_model.name,
                    "dataset_path": request_model.dataset_path,
                    "output_dir": request_model.output_dir,
                    "feature_types": request_model.feature_types,
                    "ransac_types": request_model.ransac_types,
                    "sequences": request_model.sequences,
                    "num_runs": request_model.num_runs,
                    "max_features": request_model.max_features,
                    "parallel_jobs": request_model.parallel_jobs,
                },
                "created_at": task_data.get("created_at"),
                "started_at": task_data.get("created_at"),
                "completed_at": None,
                "summary": None,
                "algorithms": [],
            }

            return {
                "task": task_data,
                "experiment": experiment_data,
            }, 201

        except VOBenchmarkException as e:
            logger.warning(f"Experiment creation failed: {e}")
            experiments_ns.abort(400, str(e))
        except Exception as e:
            logger.error(f"Unexpected error creating experiment: {e}")
            experiments_ns.abort(500, f"Failed to create experiment: {str(e)}")


@experiments_ns.route("/<string:experiment_id>")
@experiments_ns.param("experiment_id", "Unique experiment identifier")
class ExperimentDetail(Resource):
    """Individual experiment endpoint for retrieval, updates, and deletion."""

    @experiments_ns.doc("get_experiment")
    @experiments_ns.marshal_with(experiment_model)
    @experiments_ns.response(404, "Experiment not found", error_model)
    @experiments_ns.response(500, "Internal server error", error_model)
    def get(self, experiment_id: str):
        """
        Get experiment details by ID

        Retrieves comprehensive information about a specific experiment,
        including configuration, status, progress, and summary statistics.

        **Path Parameters:**
        - `experiment_id`: Unique experiment identifier

        **Response includes:**
        - Complete experiment configuration
        - Current status and progress information
        - Execution timestamps and duration
        - Summary statistics (if completed)
        - List of algorithm combinations tested

        **Example Response:**
        ```json
        {
          "experiment_id": "exp_001",
          "name": "sift_orb_comparison_tum",
          "status": "COMPLETED",
          "config": { ... },
          "created_at": "2024-01-15T10:30:00Z",
          "completed_at": "2024-01-15T11:15:30Z",
          "summary": {
            "total_runs": 6,
            "successful_runs": 6,
            "failed_runs": 0,
            "total_processing_time": 2730.5,
            "average_fps": 12.3
          },
          "algorithms": ["SIFT_STANDARD", "SIFT_PROSAC", "ORB_STANDARD", "ORB_PROSAC"]
        }
        ```
        """
        try:
            service = ExperimentService()
            experiment = service.get_experiment(experiment_id)
            if not experiment:
                experiments_ns.abort(404, f"Experiment {experiment_id} not found")

            return (
                experiment.model_dump()
                if hasattr(experiment, "model_dump")
                else experiment.dict()
            )

        except Exception as e:
            logger.error(f"Failed to get experiment {experiment_id}: {e}")
            experiments_ns.abort(500, f"Failed to retrieve experiment: {str(e)}")

    @experiments_ns.doc("delete_experiment")
    @experiments_ns.response(204, "Experiment deleted successfully")
    @experiments_ns.response(404, "Experiment not found", error_model)
    @experiments_ns.response(400, "Cannot delete experiment", error_model)
    @experiments_ns.response(500, "Internal server error", error_model)
    def delete(self, experiment_id: str):
        """
        Delete an experiment

        Deletes an experiment and all its associated data including results,
        configuration, and output files. This operation is irreversible.

        **Path Parameters:**
        - `experiment_id`: Unique experiment identifier

        **Behavior:**
        - Removes experiment record from storage
        - Deletes all associated result files
        - Cleans up output directory if it exists
        - Cannot be undone once executed

        **Restrictions:**
        - Running experiments should be stopped before deletion
        - All associated data will be permanently lost
        """
        try:
            service = ExperimentService()

            # Check if experiment exists
            experiment = service.get_experiment(experiment_id)
            if not experiment:
                experiments_ns.abort(404, f"Experiment {experiment_id} not found")

            # Delete the experiment
            service.delete_experiment(experiment_id)
            logger.info(f"Successfully deleted experiment: {experiment_id}")

            return "", 204

        except VOBenchmarkException as e:
            logger.warning(f"Cannot delete experiment {experiment_id}: {e}")
            experiments_ns.abort(400, str(e))
        except Exception as e:
            logger.error(f"Unexpected error deleting experiment {experiment_id}: {e}")
            experiments_ns.abort(500, f"Failed to delete experiment: {str(e)}")


@experiments_ns.route("/<string:experiment_id>/history")
@experiments_ns.param("experiment_id", "Unique experiment identifier")
class ExperimentHistory(Resource):
    @experiments_ns.doc("get_experiment_history")
    def get(self, experiment_id: str):
        """Get experiment history (documented)
        Mirrors legacy behavior to provide history snapshots.
        Query: hours (default 24, max 168)
        """
        try:
            service = ExperimentService()
            hours = request.args.get("hours", default=24, type=int)
            if hours <= 0 or hours > 168:
                return {"error": "hours must be between 1 and 168"}, 400
            history_data = service.get_experiment_history(experiment_id, hours)
            return history_data
        except VOBenchmarkException as e:
            logger.warning(f"Get experiment history failed: {e}")
            experiments_ns.abort(400, str(e))
        except Exception as e:
            logger.error(f"Unexpected error getting history: {e}")
            experiments_ns.abort(500, f"Failed to get experiment history: {str(e)}")


@experiments_ns.route("/preview-output-path")
class ExperimentPreviewOutputPath(Resource):
    @experiments_ns.doc("preview_output_path")
    def post(self):
        """Preview experiment output path (documented)
        Returns a preview of directory layout without creating it.
        Body: { experiment_name: string, dataset_path?: string }
        """
        try:
            data = request.get_json(force=True) or {}
            experiment_name = data.get("experiment_name") or data.get("name") or "experiment"
            dataset_path = data.get("dataset_path") or ""
            dataset_name = (dataset_path.split("\\")[-1] or dataset_path.split("/")[-1]) if dataset_path else "dataset"

            experiment_id = output_manager.generate_experiment_id(experiment_name)
            preview_dir = output_manager.root_output_dir / experiment_id

            directory_structure = {
                "results": "实验结果文件",
                "results/trajectories": "轨迹数据文件",
                "results/metrics": "评估指标文件",
                "results/visualizations": "可视化图表文件",
                "logs": "运行日志文件",
                "cache": "缓存文件",
                "config": "配置文件",
                "raw_data": "原始数据文件",
                "raw_data/features": "特征提取数据",
                "raw_data/matches": "特征匹配数据",
                "reports": "实验报告文件",
            }

            return (
                {
                    "experiment_id": experiment_id,
                    "output_path": str(preview_dir),
                    "dataset_name": dataset_name,
                    "directory_structure": directory_structure,
                },
                200,
            )
        except Exception as e:
            logger.error(f"Preview output path failed: {e}")
            return {"error": "预览输出目录失败"}, 500

