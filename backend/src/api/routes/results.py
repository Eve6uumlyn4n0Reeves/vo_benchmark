#
# 功能: 定义 /results API 路由。
#
from flask import Blueprint, request, jsonify, send_file  # type: ignore
from src.api.services.result import ResultService
from src.api.exceptions.base import (
    VOBenchmarkException,
    ExperimentNotFoundError,
    ValidationError,
)
import logging

logger = logging.getLogger(__name__)

bp = Blueprint("results", __name__, url_prefix="/api/v1/results")


@bp.route("/<string:experiment_id>/overview", methods=["GET"])
def get_results_overview(experiment_id: str):
    """聚合返回实验的概览数据（用于首屏渲染）。"""
    try:
        overview = result_service.get_results_overview(experiment_id)
        return jsonify(overview), 200
    except VOBenchmarkException as e:
        logger.error(f"获取结果概览业务错误: {e}")
        return jsonify(e.to_dict()), e.status_code
    except Exception as e:
        logger.error(f"获取结果概览内部错误: {e}")
        return jsonify({"error": "内部服务器错误"}), 500


@bp.route("/<string:experiment_id>/diagnose", methods=["GET"])
def diagnose_experiment(experiment_id: str):
    """诊断实验结果可见性与路径问题。"""
    try:
        diag = result_service.diagnose_experiment(experiment_id)
        return jsonify(diag), 200
    except VOBenchmarkException as e:
        logger.error(f"诊断实验业务错误: {e}")
        return jsonify(e.to_dict()), e.status_code
    except Exception as e:
        logger.error(f"诊断实验内部错误: {e}")
        return jsonify({"error": "内部服务器错误"}), 500


# 避免在模块导入时初始化服务，使用请求期实例化，确保配置上下文一致
# 为测试提供可 patch 的门面实例：src.api.routes.results.result_service
# 注意：不要在导入时持久化真实服务，保持每次方法调用内部新建


# Facade to allow tests to patch methods like export_results
class _ResultServiceFacade:
    def get_results_overview(self, experiment_id: str):
        return ResultService().get_results_overview(experiment_id)

    def diagnose_experiment(self, experiment_id: str):
        return ResultService().diagnose_experiment(experiment_id)

    def get_algorithm_result(self, experiment_id: str, algorithm_key: str):
        return ResultService().get_algorithm_result(experiment_id, algorithm_key)

    def get_frame_results(
        self, experiment_id: str, algorithm_key: str, start: int, limit: int
    ):
        return ResultService().get_frame_results(
            experiment_id, algorithm_key, start, limit
        )

    def get_pr_curve(self, experiment_id: str, algorithm_key: str):
        return ResultService().get_pr_curve(experiment_id, algorithm_key)

    def get_trajectory_data(
        self, experiment_id: str, algorithm_key: str, include_reference: bool = False
    ):
        return ResultService().get_trajectory_data(
            experiment_id, algorithm_key, include_reference=include_reference
        )

    def export_results(self, experiment_id: str, fmt: str):
        return ResultService().export_results(experiment_id, fmt)


# 模块级实例，供测试 patch
result_service = _ResultServiceFacade()


@bp.route("/<string:experiment_id>/<string:algorithm_key>", methods=["GET"])
def get_algorithm_result(experiment_id: str, algorithm_key: str):
    """获取算法结果"""
    try:
        result = result_service.get_algorithm_result(experiment_id, algorithm_key)
        return jsonify(result.dict()), 200

    except VOBenchmarkException as e:
        logger.error(f"获取算法结果业务错误: {e}")
        return jsonify(e.to_dict()), e.status_code
    except Exception as e:
        logger.error(f"获取算法结果内部错误: {e}")
        return jsonify({"error": "内部服务器错误"}), 500


@bp.route("/<string:experiment_id>/<string:algorithm_key>/frames", methods=["GET"])
def get_frame_results(experiment_id: str, algorithm_key: str):
    """获取帧级别结果"""
    try:
        # 获取分页参数（统一仅支持 page/per_page）
        page = request.args.get("page", default=1, type=int)
        per_page = request.args.get("per_page", default=100, type=int)

        if page < 1:
            raise ValidationError("页码必须大于等于1")
        if per_page < 1 or per_page > 1000:
            raise ValidationError("每页数量必须在1-1000之间")

        start = (page - 1) * per_page
        limit = per_page

        result = result_service.get_frame_results(
            experiment_id, algorithm_key, start, limit
        )
        return jsonify(result.dict()), 200

    except VOBenchmarkException as e:
        logger.error(f"获取帧结果业务错误: {e}")
        return jsonify(e.to_dict()), e.status_code
    except Exception as e:
        logger.error(f"获取帧结果内部错误: {e}")
        return jsonify({"error": "内部服务器错误"}), 500


@bp.route("/<string:experiment_id>/<string:algorithm_key>/pr-curve", methods=["GET"])
def get_pr_curve(experiment_id: str, algorithm_key: str):
    """获取PR曲线数据"""
    try:
        pr_curve = result_service.get_pr_curve(experiment_id, algorithm_key)
        return jsonify(pr_curve), 200

    except VOBenchmarkException as e:
        logger.error(f"获取PR曲线业务错误: {e}")
        return jsonify(e.to_dict()), e.status_code
    except Exception as e:
        logger.error(f"获取PR曲线内部错误: {e}")
        return jsonify({"error": "内部服务器错误"}), 500


@bp.route("/<string:experiment_id>/<string:algorithm_key>/trajectory", methods=["GET"])
def get_trajectory_data(experiment_id: str, algorithm_key: str):
    """获取轨迹数据
    支持参数 include_reference=true 在无GT时返回参考直线。
    """
    try:
        include_reference = (
            request.args.get("include_reference", default="false").lower() == "true"
        )
        trajectory_data = result_service.get_trajectory_data(
            experiment_id, algorithm_key, include_reference=include_reference
        )
        return jsonify(trajectory_data), 200

    except ExperimentNotFoundError as e:
        logger.error(f"获取轨迹数据业务错误: {e}")
        return jsonify(e.to_dict()), e.status_code
    except Exception as e:
        logger.error(f"获取轨迹数据内部错误: {e}")
        return jsonify({"error": "内部服务器错误"}), 500


@bp.route("/<string:experiment_id>/export", methods=["GET"])
def export_results(experiment_id: str):
    """导出实验结果"""
    try:
        # 获取导出格式参数
        format_param = request.args.get("format", "json")
        if format_param not in ["json", "csv", "xlsx", "pdf"]:
            raise ValidationError("不支持的导出格式，支持: json, csv, xlsx, pdf")

        # 使用请求期实例化，避免错误的配置上下文；并修复未定义变量问题
        file_data = result_service.export_results(experiment_id, format_param)

        # 设置响应头
        filename = f"experiment_{experiment_id}_results.{format_param}"
        content_type = {
            "json": "application/json",
            "csv": "text/csv",
            "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "pdf": "application/pdf",
        }[format_param]

        return send_file(
            file_data, as_attachment=True, download_name=filename, mimetype=content_type
        )

    except VOBenchmarkException as e:
        logger.error(f"导出结果业务错误: {e}")
        return jsonify(e.to_dict()), e.status_code
    except Exception as e:
        logger.error(f"导出结果内部错误: {e}")
        return jsonify({"error": "内部服务器错误"}), 500
