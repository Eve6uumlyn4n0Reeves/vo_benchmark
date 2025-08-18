#
# 功能: 定义API请求的数据结构和验证规则。
#
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, field_validator, model_validator
from pathlib import Path
import os


class CreateExperimentRequest(BaseModel):
    """创建实验的请求模型"""

    name: str = Field(..., min_length=1, max_length=100, description="实验名称")
    dataset_path: str = Field(..., description="数据集路径")
    # 改为可选：由服务在创建时自动生成
    output_dir: Optional[str] = Field(
        None, description="输出目录（可选，未提供时自动生成）"
    )
    feature_types: List[str] = Field(..., min_length=1, description="特征类型列表")
    ransac_types: List[str] = Field(..., min_length=1, description="RANSAC类型列表")
    sequences: List[str] = Field(..., min_length=1, description="序列列表")
    num_runs: int = Field(1, ge=1, le=10, description="运行次数")
    parallel_jobs: int = Field(4, ge=1, le=16, description="并行任务数")
    random_seed: int = Field(42, ge=0, description="随机种子")
    save_frame_data: bool = Field(True, description="是否保存帧数据")
    save_descriptors: bool = Field(False, description="是否保存描述子")
    compute_pr_curves: bool = Field(True, description="是否计算PR曲线")
    analyze_ransac: bool = Field(True, description="是否分析RANSAC")
    ransac_success_threshold: float = Field(
        0.1, ge=0.0, le=1.0, description="RANSAC成功阈值"
    )
    max_features: int = Field(5000, ge=100, le=20000, description="最大特征数")
    feature_params: Dict[str, Any] = Field(default_factory=dict, description="特征参数")
    ransac_threshold: float = Field(1.0, gt=0.0, le=10.0, description="RANSAC阈值")
    ransac_confidence: float = Field(0.999, gt=0.0, lt=1.0, description="RANSAC置信度")
    ransac_max_iters: int = Field(
        2000, ge=100, le=10000, description="RANSAC最大迭代次数"
    )

    @field_validator("feature_types")
    def validate_feature_types(cls, v):
        """验证特征类型"""
        valid_types = ["SIFT", "ORB"]
        for feature_type in v:
            if feature_type not in valid_types:
                raise ValueError(
                    f"不支持的特征类型: {feature_type}. 支持的类型: {valid_types}"
                )
        return v

    @field_validator("ransac_types")
    def validate_ransac_types(cls, v):
        """验证RANSAC类型"""
        valid_types = ["STANDARD", "PROSAC"]
        for ransac_type in v:
            if ransac_type not in valid_types:
                raise ValueError(
                    f"不支持的RANSAC类型: {ransac_type}. 支持的类型: {valid_types}"
                )
        return v

    @field_validator("dataset_path")
    def validate_dataset_path(cls, v):
        """验证数据集路径"""
        try:
            path = Path(v).resolve()
            if not path.exists():
                raise ValueError(f"数据集路径不存在: {v}")
            if not path.is_dir():
                raise ValueError(f"数据集路径必须是目录: {v}")
        except Exception as e:
            raise ValueError(f"数据集路径无效: {v} ({e})")
        return v

    @field_validator("name")
    def validate_name(cls, v):
        """验证实验名称"""
        # 检查名称是否包含非法字符
        invalid_chars = ["/", "\\", ":", "*", "?", '"', "<", ">", "|"]
        for char in invalid_chars:
            if char in v:
                raise ValueError(f"实验名称不能包含字符: {char}")
        return v.strip()


class UpdateExperimentRequest(BaseModel):
    """更新实验的请求模型"""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)

    @field_validator("name")
    def validate_name(cls, v):
        if v is not None:
            invalid_chars = ["/", "\\", ":", "*", "?", '"', "<", ">", "|"]
            for char in invalid_chars:
                if char in v:
                    raise ValueError(f"实验名称不能包含字符: {char}")
            return v.strip()
        return v


class ListExperimentsRequest(BaseModel):
    """列出实验的请求模型"""

    page: int = Field(1, ge=1, description="页码")
    limit: int = Field(20, ge=1, le=100, description="每页数量")
    sort_by: str = Field("created_at", description="排序字段")
    sort_order: str = Field("desc", description="排序顺序")
    status_filter: Optional[str] = Field(None, description="状态过滤")
    name_filter: Optional[str] = Field(None, description="名称过滤")

    @field_validator("sort_by")
    def validate_sort_by(cls, v):
        valid_fields = ["created_at", "updated_at", "name", "status"]
        if v not in valid_fields:
            raise ValueError(f"无效的排序字段: {v}. 支持的字段: {valid_fields}")
        return v

    @field_validator("sort_order")
    def validate_sort_order(cls, v):
        if v.lower() not in ["asc", "desc"]:
            raise ValueError('排序顺序必须是 "asc" 或 "desc"')
        return v.lower()


class CancelTaskRequest(BaseModel):
    """取消任务的请求模型"""

    reason: Optional[str] = Field(None, max_length=200, description="取消原因")


class RetryTaskRequest(BaseModel):
    """重试任务的请求模型"""

    reset_progress: bool = Field(False, description="是否重置进度")


class GetResultsRequest(BaseModel):
    """获取结果的请求模型"""

    experiment_id: str = Field(..., description="实验ID")
    algorithm_filter: Optional[str] = Field(None, description="算法过滤")
    sequence_filter: Optional[str] = Field(None, description="序列过滤")
    metric_type: Optional[str] = Field(None, description="指标类型")
    include_frame_data: bool = Field(False, description="是否包含帧数据")

    @field_validator("metric_type")
    def validate_metric_type(cls, v):
        if v is not None:
            valid_types = ["trajectory", "matching", "ransac", "all"]
            if v not in valid_types:
                raise ValueError(f"无效的指标类型: {v}. 支持的类型: {valid_types}")
        return v


class CompareResultsRequest(BaseModel):
    """比较结果的请求模型"""

    experiment_ids: List[str] = Field(
        ..., min_length=2, max_length=5, description="实验ID列表"
    )
    algorithms: Optional[List[str]] = Field(None, description="算法列表")
    sequences: Optional[List[str]] = Field(None, description="序列列表")
    metrics: List[str] = Field(..., min_length=1, description="比较指标")

    @field_validator("metrics")
    def validate_metrics(cls, v):
        valid_metrics = [
            "ate_rmse",
            "ate_mean",
            "rpe_rmse",
            "rpe_mean",
            "avg_matches",
            "avg_inliers",
            "avg_inlier_ratio",
            "success_rate",
            "avg_processing_time",
        ]
        for metric in v:
            if metric not in valid_metrics:
                raise ValueError(f"无效的指标: {metric}. 支持的指标: {valid_metrics}")
        return v


class ExportResultsRequest(BaseModel):
    """导出结果的请求模型"""

    experiment_id: str = Field(..., description="实验ID")
    format: str = Field("json", description="导出格式")
    include_raw_data: bool = Field(False, description="是否包含原始数据")
    include_visualizations: bool = Field(True, description="是否包含可视化")

    @field_validator("format")
    def validate_format(cls, v):
        valid_formats = ["json", "csv", "xlsx", "pdf"]
        if v not in valid_formats:
            raise ValueError(f"不支持的导出格式: {v}. 支持的格式: {valid_formats}")
        return v
