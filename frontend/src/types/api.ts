/**
 * TypeScript types strictly aligned with backend/docs/api-contract.md
 * All types are derived from the API contract and must not contain any frontend-specific additions
 */

// =============================================================================
// COMMON TYPES
// =============================================================================

export type ExperimentStatus = 'CREATED' | 'RUNNING' | 'COMPLETED' | 'FAILED' | 'CANCELLED'; // backend uses TaskStatus for ExperimentResponse.status but values are lowercase for tasks only
export type TaskStatus = 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
export type HealthStatus = 'healthy' | 'degraded' | 'unhealthy';
export type CheckStatus = 'pass' | 'fail';
export type SortOrder = 'asc' | 'desc';
export type ExperimentSortBy = 'created_at' | 'name' | 'status';
export type FeatureType = 'SIFT' | 'ORB';
export type RansacType = 'STANDARD' | 'PROSAC';
export type ExportFormat = 'json' | 'csv' | 'xlsx' | 'pdf';

// =============================================================================
// ERROR MODELS
// =============================================================================

export interface ApiError {
  error?: string;
  error_code?: string;
  message?: string;
  details?: Record<string, unknown>;
  request_id?: string;
}

// =============================================================================
// PAGINATION
// =============================================================================

export interface Pagination {
  page: number;
  limit: number;
  total: number;
  total_pages: number;
  has_next: boolean;
  has_previous: boolean;
}

// =============================================================================
// HEALTH ENDPOINTS
// =============================================================================

export interface HealthResponse {
  status: HealthStatus;
  timestamp: string;
  version: string;
  uptime: number;
}

export interface HealthDetailedResponse extends HealthResponse {
  system_metrics: Record<string, unknown>;
  // Allow both record and array shapes for dependencies
  dependencies: Record<string, unknown> | Array<{
    name: string;
    status: string;
    version?: string;
    response_time_ms?: number;
    error_message?: string | null;
  }>;
  active_experiments: number;
  total_experiments: number;
  queue_size: number;
}

export interface HealthCheck {
  name: string;
  status: CheckStatus;
  message?: string;
}

export interface HealthReadyResponse {
  ready: boolean;
  timestamp: string;
  checks: HealthCheck[];
}

// =============================================================================
// CONFIG ENDPOINTS
// =============================================================================

export interface ExperimentDefaults {
  defaultRuns: number;
  defaultParallelJobs: number;
  defaultMaxFeatures: number;
  defaultRansacThreshold: number;
  defaultRansacConfidence: number;
  defaultRansacMaxIters: number;
  defaultRatioThreshold: number;
}

export interface AlgorithmConfig {
  featureTypes: string[];
  ransacTypes: string[];
}

export interface ClientConfig {
  experiment: ExperimentDefaults;
  algorithms: AlgorithmConfig;
}

export interface DiagnosticsConfig {
  results_root: string;
  visible_experiments: string[];
  count: number;
}

// =============================================================================
// EXPERIMENT TYPES
// =============================================================================

export interface ExperimentConfig {
  name: string;
  dataset_path: string;
  output_dir: string;
  feature_types: string[];
  ransac_types: string[];
  sequences: string[];
  num_runs: number;
  parallel_jobs: number;
  feature_params: Record<string, unknown>;
  ransac_params: Record<string, unknown>;
}

export interface ExperimentSummary {
  total_runs: number;
  successful_runs: number;
  failed_runs: number;
  total_frames: number;
  total_processing_time: number;
  average_fps: number;
  algorithms_tested: string[];
  sequences_processed: string[];
  best_algorithm?: string;
  worst_algorithm?: string;
}

export interface Experiment {
  experiment_id: string;
  name: string;
  description?: string | null;
  status: ExperimentStatus;
  created_at: string;
  updated_at: string;
  completed_at?: string;
  config: ExperimentConfig;
  summary?: ExperimentSummary;
  task_id?: string;
  output_files: string[];
  algorithms: string[];
}

export interface CreateExperimentRequest {
  name: string;
  dataset_path: string;
  output_dir?: string;
  feature_types: string[];
  ransac_types: string[];
  sequences: string[];
  num_runs: number;
  parallel_jobs: number;
  random_seed: number;
  save_frame_data: boolean;
  save_descriptors: boolean;
  compute_pr_curves: boolean;
  analyze_ransac: boolean;
  ransac_success_threshold: number;
  max_features: number;
  feature_params: Record<string, unknown>;
  ransac_threshold: number;
  ransac_confidence: number;
  ransac_max_iters: number;
}

