"""
配置管理API

提供客户端配置获取和系统配置管理功能。
"""

from flask import Blueprint, jsonify, request
from flask_restx import Namespace, Resource, fields
from src.api.docs import api
from src.config.manager import get_config, get_client_config
import logging

logger = logging.getLogger(__name__)

# 创建Blueprint
bp = Blueprint("config", __name__)

# 创建Flask-RESTX Namespace
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

        返回系统支持的算法类型和参数。
        """
        try:
            config = get_config()

            algorithms_config = {
                "featureTypes": config.experiment.supported_feature_types,
                "ransacTypes": config.experiment.supported_ransac_types,
            }

            logger.info("Algorithms configuration requested")
            return algorithms_config
        except Exception as e:
            logger.error(f"Failed to get algorithms config: {e}")
            return {"error": "Failed to get algorithms configuration"}, 500


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


