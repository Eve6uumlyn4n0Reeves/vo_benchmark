"""
统一配置管理系统

提供灵活的配置加载和管理，支持环境变量、配置文件和默认值。
"""

import os
import json
import yaml
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum


class Environment(Enum):
    DEVELOPMENT = "development"
    TESTING = "testing"
    PRODUCTION = "production"


@dataclass
class DatabaseConfig:
    url: str = "sqlite:///vo_benchmark.db"
    pool_size: int = 10
    pool_timeout: int = 30
    echo: bool = False


@dataclass
class RedisConfig:
    url: str = "redis://localhost:6379/0"
    password: Optional[str] = None
    db: int = 0
    decode_responses: bool = True


@dataclass
class CorsConfig:
    origins: List[str] = field(default_factory=lambda: ["*"])
    allow_credentials: bool = True
    allow_methods: List[str] = field(
        default_factory=lambda: ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    )
    allow_headers: List[str] = field(default_factory=lambda: ["*"])


@dataclass
class ExperimentConfig:
    default_num_runs: int = 1
    default_parallel_jobs: int = 4
    default_max_features: int = 5000
    default_ransac_threshold: float = 1.0
    default_ransac_confidence: float = 0.999
    default_ransac_max_iters: int = 2000
    default_ratio_threshold: float = 0.75
    post_filter: dict = field(
        default_factory=lambda: {
            "enabled": True,
            "gms": {"with_rotation": False, "with_scale": False, "threshold_factor": 6},
            "symmetric_mad": {"mad_k": 3.0},
        }
    )
    # 动态算法支持 - 不再硬编码
    supported_feature_types: List[str] = field(default_factory=list)
    supported_ransac_types: List[str] = field(default_factory=list)

    # 算法默认参数（集中管理，可由配置覆盖）
    algorithms_defaults: Dict[str, Any] = field(default_factory=dict)

    # 图表配置参数
    chart_config: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """初始化后动态加载算法支持"""
        if not self.supported_feature_types or not self.supported_ransac_types:
            self._load_dynamic_algorithms()

    def _load_dynamic_algorithms(self):
        """动态加载可用算法"""
        try:
            from .dynamic_config import get_dynamic_config_manager
            manager = get_dynamic_config_manager()

            if not self.supported_feature_types:
                self.supported_feature_types = manager.get_available_feature_types()

            if not self.supported_ransac_types:
                self.supported_ransac_types = manager.get_available_ransac_types()

        except ImportError as e:
            # 回退到默认值
            if not self.supported_feature_types:
                self.supported_feature_types = ["SIFT", "ORB", "AKAZE", "BRISK", "KAZE"]
            if not self.supported_ransac_types:
                self.supported_ransac_types = ["STANDARD", "PROSAC"]


@dataclass
class StorageConfig:
    # 默认使用相对路径，后续由 _normalize_paths 锚定为绝对路径（兼容 Windows）
    datasets_root: str = "./data/datasets"
    results_root: str = "./data/results"
    temp_root: str = "./data/tmp/vo_benchmark"


@dataclass
class LoggingConfig:
    level: str = "INFO"
    format: str = "standard"
    file: Optional[str] = None
    to_stdout: bool = False


@dataclass
class AppConfig:
    environment: Environment = Environment.DEVELOPMENT
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 5000
    secret_key: str = "dev-secret-key"

    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    redis: RedisConfig = field(default_factory=RedisConfig)
    cors: CorsConfig = field(default_factory=CorsConfig)
    experiment: ExperimentConfig = field(default_factory=ExperimentConfig)
    storage: StorageConfig = field(default_factory=StorageConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)


