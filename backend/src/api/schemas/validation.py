#
# 功能: 定义API请求数据的验证规则和自定义验证器。
#
from typing import List, Dict, Any, Optional
from pathlib import Path
from pydantic import field_validator, BaseModel
from src.models.types import FeatureType, RANSACType


class ValidationMixin:
    """验证混入类，提供通用验证方法"""

    @field_validator("dataset_path")
    def validate_dataset_path(cls, v):
        """验证数据集路径"""
        if not v or not v.strip():
            raise ValueError("数据集路径不能为空")

        path = Path(v)
        if not path.exists():
            raise ValueError(f"数据集路径不存在: {v}")

        if not path.is_dir():
            raise ValueError(f"数据集路径必须是目录: {v}")

        return v

    @field_validator("output_dir")
    def validate_output_dir(cls, v):
        """验证输出目录路径"""
        if not v or not v.strip():
            raise ValueError("输出目录不能为空")

        # 尝试创建目录（如果不存在）
        path = Path(v)
        try:
            path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise ValueError(f"无法创建输出目录: {v}, 错误: {str(e)}")

        return v

    @field_validator("feature_types")
    def validate_feature_types(cls, v):
        """验证特征类型列表"""
        if not v or len(v) == 0:
            raise ValueError("至少选择一种特征类型")

        valid_types = [t.value for t in FeatureType]
        for feature_type in v:
            if feature_type not in valid_types:
                raise ValueError(
                    f"不支持的特征类型: {feature_type}，支持的类型: {valid_types}"
                )

        return v

    @field_validator("ransac_types")
    def validate_ransac_types(cls, v):
        """验证RANSAC类型列表"""
        if not v or len(v) == 0:
            raise ValueError("至少选择一种RANSAC类型")

        valid_types = [t.value for t in RANSACType]
        for ransac_type in v:
            if ransac_type not in valid_types:
                raise ValueError(
                    f"不支持的RANSAC类型: {ransac_type}，支持的类型: {valid_types}"
                )

        return v

    @field_validator("sequences")
    def validate_sequences(cls, v):
        """验证序列列表"""
        if not v or len(v) == 0:
            raise ValueError("至少选择一个序列")

        for sequence in v:
            if not sequence or not sequence.strip():
                raise ValueError("序列名称不能为空")

        return v

    @field_validator("num_runs")
    def validate_num_runs(cls, v):
        """验证运行次数"""
        if v < 1:
            raise ValueError("运行次数必须至少为1")
        if v > 100:
            raise ValueError("运行次数不能超过100")
        return v

    @field_validator("parallel_jobs")
    def validate_parallel_jobs(cls, v):
        """验证并行任务数"""
        if v < 1:
            raise ValueError("并行任务数必须至少为1")
        if v > 32:
            raise ValueError("并行任务数不能超过32")
        return v

    @field_validator("ransac_success_threshold")
    def validate_ransac_success_threshold(cls, v):
        """验证RANSAC成功阈值"""
        if v < 0.0 or v > 1.0:
            raise ValueError("RANSAC成功阈值必须在0.0-1.0之间")
        return v

    @field_validator("max_features")
    def validate_max_features(cls, v):
        """验证最大特征数"""
        if v < 100:
            raise ValueError("最大特征数不能少于100")
        if v > 50000:
            raise ValueError("最大特征数不能超过50000")
        return v

    @field_validator("ransac_threshold")
    def validate_ransac_threshold(cls, v):
        """验证RANSAC阈值"""
        if v <= 0.0:
            raise ValueError("RANSAC阈值必须大于0")
        if v > 10.0:
            raise ValueError("RANSAC阈值不应超过10像素")
        return v

    @field_validator("ransac_confidence")
    def validate_ransac_confidence(cls, v):
        """验证RANSAC置信度"""
        if v < 0.5 or v > 1.0:
            raise ValueError("RANSAC置信度必须在0.5-1.0之间")
        return v

    @field_validator("ransac_max_iters")
    def validate_ransac_max_iters(cls, v):
        """验证RANSAC最大迭代次数"""
        if v < 100:
            raise ValueError("RANSAC最大迭代次数不能少于100")
        if v > 10000:
            raise ValueError("RANSAC最大迭代次数不能超过10000")
        return v


