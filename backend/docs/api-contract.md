# VO-Benchmark 后端接口契约文档

本文件定义后端 API 的请求/响应契约与错误语义，前端可据此适配。所有接口均遵循以下通用约定：
- 统一前缀：/api/v1
- 认证：当前无鉴权；后续如启用请在 Header 加 Authorization: Bearer <token>
- Content-Type: application/json，除导出接口外
- 时间戳：ISO 8601（UTC），示例 2025-01-01T12:00:00Z
- 错误返回：{ error: string } 或 { error_code, message, details? }（详见各路由）
- 文档页面：Swagger UI at /api/v1/docs/

## 健康检查 Health（documented）
- 基础存活检查 GET /api/v1/health-doc/
  - 200 OK
    - { status: "healthy", timestamp: string, version: string, uptime: number }
  - 503 Service Unavailable
    - { message: string }
- 详细健康检查 GET /api/v1/health-doc/detailed
  - 200/503
    - { status: "healthy|degraded|unhealthy", timestamp, version, uptime, system_metrics, dependencies, active_experiments, total_experiments, queue_size }
- 就绪检查 GET /api/v1/health-doc/ready
  - 200 OK
    - { ready: boolean, timestamp: string, checks: Array<{ name, status: "pass|fail", message? }> }

## 配置 Config（documented + legacy）
- 获取客户端配置 GET /api/v1/config/client
  - 200 OK
    - { experiment: { defaultRuns, defaultParallelJobs, defaultMaxFeatures, defaultRansacThreshold, defaultRansacConfidence, defaultRansacMaxIters, defaultRatioThreshold }, algorithms: { featureTypes: string[], ransacTypes: string[] } }
- 获取系统配置 GET /api/v1/config/system
  - 200 OK
    - 非敏感配置摘要
- 获取算法配置 GET /api/v1/config/algorithms
  - 200 OK
    - { featureTypes: string[], ransacTypes: string[] }
- 诊断（结果根与可见实验）GET /api/v1/config/diagnostics
  - 200 OK
    - { results_root: string, visible_experiments: string[], count: number }
- Legacy（兼容旧前端）
  - GET /config/config, /config/config/system, /config/config/health

## 实验 Experiments（documented）
- 列表 GET /api/v1/experiments-doc/
  - Query: page(>=1), per_page(1-100), status in [CREATED,RUNNING,COMPLETED,FAILED,CANCELLED], sort_by in [created_at,name,status], sort_order in [asc,desc]
  - 200 OK
    - { experiments: Experiment[], pagination }
  - 400 参数错误 | 500 内部错误