class ConfigManager:
    def __init__(self):
        self._config: Optional[AppConfig] = None
        self._config_file: Optional[Path] = None

    def load_config(self, config_file: Optional[str] = None) -> AppConfig:
        """加载配置

        加载顺序（后者覆盖前者）：
        1) config/default.yaml
        2) config/<env>.yaml  （env 取自 FLASK_ENV，默认 development）
        3) 环境变量
        如传入 config_file 则优先加载该文件后再与环境变量合并。
        """
        if self._config is not None:
            return self._config

        # 1. 从配置文件加载（default.yaml + <env>.yaml）
        file_config: Dict[str, Any] = {}
        try:
            from pathlib import Path as _Path

            current_file = _Path(__file__).resolve()
            # __file__ = backend/src/config/manager.py → backend 目录
            backend_dir = current_file.parents[2]
            config_dir = backend_dir / "config"

            # 默认配置
            default_yaml = config_dir / "default.yaml"
            if default_yaml.exists():
                file_config = self._deep_merge(
                    file_config, self._load_from_file(str(default_yaml))
                )

            # 计算环境并加载对应 YAML
            env_name = os.getenv("FLASK_ENV", "development").lower()
            env_yaml = config_dir / f"{env_name}.yaml"
            if env_yaml.exists():
                file_config = self._deep_merge(
                    file_config, self._load_from_file(str(env_yaml))
                )

            # 若显式传入了配置文件，再次覆盖
            if config_file:
                file_config = self._deep_merge(
                    file_config, self._load_from_file(config_file)
                )
        except Exception as _e:
            # 文件加载失败不应阻塞，回退到仅环境变量
            pass

        # 2. 从环境变量加载
        env_config = self._load_from_env()

        # 3. 合并配置（文件 ← 环境变量 覆盖）
        merged_config = self._merge_configs(file_config, env_config)

        # 4. 创建配置对象（对未知字段进行净化，避免 dataclass 构造报错）
        self._config = self._create_config(merged_config)

        # 4.1 规范化关键路径为绝对路径（仅当为相对路径时）
        self._normalize_paths(self._config)

        # 5. 验证配置
        self._validate_config(self._config)

        return self._config

    def _load_from_file(self, config_file: str) -> Dict[str, Any]:
        """从文件加载配置"""
        config_path = Path(config_file)
        if not config_path.exists():
            return {}

        try:
            with open(config_path, "r", encoding="utf-8") as f:
                if config_path.suffix.lower() == ".json":
                    data_json: Dict[str, Any] = json.load(f)
                    return data_json
                elif config_path.suffix.lower() in [".yml", ".yaml"]:
                    data_yaml = yaml.safe_load(f)
                    return data_yaml if isinstance(data_yaml, dict) else {}
                else:
                    raise ValueError(
                        f"Unsupported config file format: {config_path.suffix}"
                    )
        except Exception as e:
            import logging as _logging
            _logging.getLogger(__name__).warning(
                f"Failed to load config file {config_file}: {e}"
            )
            return {}

    def _load_from_env(self) -> Dict[str, Any]:
        """从环境变量加载配置（仅在环境变量显式提供时才覆盖）。
        之前的实现会用默认值覆盖文件配置，导致如 results_root 总被 '/data/results' 覆盖。
        此处修复为：只有当对应环境变量存在时才写入覆盖项。
        """

        def safe_int(value: str, default: int) -> int:
            try:
                return int(value)
            except (ValueError, TypeError):
                return default

        env: Dict[str, Any] = {}

        # 顶层
        if "FLASK_ENV" in os.environ:
            env["environment"] = os.getenv("FLASK_ENV")
        if "FLASK_DEBUG" in os.environ:
            env["debug"] = os.getenv("FLASK_DEBUG", "false").lower() == "true"
        if "FLASK_HOST" in os.environ:
            env["host"] = os.getenv("FLASK_HOST")
        if "FLASK_PORT" in os.environ:
            env["port"] = safe_int(os.getenv("FLASK_PORT", ""), 5000)
        if "SECRET_KEY" in os.environ:
            env["secret_key"] = os.getenv("SECRET_KEY")

        # 数据库
        db: Dict[str, Any] = {}
        if "DATABASE_URL" in os.environ:
            db["url"] = os.getenv("DATABASE_URL")
        if "DATABASE_POOL_SIZE" in os.environ:
            db["pool_size"] = safe_int(os.getenv("DATABASE_POOL_SIZE", ""), 10)
        if "DATABASE_POOL_TIMEOUT" in os.environ:
            db["pool_timeout"] = safe_int(os.getenv("DATABASE_POOL_TIMEOUT", ""), 30)
        if "DATABASE_ECHO" in os.environ:
            db["echo"] = os.getenv("DATABASE_ECHO", "false").lower() == "true"
        if db:
            env["database"] = db

        # Redis
        rds: Dict[str, Any] = {}
        if "REDIS_URL" in os.environ:
            rds["url"] = os.getenv("REDIS_URL")
        if "REDIS_PASSWORD" in os.environ:
            rds["password"] = os.getenv("REDIS_PASSWORD")
        if "REDIS_DB" in os.environ:
            rds["db"] = safe_int(os.getenv("REDIS_DB", ""), 0)
        if rds:
            env["redis"] = rds

        # CORS
        cors: Dict[str, Any] = {}
        if "CORS_ORIGINS" in os.environ:
            cors["origins"] = [
                origin.strip() for origin in os.getenv("CORS_ORIGINS", "*").split(",")
            ]
        if "CORS_ALLOW_CREDENTIALS" in os.environ:
            cors["allow_credentials"] = (
                os.getenv("CORS_ALLOW_CREDENTIALS", "true").lower() == "true"
            )
        if cors:
            env["cors"] = cors

        # 实验默认
        exp: Dict[str, Any] = {}
        if "DEFAULT_NUM_RUNS" in os.environ:
            exp["default_num_runs"] = safe_int(os.getenv("DEFAULT_NUM_RUNS", ""), 1)
        if "DEFAULT_PARALLEL_JOBS" in os.environ:
            exp["default_parallel_jobs"] = safe_int(
                os.getenv("DEFAULT_PARALLEL_JOBS", ""), 4
            )
        if "DEFAULT_MAX_FEATURES" in os.environ:
            exp["default_max_features"] = safe_int(
                os.getenv("DEFAULT_MAX_FEATURES", ""), 5000
            )
        if "DEFAULT_RANSAC_THRESHOLD" in os.environ:
            exp["default_ransac_threshold"] = self._safe_float(
                os.getenv("DEFAULT_RANSAC_THRESHOLD", ""), 1.0
            )
        if "DEFAULT_RANSAC_CONFIDENCE" in os.environ:
            exp["default_ransac_confidence"] = self._safe_float(
                os.getenv("DEFAULT_RANSAC_CONFIDENCE", ""), 0.999
            )
        if "DEFAULT_RANSAC_MAX_ITERS" in os.environ:
            exp["default_ransac_max_iters"] = safe_int(
                os.getenv("DEFAULT_RANSAC_MAX_ITERS", ""), 2000
            )
        if "DEFAULT_RATIO_THRESHOLD" in os.environ:
            exp["default_ratio_threshold"] = self._safe_float(
                os.getenv("DEFAULT_RATIO_THRESHOLD", ""), 0.75
            )
        if "SUPPORTED_FEATURE_TYPES" in os.environ:
            exp["supported_feature_types"] = os.getenv(
                "SUPPORTED_FEATURE_TYPES", "SIFT,ORB"
            ).split(",")
        if "SUPPORTED_RANSAC_TYPES" in os.environ:
            exp["supported_ransac_types"] = os.getenv(
                "SUPPORTED_RANSAC_TYPES", "STANDARD,PROSAC"
            ).split(",")
        if exp:
            env["experiment"] = exp

        # 存储路径
        storage: Dict[str, Any] = {}
        if "DATASETS_ROOT" in os.environ:
            storage["datasets_root"] = os.getenv("DATASETS_ROOT")
        if "RESULTS_ROOT" in os.environ:
            storage["results_root"] = os.getenv("RESULTS_ROOT")
        if "TEMP_ROOT" in os.environ:
            storage["temp_root"] = os.getenv("TEMP_ROOT")
        if storage:
            env["storage"] = storage

        # 日志
        log: Dict[str, Any] = {}
        if "LOG_LEVEL" in os.environ:
            log["level"] = os.getenv("LOG_LEVEL")
        if "LOG_FORMAT" in os.environ:
            log["format"] = os.getenv("LOG_FORMAT")
        if "LOG_FILE" in os.environ:
            log["file"] = os.getenv("LOG_FILE")
        if "LOG_TO_STDOUT" in os.environ:
            log["to_stdout"] = os.getenv("LOG_TO_STDOUT", "false").lower() == "true"
        if log:
            env["logging"] = log

        return env

    def _safe_float(self, value: str, default: float) -> float:
        """安全地获取浮点类型的环境变量"""
        try:
            return float(value)
        except (ValueError, TypeError):
            return default

    def _merge_configs(self, *configs: Dict[str, Any]) -> Dict[str, Any]:
        """合并多个配置字典"""
        result: Dict[str, Any] = {}
        for config in configs:
            result = self._deep_merge(result, config)
        return result

    def _deep_merge(
        self, base: Dict[str, Any], override: Dict[str, Any]
    ) -> Dict[str, Any]:
        """深度合并字典"""
        result = base.copy()
        for key, value in override.items():
            if (
                key in result
                and isinstance(result[key], dict)
                and isinstance(value, dict)
            ):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        return result

    def _create_config(self, config_dict: Dict[str, Any]) -> AppConfig:
        """从字典创建配置对象"""
        # 仅保留 LoggingConfig 支持的字段，避免 YAML 中出现的额外键（如 requests）导致报错
        logging_raw: Dict[str, Any] = config_dict.get("logging", {}) or {}
        allowed_logging_keys = {"level", "format", "file", "to_stdout"}
        logging_sanitized = {
            k: v for k, v in logging_raw.items() if k in allowed_logging_keys
        }

        return AppConfig(
            environment=Environment(config_dict.get("environment", "development")),
            debug=config_dict.get("debug", False),
            host=config_dict.get("host", "0.0.0.0"),
            port=config_dict.get("port", 5000),
            secret_key=config_dict.get("secret_key", "dev-secret-key"),
            database=DatabaseConfig(**config_dict.get("database", {})),
            redis=RedisConfig(**config_dict.get("redis", {})),
            cors=CorsConfig(**config_dict.get("cors", {})),
            experiment=ExperimentConfig(**config_dict.get("experiment", {})),
            storage=StorageConfig(**config_dict.get("storage", {})),
            logging=LoggingConfig(**logging_sanitized),
        )

    def _normalize_paths(self, config: AppConfig) -> None:
        """将存储等路径规范化为绝对路径（当提供为相对路径时锚定到 backend 目录）。"""
        try:
            # backend/src/config/manager.py → 项目根目录
            project_root = Path(__file__).resolve().parents[3]

            def to_abs(p: str) -> str:
                try:
                    path_obj = Path(p)
                    return str(
                        path_obj
                        if path_obj.is_absolute()
                        else (project_root / path_obj).resolve()
                    )
                except Exception:
                    # 若解析失败，原样返回
                    return p

            # 仅当提供为相对路径时进行锚定
            config.storage.datasets_root = to_abs(config.storage.datasets_root)
            config.storage.results_root = to_abs(config.storage.results_root)
            config.storage.temp_root = to_abs(config.storage.temp_root)
        except Exception:
            # 路径规范化失败不应阻塞应用启动
            pass

    def _validate_config(self, config: AppConfig) -> None:
        """验证配置"""
        errors = []

        # 验证端口
        if not (1 <= config.port <= 65535):
            errors.append(f"Invalid port: {config.port}")

        # 验证存储路径
        for path_name, path_value in [
            ("datasets_root", config.storage.datasets_root),
            ("results_root", config.storage.results_root),
            ("temp_root", config.storage.temp_root),
        ]:
            path = Path(path_value)
            if not path.exists():
                try:
                    path.mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    errors.append(
                        f"Cannot create {path_name} directory {path_value}: {e}"
                    )

        # 验证实验配置
        if config.experiment.default_num_runs < 1:
            errors.append("default_num_runs must be >= 1")

        if config.experiment.default_parallel_jobs < 1:
            errors.append("default_parallel_jobs must be >= 1")

        if not (0 < config.experiment.default_ransac_confidence < 1):
            errors.append("default_ransac_confidence must be between 0 and 1")

        if errors:
            raise ValueError(f"Configuration validation failed: {'; '.join(errors)}")


