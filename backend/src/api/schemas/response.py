#
# 功能: 定义API响应的数据结构。
#
from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from src.models.types import TaskStatus, ErrorCode


class PaginationInfo(BaseModel):
    """分页信息"""

    page: int = Field(..., description="当前页码")
    limit: int = Field(..., description="每页数量")
    total: int = Field(..., description="总记录数")
    total_pages: int = Field(..., description="总页数")
    has_next: bool = Field(..., description="是否有下一页")
    has_previous: bool = Field(..., description="是否有上一页")


class TaskResponse(BaseModel):
    """任务响应"""


    task_id: str = Field(..., description="任务ID")
    status: TaskStatus = Field(..., description="任务状态")
    message: str = Field(..., description="状态消息")
    progress: float = Field(..., ge=0.0, le=1.0, description="进度百分比")
    current_step: Optional[int] = Field(None, description="当前步骤")
    total_steps: Optional[int] = Field(None, description="总步骤数")
    experiment_id: Optional[str] = Field(None, description="关联的实验ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    completed_at: Optional[datetime] = Field(None, description="完成时间")
    error_details: Optional[Dict[str, Any]] = Field(None, description="错误详情")
    estimated_remaining_time: Optional[int] = Field(
        None, description="预计剩余时间(秒)"
    )


class ExperimentConfigResponse(BaseModel):
    """实验配置响应"""

    name: str = Field(..., description="实验名称")
    dataset_path: str = Field(..., description="数据集路径")
    output_dir: str = Field(..., description="输出目录")
    feature_types: List[str] = Field(..., description="特征类型")
    ransac_types: List[str] = Field(..., description="RANSAC类型")
    sequences: List[str] = Field(..., description="序列列表")
    num_runs: int = Field(..., description="运行次数")
    parallel_jobs: int = Field(..., description="并行任务数")
    feature_params: Dict[str, Any] = Field(..., description="特征参数")
    ransac_params: Dict[str, Any] = Field(..., description="RANSAC参数")


class ExperimentSummaryResponse(BaseModel):
    """实验摘要响应"""

    total_runs: int = Field(..., description="总运行数")
    successful_runs: int = Field(..., description="成功运行数")
    failed_runs: int = Field(..., description="失败运行数")
    total_frames: int = Field(0, description="总帧数")
    total_processing_time: float = Field(0.0, description="总处理时间")
    average_fps: float = Field(0.0, description="平均FPS")
    algorithms_tested: List[str] = Field(..., description="测试的算法")
    sequences_processed: List[str] = Field(..., description="处理的序列")
    best_algorithm: Optional[str] = Field(None, description="最佳算法")
    worst_algorithm: Optional[str] = Field(None, description="最差算法")


class ExperimentResponse(BaseModel):
    """实验响应"""

    model_config = ConfigDict(use_enum_values=True)

    experiment_id: str = Field(..., description="实验ID")
    name: str = Field(..., description="实验名称")
    description: Optional[str] = Field(None, description="实验描述")
    status: TaskStatus = Field(..., description="实验状态")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="更新时间")
    completed_at: Optional[datetime] = Field(None, description="完成时间")
    config: ExperimentConfigResponse = Field(..., description="实验配置")
    summary: Optional[ExperimentSummaryResponse] = Field(None, description="实验摘要")
    task_id: Optional[str] = Field(None, description="关联的任务ID")
    output_files: List[str] = Field(default_factory=list, description="输出文件列表")
    algorithms: List[str] = Field(
        default_factory=list, description="此实验可用的完整算法键列表（含序列与运行后缀）"
    )


class TrajectoryMetricsResponse(BaseModel):
    """轨迹指标响应"""

    ate_rmse: float = Field(..., description="绝对轨迹误差RMSE")
    ate_mean: float = Field(..., description="绝对轨迹误差均值")
    ate_median: float = Field(..., description="绝对轨迹误差中位数")
    ate_std: float = Field(..., description="绝对轨迹误差标准差")
    rpe_rmse: float = Field(..., description="相对位姿误差RMSE")
    rpe_mean: float = Field(..., description="相对位姿误差均值")
    trajectory_length: float = Field(..., description="轨迹长度")
    num_valid_poses: int = Field(..., description="有效位姿数")


class MatchingMetricsResponse(BaseModel):
    """匹配指标响应"""

    avg_matches: float = Field(..., description="平均匹配数")
    avg_inliers: float = Field(..., description="平均内点数")
    avg_inlier_ratio: float = Field(..., description="平均内点比例")
    avg_match_score: float = Field(..., description="平均匹配分数")
    avg_reprojection_error: float = Field(..., description="平均重投影误差")


class RANSACMetricsResponse(BaseModel):
    """RANSAC指标响应"""

    avg_iterations: float = Field(..., description="平均迭代次数")
    std_iterations: float = Field(..., description="迭代次数标准差")
    convergence_rate: float = Field(..., description="收敛率")
    success_rate: float = Field(..., description="成功率")
    avg_processing_time_ms: float = Field(..., description="平均处理时间(毫秒)")