def validate_experiment_name(name: str) -> str:
    """验证实验名称"""
    if not name or not name.strip():
        raise ValueError("实验名称不能为空")

    # 检查名称长度
    if len(name.strip()) < 3:
        raise ValueError("实验名称至少需要3个字符")

    if len(name.strip()) > 100:
        raise ValueError("实验名称不能超过100个字符")

    # 检查非法字符
    invalid_chars = ["<", ">", ":", '"', "|", "?", "*", "/", "\\"]
    for char in invalid_chars:
        if char in name:
            raise ValueError(f"实验名称不能包含字符: {char}")

    return name.strip()


def validate_feature_params(
    feature_type: str, params: Dict[str, Any]
) -> Dict[str, Any]:
    """验证特征参数"""
    if feature_type == FeatureType.SIFT.value:
        return validate_sift_params(params)
    elif feature_type == FeatureType.ORB.value:
        return validate_orb_params(params)
    else:
        raise ValueError(f"不支持的特征类型: {feature_type}")


def validate_sift_params(params: Dict[str, Any]) -> Dict[str, Any]:
    """验证SIFT参数"""
    valid_params = {}

    if "nfeatures" in params:
        nfeatures = params["nfeatures"]
        if not isinstance(nfeatures, int) or nfeatures < 0:
            raise ValueError("SIFT nfeatures必须是非负整数")
        valid_params["nfeatures"] = nfeatures

    if "contrastThreshold" in params:
        threshold = params["contrastThreshold"]
        if not isinstance(threshold, (int, float)) or threshold <= 0:
            raise ValueError("SIFT contrastThreshold必须是正数")
        valid_params["contrastThreshold"] = float(threshold)

    if "edgeThreshold" in params:
        threshold = params["edgeThreshold"]
        if not isinstance(threshold, (int, float)) or threshold <= 0:
            raise ValueError("SIFT edgeThreshold必须是正数")
        valid_params["edgeThreshold"] = float(threshold)

    return valid_params


def validate_orb_params(params: Dict[str, Any]) -> Dict[str, Any]:
    """验证ORB参数"""
    valid_params = {}

    if "nfeatures" in params:
        nfeatures = params["nfeatures"]
        if not isinstance(nfeatures, int) or nfeatures <= 0:
            raise ValueError("ORB nfeatures必须是正整数")
        valid_params["nfeatures"] = nfeatures

    if "scaleFactor" in params:
        scale = params["scaleFactor"]
        if not isinstance(scale, (int, float)) or scale <= 1.0:
            raise ValueError("ORB scaleFactor必须大于1.0")
        valid_params["scaleFactor"] = float(scale)

    if "nlevels" in params:
        levels = params["nlevels"]
        if not isinstance(levels, int) or levels <= 0:
            raise ValueError("ORB nlevels必须是正整数")
        valid_params["nlevels"] = levels

    return valid_params


def validate_sequence_exists(dataset_path: str, sequence: str) -> bool:
    """验证序列是否存在于数据集中"""
    try:
        dataset_dir = Path(dataset_path)
        sequence_dir = dataset_dir / sequence

        # 检查序列目录是否存在
        if not sequence_dir.exists() or not sequence_dir.is_dir():
            return False

        # 检查是否包含图像文件
        image_extensions = [".png", ".jpg", ".jpeg", ".bmp", ".tiff"]
        has_images = any(
            file.suffix.lower() in image_extensions
            for file in sequence_dir.iterdir()
            if file.is_file()
        )

        return has_images
    except Exception:
        return False


def validate_config_consistency(config: Dict[str, Any]) -> List[str]:
    """验证配置的一致性"""
    warnings = []

    # 检查特征数量与RANSAC参数的一致性
    max_features = config.get("max_features", 5000)
    ransac_threshold = config.get("ransac_threshold", 1.0)

    if max_features < 1000 and ransac_threshold < 0.5:
        warnings.append("特征数量较少且RANSAC阈值较小，可能导致匹配困难")

    # 检查并行任务数与序列数的关系
    parallel_jobs = config.get("parallel_jobs", 4)
    sequences = config.get("sequences", [])

    if parallel_jobs > len(sequences):
        warnings.append(
            f"并行任务数({parallel_jobs})超过序列数({len(sequences)})，建议调整"
        )

    return warnings