- 创建 POST /api/v1/experiments-doc/
  - Body CreateExperimentRequest
    - name: string(1-100, 禁止 \ / : * ? " < > |)
    - dataset_path: string(必须存在)
    - output_dir?: string(可选，未给将自动生成)
    - feature_types: string[]（SIFT, ORB）
    - ransac_types: string[]（STANDARD, PROSAC）
    - sequences: string[]
    - num_runs: int(1-10)，parallel_jobs: int(1-16)
    - random_seed: int>=0
    - save_frame_data: bool, save_descriptors: bool
    - compute_pr_curves: bool, analyze_ransac: bool
    - ransac_success_threshold: float 0-1
    - max_features: int 100-20000
    - feature_params: dict
    - ransac_threshold: float >0 <=10
    - ransac_confidence: float (0,1)
    - ransac_max_iters: int 100-10000
  - 201 Created
    - { task: TaskResponse, experiment: Experiment }
  - 400 验证错误（含字段 details 列表）| 409 名称冲突 | 500 错误
- 详情 GET /api/v1/experiments-doc/{experiment_id}
  - 200 OK Experiment
  - 404 Not Found
- 取消 DELETE /api/v1/experiments-doc/{experiment_id}
  - 405 当前不支持（保留语义位）

Experiment（响应模型摘要）
- experiment_id, name, description?, status, created_at, updated_at, completed_at?,
- config: { name, dataset_path, output_dir, feature_types[], ransac_types[], sequences[], num_runs, parallel_jobs, feature_params, ransac_params }
- summary?: { total_runs, successful_runs, failed_runs, total_frames, total_processing_time, average_fps, algorithms_tested[], sequences_processed[], best_algorithm?, worst_algorithm? }
- task_id?: string, output_files: string[], algorithms: string[]

TaskResponse
- task_id, status, message, progress, current_step?, total_steps?, experiment_id?, created_at, updated_at, completed_at?, error_details?, estimated_remaining_time?

Pagination
- page, limit, total, total_pages, has_next, has_previous

## 结果 Results
- 概览 GET /api/v1/results/{experiment_id}/overview
  - 200 OK: 概览统计（首屏）| 4xx/5xx 错误模型
- 诊断 GET /api/v1/results/{experiment_id}/diagnose
  - 200 OK: 存储/路径诊断结果 | 4xx/5xx 错误模型
- 算法结果 GET /api/v1/results/{experiment_id}/{algorithm_key}
  - 200 OK AlgorithmResultResponse
- 帧结果 GET /api/v1/results/{experiment_id}/{algorithm_key}/frames
  - 分页：page>=1, per_page in [1,1000]
  - 200 OK FrameResultsResponse
- PR曲线 GET /api/v1/results/{experiment_id}/{algorithm_key}/pr-curve
  - 200 OK PRCurveResponse
- 轨迹 GET /api/v1/results/{experiment_id}/{algorithm_key}/trajectory?include_reference=true|false
  - 200 OK: { poses: [...], gt?: [...], ref?: [...] }
- 导出 GET /api/v1/results/{experiment_id}/export?format=json|csv|xlsx|pdf
  - 200 OK: 文件下载；Content-Type 依格式不同
- 预览输出路径 POST /api/v1/experiments-doc/preview-output-path
  - 200 OK: { experiment_id, output_path, dataset_name, directory_structure }
- 历史 GET /api/v1/experiments-doc/{experiment_id}/history
  - 200 OK: Experiment[]


AlgorithmResultResponse（摘要）
- algorithm_key, feature_type, ransac_type, sequence
- metrics: AlgorithmMetricsResponse
- pr_curve?: PRCurveResponse
- visualization_files: string[]

AlgorithmMetricsResponse
- trajectory?: TrajectoryMetricsResponse
- matching: { avg_matches, avg_inliers, avg_inlier_ratio, avg_match_score, avg_reprojection_error }
- ransac: { avg_iterations, std_iterations, convergence_rate, success_rate, avg_processing_time_ms }
- avg_frame_time_ms, total_time_s, fps, success_rate, total_frames, successful_frames, failed_frames, failure_reasons{}

PRCurveResponse
- algorithm, precisions[], recalls[], thresholds[], auc_score, optimal_threshold, optimal_precision, optimal_recall, f1_scores[], max_f1_score

FrameResultsResponse
- experiment_id, algorithm_key, sequence, frames: FrameResultResponse[], pagination, summary
- FrameResultResponse: frame_id, timestamp, num_matches, num_inliers, inlier_ratio, processing_time, status, pose_error?, reprojection_errors?

错误语义
- 业务错误：返回 e.to_dict()，含 error_code、message、details?，并用 e.status_code
- 通用错误：返回 { error: "内部服务器错误" }，HTTP 500

## 任务 Tasks
- 列表 GET /api/v1/tasks/?status=CREATED|RUNNING|COMPLETED|FAILED|CANCELLED
  - 200 OK: TaskResponse[]
- 详情 GET /api/v1/tasks/{task_id}
  - 200 OK: TaskResponse
  - 404 Not Found: { error }
- 取消 POST /api/v1/tasks/{task_id}/cancel
  - 200 OK: { success: boolean }
- 日志 GET /api/v1/tasks/{task_id}/logs
  - 200 OK: { logs: string[] }
  - 404 Not Found: { error }
- 添加日志 POST /api/v1/tasks/{task_id}/logs
  - Body: { log_line: string }
  - 200 OK: { success: boolean }
  - 404 Not Found: { error }

## 事件 Events（SSE）
- GET /api/v1/events/
  - 200 text/event-stream，推送任务/实验状态变化
  - 事件类型：
    - task_updated: { task_id, status, progress, message, experiment_id }
    - task_log: { task_id, line, timestamp }

## 错误模型与状态码规范
- 4xx：参数/请求错误，返回错误模型或 { error }
- 5xx：内部错误，返回 { error: "内部服务器错误" }
- 特定业务错误（如找不到实验）：使用自定义 ErrorCode 与 message

## 版本与兼容
- 当前 API_VERSION: 1.0.0
- 向后兼容：保留 Legacy /config/* 路径
- 废弃计划：未来移除 legacy 后保持 /api/v1/config/* 的单一路径