class AlgorithmMetricsResponse(BaseModel):
    """算法指标响应"""

    algorithm_key: str = Field(..., description="算法键")
    feature_type: str = Field(..., description="特征类型")
    ransac_type: str = Field(..., description="RANSAC类型")
    trajectory: Optional[TrajectoryMetricsResponse] = Field(
        None, description="轨迹指标"
    )
    matching: MatchingMetricsResponse = Field(..., description="匹配指标")
    ransac: RANSACMetricsResponse = Field(..., description="RANSAC指标")
    avg_frame_time_ms: float = Field(..., description="平均帧处理时间")
    total_time_s: float = Field(..., description="总处理时间")
    fps: float = Field(..., description="处理帧率")
    success_rate: float = Field(..., description="成功率")
    total_frames: int = Field(..., description="总帧数")
    successful_frames: int = Field(..., description="成功帧数")
    failed_frames: int = Field(default=0, description="失败帧数")
    failure_reasons: Dict[str, int] = Field(
        default_factory=dict, description="失败原因计数"
    )


class PRCurveResponse(BaseModel):
    """PR曲线响应"""

    algorithm: str = Field(..., description="算法名称")
    precisions: List[float] = Field(..., description="精确率列表")
    recalls: List[float] = Field(..., description="召回率列表")
    thresholds: List[float] = Field(..., description="阈值列表")
    auc_score: float = Field(..., description="AUC分数")
    optimal_threshold: float = Field(..., description="最优阈值")
    optimal_precision: float = Field(..., description="最优精确率")
    optimal_recall: float = Field(..., description="最优召回率")
    f1_scores: List[float] = Field(..., description="F1分数列表")
    max_f1_score: float = Field(..., description="最大F1分数")


class AlgorithmResultResponse(BaseModel):
    """算法结果响应"""

    algorithm_key: str = Field(..., description="算法键")
    feature_type: str = Field(..., description="特征类型")
    ransac_type: str = Field(..., description="RANSAC类型")
    sequence: str = Field(..., description="序列名称")
    metrics: AlgorithmMetricsResponse = Field(..., description="算法指标")
    pr_curve: Optional[PRCurveResponse] = Field(None, description="PR曲线数据")
    visualization_files: List[str] = Field(
        default_factory=list, description="可视化文件"
    )


class FrameResultResponse(BaseModel):
    """帧结果响应"""

    frame_id: int = Field(..., description="帧ID")
    timestamp: float = Field(..., description="时间戳")
    num_matches: int = Field(..., description="匹配数")
    num_inliers: int = Field(..., description="内点数")
    inlier_ratio: float = Field(..., description="内点比例")
    processing_time: float = Field(..., description="处理时间")
    status: str = Field(..., description="处理状态")
    pose_error: Optional[float] = Field(None, description="位姿误差")
    reprojection_errors: Optional[List[float]] = Field(None, description="重投影误差")


class FrameResultsResponse(BaseModel):
    """帧结果列表响应"""

    experiment_id: str = Field(..., description="实验ID")
    algorithm_key: str = Field(..., description="算法键")
    sequence: str = Field(..., description="序列名称")
    frames: List[FrameResultResponse] = Field(..., description="帧结果列表")
    pagination: PaginationInfo = Field(..., description="分页信息")
    summary: Dict[str, Any] = Field(..., description="摘要统计")


class ComparisonResponse(BaseModel):
    """比较结果响应"""

    experiments: List[str] = Field(..., description="比较的实验ID")
    algorithms: List[str] = Field(..., description="比较的算法")
    metrics: Dict[str, Dict[str, float]] = Field(..., description="比较指标")
    rankings: Dict[str, List[str]] = Field(..., description="排名结果")
    statistical_tests: Optional[Dict[str, Any]] = Field(
        None, description="统计检验结果"
    )


class HealthResponse(BaseModel):
    """健康检查响应"""

    status: str = Field(..., description="服务状态")
    timestamp: datetime = Field(..., description="检查时间")
    version: str = Field(..., description="版本信息")
    uptime: float = Field(..., description="运行时间(秒)")
    system_info: Dict[str, Any] = Field(..., description="系统信息")
    dependencies: Dict[str, str] = Field(..., description="依赖状态")


class ErrorResponse(BaseModel):
    """错误响应"""

    error_code: ErrorCode = Field(..., description="错误代码")
    message: str = Field(..., description="错误消息")
    details: Optional[Dict[str, Any]] = Field(None, description="错误详情")
    timestamp: datetime = Field(..., description="错误时间")
    request_id: Optional[str] = Field(None, description="请求ID")
    suggestions: Optional[List[str]] = Field(None, description="解决建议")


class SuccessResponse(BaseModel):
    """成功响应"""

    success: bool = Field(True, description="操作是否成功")
    message: str = Field(..., description="成功消息")
    data: Optional[Dict[str, Any]] = Field(None, description="返回数据")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="响应时间")


class ListResponse(BaseModel):
    """列表响应基类"""

    items: List[Any] = Field(..., description="数据项列表")
    pagination: PaginationInfo = Field(..., description="分页信息")
    filters: Optional[Dict[str, Any]] = Field(None, description="应用的过滤器")
    sort: Optional[Dict[str, str]] = Field(None, description="排序信息")