export interface ExperimentsListResponse {
  experiments: Experiment[];
  pagination: Pagination;
}

// =============================================================================
// TASK TYPES
// =============================================================================

export interface Task {
  task_id: string;
  status: TaskStatus;
  message: string;
  progress: number;
  current_step?: number | string;
  total_steps?: number;
  experiment_id?: string;
  created_at: string;
  updated_at: string;
  completed_at?: string;
  error_details?: Record<string, unknown>;
  estimated_remaining_time?: number;
}

export interface CreateExperimentResponse {
  task: Task;
  experiment: Experiment;
}

export interface TaskCancelResponse {
  success: boolean;
}

// =============================================================================
// RESULTS TYPES
// =============================================================================

export interface TrajectoryMetricsResponse {
  // Trajectory metrics details - to be defined based on actual implementation
  [key: string]: unknown;
}

export interface MatchingMetrics {
  avg_matches: number;
  avg_inliers: number;
  avg_inlier_ratio: number;
  avg_match_score: number;
  avg_reprojection_error: number;
}

export interface RansacMetrics {
  avg_iterations: number;
  std_iterations: number;
  min_iterations: number;
  max_iterations: number;
  convergence_rate: number;
  avg_inlier_ratio: number;
  success_rate: number;
  avg_processing_time_ms: number;
}

export interface AlgorithmMetricsResponse {
  trajectory?: TrajectoryMetricsResponse;
  matching: MatchingMetrics;
  ransac: RansacMetrics;
  avg_frame_time_ms: number;
  total_time_s: number;
  fps: number;
  success_rate: number;
  metrics_schema_version?: string;
  source_flags?: { match_scores?: 'present'|'absent'; reprojection?: 'present'|'absent' };

  total_frames: number;
  successful_frames: number;
  failed_frames: number;
  failure_reasons: Record<string, number>;
}

export interface PRCurveResponse {
  algorithm: string;
  precisions: number[];
  recalls: number[];
  thresholds: number[];
  auc_score: number;
  optimal_threshold: number;
  optimal_precision: number;
  optimal_recall: number;
  f1_scores: number[];
  max_f1_score: number;
}

export interface PRCurveComputingResponse {
  status: 'computing';
  message: string;
  algorithm: string;
}

export type PRCurveApiResponse = PRCurveResponse | PRCurveComputingResponse;

export interface AlgorithmResultResponse {
  algorithm_key: string;
  feature_type: string;
  ransac_type: string;
  sequence: string;
  metrics: AlgorithmMetricsResponse;
  pr_curve?: PRCurveResponse;
  visualization_files: string[];
}

export interface FrameResultResponse {
  frame_id: string;
  timestamp: string;
  num_matches: number;
  num_inliers: number;
  inlier_ratio: number;
  processing_time: number;
  status: string;
  pose_error?: number;
  reprojection_errors?: number[];
}

export interface FrameResultsResponse {
  experiment_id: string;
  algorithm_key: string;
  sequence: string;
  frames: FrameResultResponse[];
  pagination: Pagination;
  summary: Record<string, unknown>;
}

export interface TrajectoryResponse {
  poses: Array<Record<string, unknown>>;
  gt?: Array<Record<string, unknown>>;
  ref?: Array<Record<string, unknown>>;
}

export interface TrajectoryComputingResponse {
  status: 'computing';
  message: string;
  algorithm: string;
}

export type TrajectoryApiResponse = TrajectoryResponse | TrajectoryComputingResponse;

// =============================================================================
// QUERY PARAMETERS
// =============================================================================

export interface ExperimentsListParams {
  q?: string;
  page?: number;
  per_page?: number;
  status?: ExperimentStatus;
  sort_by?: ExperimentSortBy;
  sort_order?: SortOrder;
}

export interface FrameResultsParams {
  page?: number;
  per_page?: number;
}

export interface TrajectoryParams {
  include_reference?: boolean;
}

export interface ExportParams {
  format: ExportFormat;
}

export interface TasksListParams {
  q?: string;
  status?: TaskStatus;
  task_type?: string;
  sort_by?: 'created_at' | 'status' | 'task_type';
  sort_order?: SortOrder;
  page?: number;
  per_page?: number;
}
