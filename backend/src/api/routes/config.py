"""
配置管理API

提供客户端配置获取和系统配置管理功能。
"""

from flask import jsonify, request
from flask_restx import Namespace, Resource, fields
from src.api.docs import api
from src.config.manager import get_config, get_client_config
import logging

logger = logging.getLogger(__name__)

# 仅使用 Flask-RESTX Namespace（不再导出 Blueprint，避免重复注册与冲突）
config_ns = api.namespace("config", description="配置管理操作")

# 定义响应模型
experiment_config_model = config_ns.model(
    "ExperimentConfig",
    {
        "defaultRuns": fields.Integer(description="默认运行次数"),
        "defaultParallelJobs": fields.Integer(description="默认并行任务数"),
        "defaultMaxFeatures": fields.Integer(description="默认最大特征数"),
        "defaultRansacThreshold": fields.Float(description="默认RANSAC阈值"),
        "defaultRansacConfidence": fields.Float(description="默认RANSAC置信度"),
        "defaultRansacMaxIters": fields.Integer(description="默认RANSAC最大迭代次数"),
        "defaultRatioThreshold": fields.Float(description="默认匹配器ratio阈值"),
    },
)

algorithms_config_model = config_ns.model(
    "AlgorithmsConfig",
    {
        "featureTypes": fields.List(fields.String, description="支持的特征类型"),
        "ransacTypes": fields.List(fields.String, description="支持的RANSAC类型"),
    },
)

client_config_model = config_ns.model(
    "ClientConfig",
    {
        "experiment": fields.Nested(experiment_config_model),
        "algorithms": fields.Nested(algorithms_config_model),
    },
)


@config_ns.route("/client")
class ClientConfig(Resource):
    @config_ns.doc("get_client_config")
    @config_ns.marshal_with(client_config_model)
    def get(self):
        """获取客户端配置

        返回前端需要的配置信息，包括实验默认参数和支持的算法类型。
        这些配置可以被前端用来初始化表单默认值和选项列表。
        """
        try:
            client_config = get_client_config()
            logger.info("Client configuration requested")
            return client_config
        except Exception as e:
            logger.error(f"Failed to get client config: {e}")
            return {"error": "Failed to get client configuration"}, 500


@config_ns.route("/system")
class SystemConfig(Resource):
    @config_ns.doc("get_system_config")
    def get(self):
        """获取系统配置信息

        返回系统级别的配置信息，用于监控和调试。
        注意：敏感信息（如密钥）不会被返回。
        """
        try:
            config = get_config()

            # 只返回非敏感的系统配置
            system_config = {
                "environment": config.environment.value,
                "debug": config.debug,
                "host": config.host,
                "port": config.port,
                "database": {
                    "pool_size": config.database.pool_size,
                    "pool_timeout": config.database.pool_timeout,
                    "echo": config.database.echo,
                },
                "storage": {
                    "datasets_root": config.storage.datasets_root,
                    "results_root": config.storage.results_root,
                    "temp_root": config.storage.temp_root,
                },
                "logging": {
                    "level": config.logging.level,
                    "format": config.logging.format,
                    "to_stdout": config.logging.to_stdout,
                },
            }

            logger.info("System configuration requested")
            return system_config
        except Exception as e:
            logger.error(f"Failed to get system config: {e}")
            return {"error": "Failed to get system configuration"}, 500


@config_ns.route("/algorithms")
class AlgorithmsConfig(Resource):
    @config_ns.doc("get_algorithms_config")
    @config_ns.marshal_with(algorithms_config_model)
    def get(self):
        """获取算法配置

        返回系统支持的算法类型和参数，基于动态发现机制。
        """
        try:
            # 使用动态配置管理器
            from src.config.dynamic_config import get_dynamic_config_manager
            manager = get_dynamic_config_manager()

            algorithms_config = {
                "featureTypes": manager.get_available_feature_types(),
                "ransacTypes": manager.get_available_ransac_types(),
            }

            logger.info(f"Dynamic algorithms configuration requested: {algorithms_config}")
            return algorithms_config
        except Exception as e:
            logger.error(f"Failed to get algorithms config: {e}")
            # 回退到静态配置
            config = get_config()
            return {
                "featureTypes": config.experiment.supported_feature_types,
                "ransacTypes": config.experiment.supported_ransac_types,
            }


@config_ns.route("/algorithms/capabilities")
class AlgorithmsCapabilities(Resource):
    @config_ns.doc("get_algorithms_capabilities")
    def get(self):
        """获取算法详细能力信息

        返回每个算法的详细信息，包括可用性、要求、默认配置等。
        """
        try:
            from src.config.dynamic_config import get_dynamic_config_manager
            manager = get_dynamic_config_manager()

            capabilities = {
                "features": {},
                "ransac": {},
                "chart_config": {
                    "pr_curve": manager.get_chart_config("pr_curve"),
                    "trajectory": manager.get_chart_config("trajectory"),
                    "metrics": manager.get_chart_config("metrics")
                }
            }

            # 获取特征算法能力
            for feature_type in manager.get_available_feature_types():
                cap = manager.get_feature_capability(feature_type)
                if cap:
                    capabilities["features"][feature_type] = {
                        "name": cap.name,
                        "display_name": cap.display_name,
                        "description": cap.description,
                        "is_available": cap.is_available,
                        "requirements": cap.requirements,
                        "supported_matchers": cap.supported_matchers
                    }

            # 获取RANSAC算法能力
            for ransac_type in manager.get_available_ransac_types():
                cap = manager.get_ransac_capability(ransac_type)
                if cap:
                    capabilities["ransac"][ransac_type] = {
                        "name": cap.name,
                        "display_name": cap.display_name,
                        "description": cap.description,
                        "is_available": cap.is_available,
                        "requirements": cap.requirements
                    }

            logger.info("Algorithms capabilities requested")
            return capabilities
        except Exception as e:
            logger.error(f"Failed to get algorithms capabilities: {e}")
            return {"error": "Failed to get algorithms capabilities"}, 500


@config_ns.route("/diagnostics")
class Diagnostics(Resource):
    @config_ns.doc("get_diagnostics")
    def get(self):
        """返回存储诊断信息：RESULTS_ROOT 与可见实验列表"""
        try:
            from src.api.services.experiment import ExperimentService

            cfg = get_config()
            service = ExperimentService()
            # 直接复用 list_experiments 逻辑，获取简化列表
            result = service.list_experiments(page=1, per_page=100)
            if isinstance(result, dict):
                experiments = result.get("experiments", [])
            else:
                experiments = result
            # 最终返回实验ID列表
            exp_list = []
            for exp in experiments:
                if hasattr(exp, "experiment_id"):
                    exp_list.append(exp.experiment_id)
                elif isinstance(exp, dict) and "experiment_id" in exp:
                    exp_list.append(exp["experiment_id"])
            return (
                {
                    "results_root": cfg.storage.results_root,
                    "visible_experiments": exp_list,
                    "count": len(exp_list),
                },
                200,
            )
        except Exception as e:
            logger.error(f"Failed to get diagnostics: {e}")
            return {"error": "Failed to get diagnostics"}, 500