# 全局配置管理器实例
config_manager = ConfigManager()


def get_config(config_name: Optional[str] = None) -> AppConfig:
    """获取应用配置"""
    return config_manager.load_config()


def get_client_config() -> Dict[str, Any]:
    """获取客户端配置"""
    config = get_config()

    # 运行时过滤不可用算法（例如 SURF 缺少 opencv-contrib 时）
    feature_types = list(config.experiment.supported_feature_types)
    try:
        import cv2
        _ = cv2.xfeatures2d  # type: ignore[attr-defined]
    except Exception:
        if "SURF" in feature_types:
            feature_types.remove("SURF")
    # 运行时过滤不可用的 RANSAC 方法（依赖 OpenCV 版本）
    ransac_types = list(config.experiment.supported_ransac_types)
    try:
        import cv2  # already imported above if feature filter passed
        required = {
            "USAC_DEFAULT": "USAC_DEFAULT",
            "USAC_MAGSAC": "USAC_MAGSAC",
            "USAC_ACCURATE": "USAC_ACCURATE",
            "RHO": "RHO",
            "LMEDS": "LMEDS",
        }
        for name, attr in required.items():
            if name in ransac_types and not hasattr(cv2, attr):
                ransac_types.remove(name)
    except Exception:
        # 如果连 cv2 都不可用，保持原值（但实际运行会失败）；这里不抛出以便文档仍可访问
        pass

    return {
        "experiment": {
            "defaultRuns": config.experiment.default_num_runs,
            "defaultParallelJobs": config.experiment.default_parallel_jobs,
            "defaultMaxFeatures": config.experiment.default_max_features,
            "defaultRansacThreshold": config.experiment.default_ransac_threshold,
            "defaultRansacConfidence": config.experiment.default_ransac_confidence,
            "defaultRansacMaxIters": config.experiment.default_ransac_max_iters,
            "defaultRatioThreshold": config.experiment.default_ratio_threshold,
        },
        "algorithms": {
            "featureTypes": feature_types,
            "ransacTypes": ransac_types,
        },
    }
