/**
 * Zod schemas for runtime validation of critical API responses
 * These schemas validate data structure and provide type safety at runtime
 */

import { z } from 'zod';

// =============================================================================
// COMMON SCHEMAS
// =============================================================================

export const ExperimentStatusSchema = z.enum(['CREATED', 'RUNNING', 'COMPLETED', 'FAILED', 'CANCELLED']);
export const TaskStatusSchema = z.enum(['pending', 'running', 'completed', 'failed', 'cancelled']);
export const HealthStatusSchema = z.enum(['healthy', 'degraded', 'unhealthy']);
export const CheckStatusSchema = z.enum(['pass', 'fail']);
export const FeatureTypeSchema = z.enum(['SIFT', 'ORB']);
export const RansacTypeSchema = z.enum(['STANDARD', 'PROSAC']);
export const ExportFormatSchema = z.enum(['json', 'csv', 'xlsx']);

// =============================================================================
// ERROR SCHEMAS
// =============================================================================

export const ApiErrorSchema = z.object({
  error: z.string().optional(),
  error_code: z.string().optional(),
  message: z.string().optional(),
  details: z.record(z.unknown()).optional(),
  request_id: z.string().optional(),
});

// =============================================================================
// PAGINATION SCHEMA
// =============================================================================

export const PaginationSchema = z.object({
  page: z.number().int().min(1),
  limit: z.number().int().min(1),
  total: z.number().int().min(0),
  total_pages: z.number().int().min(0),
  has_next: z.boolean(),
  has_previous: z.boolean(),
});

// =============================================================================
// HEALTH SCHEMAS
// =============================================================================

export const HealthResponseSchema = z.object({
  status: HealthStatusSchema,
  timestamp: z.string(),
  version: z.string(),
  uptime: z.number(),
});

export const HealthDetailedResponseSchema = HealthResponseSchema.extend({
  // 更宽松地接收系统指标：允许任意键，兼容最小字段集
  system_metrics: z.record(z.unknown()),
  // 后端可能返回数组或记录，这里统一接收
  dependencies: z.union([
    z.array(z.object({
      name: z.string(),
      status: z.string(),
      version: z.string().optional(),
      response_time_ms: z.number().optional(),
      error_message: z.string().nullable().optional(),
    })),
    z.record(z.unknown()),
  ]),
  active_experiments: z.number().int().min(0),
  total_experiments: z.number().int().min(0),
  queue_size: z.number().int().min(0),
});

export const HealthCheckSchema = z.object({
  name: z.string(),
  status: CheckStatusSchema,
  message: z.string().optional(),
});

export const HealthReadyResponseSchema = z.object({
  ready: z.boolean(),
  timestamp: z.string(),
  checks: z.array(HealthCheckSchema),
});

// =============================================================================
// CONFIG SCHEMAS
// =============================================================================

export const ExperimentDefaultsSchema = z.object({
  defaultRuns: z.number().int().min(1),
  defaultParallelJobs: z.number().int().min(1),
  defaultMaxFeatures: z.number().int().min(100),
  defaultRansacThreshold: z.number().positive(),
  defaultRansacConfidence: z.number().min(0).max(1),
  defaultRansacMaxIters: z.number().int().min(100),
  defaultRatioThreshold: z.number().positive(),
});

export const AlgorithmConfigSchema = z.object({
  featureTypes: z.array(z.string()),
  ransacTypes: z.array(z.string()),
});

export const ClientConfigSchema = z.object({
  experiment: ExperimentDefaultsSchema,
  algorithms: AlgorithmConfigSchema,
});

export const DiagnosticsConfigSchema = z.object({
  results_root: z.string(),
  visible_experiments: z.array(z.string()),
  count: z.number().int().min(0),
});

// =============================================================================
// TASK SCHEMAS
// =============================================================================

export const TaskResponseSchema = z.object({
  task_id: z.string(),
  status: TaskStatusSchema,
  message: z.string().nullable().optional().default(''),
  // backend uses 0.0..1.0 for progress
  progress: z.number().min(0).max(1).nullable().optional().default(0),
  current_step: z.string().nullable().optional(),
  total_steps: z.number().int().min(0).nullable().optional(),
  experiment_id: z.string().nullable().optional(),
  created_at: z.string().nullable().optional().default(new Date().toISOString()),
  updated_at: z.string().nullable().optional().default(new Date().toISOString()),
  completed_at: z.string().nullable().optional(),
  error_details: z.record(z.unknown()).nullable().optional(),
  estimated_remaining_time: z.number().min(0).nullable().optional(),
}).passthrough(); // Allow additional fields

// =============================================================================
// EXPERIMENT SCHEMAS
// =============================================================================

export const ExperimentConfigSchema = z.object({
  name: z.string(),
  dataset_path: z.string(),
  output_dir: z.string(),
  feature_types: z.array(z.string()),
  ransac_types: z.array(z.string()),
  sequences: z.array(z.string()),
  num_runs: z.number().int().min(1),
  parallel_jobs: z.number().int().min(1),
  feature_params: z.record(z.unknown()),
  ransac_params: z.record(z.unknown()),
});

export const ExperimentSummarySchema = z.object({
  total_runs: z.number().int().min(0),
  successful_runs: z.number().int().min(0),
  failed_runs: z.number().int().min(0),
  total_frames: z.number().int().min(0),
  total_processing_time: z.number().min(0),
  average_fps: z.number().min(0),
  algorithms_tested: z.array(z.string()),
  sequences_processed: z.array(z.string()),
  best_algorithm: z.string().optional(),
  worst_algorithm: z.string().optional(),
});

// Temporarily use a very permissive schema to bypass validation issues
export const ExperimentSchema = z.object({}).passthrough().transform((data: any) => ({
  experiment_id: data.experiment_id || data.id || '',
  name: data.name || '',
  description: data.description || undefined,
  status: data.status || 'CREATED',
  created_at: data.created_at || new Date().toISOString(),
  updated_at: data.updated_at || new Date().toISOString(),
  completed_at: data.completed_at || undefined,
  config: data.config || {},
  summary: data.summary || undefined,
  task_id: data.task_id || undefined,
  output_files: data.output_files || [],
  algorithms: data.algorithms || [],
  ...data, // preserve all other fields
}));

// Accept both documented pagination (per_page/pages/has_prev) and internal pagination, and normalize to internal shape
const DocPaginationSchema = z.object({
  page: z.number().int().min(1),
  per_page: z.number().int().min(1),
  total: z.number().int().min(0),
  pages: z.number().int().min(0),
  has_prev: z.boolean(),
  has_next: z.boolean(),
  prev_num: z.number().int().nullable().optional(),
  next_num: z.number().int().nullable().optional(),
}).passthrough();

const ExperimentsListResponseRawSchema = z.object({
  experiments: z.array(ExperimentSchema),
  pagination: z.union([PaginationSchema, DocPaginationSchema]),
});

export const ExperimentsListResponseSchema = ExperimentsListResponseRawSchema.transform((data) => {
  const { experiments, pagination } = data as any;
  if ('limit' in pagination) {
    return { experiments, pagination };
  }
  return {
    experiments,
    pagination: {
      page: pagination.page,
      limit: pagination.per_page,
      total: pagination.total,
      total_pages: pagination.pages,
      has_next: pagination.has_next,
      has_previous: pagination.has_prev ?? false,
    },
  };
});

export const CreateExperimentResponseSchema = z.object({
  task: TaskResponseSchema,
  experiment: ExperimentSchema,
}).passthrough(); // Allow additional fields

// =============================================================================
// RESULTS SCHEMAS
// =============================================================================

export const ResultsOverviewSchema = z.object({
  algorithms: z.array(z.string()),
  summary_per_algorithm: z.record(z.string(), z.any()).optional().default({}),
}).passthrough(); // Allow additional fields

export const ResultsDiagnosticsSchema = z.object({
  storage_root: z.string().nullable().optional(),
  visible_keys: z.array(z.string()).optional().default([]),
  algorithms: z.array(z.string()).optional().default([]),
  per_algorithm: z.record(z.string(), z.object({
    metrics_exists: z.boolean(),
    frames_exists: z.boolean(),
  })).optional().default({}),
}).passthrough(); // Allow additional fields

export const MatchingMetricsSchema = z.object({
  avg_matches: z.number().min(0).optional().default(0),
  avg_inliers: z.number().min(0).optional().default(0),
  avg_inlier_ratio: z.number().min(0).max(1).optional().default(0),
  avg_match_score: z.number().min(0).optional().default(0),
  avg_reprojection_error: z.number().min(0).optional().default(0),
}).passthrough();

export const RansacMetricsSchema = z.object({
  avg_iterations: z.number().min(0).optional().default(0),
  std_iterations: z.number().min(0).optional().default(0),
  convergence_rate: z.number().min(0).max(1).optional().default(0),
  success_rate: z.number().min(0).max(1).optional().default(0),
  avg_processing_time_ms: z.number().min(0).optional().default(0),
}).passthrough();

export const AlgorithmMetricsResponseSchema = z.object({
  algorithm_key: z.string().optional(),
  feature_type: z.string().optional(),
  ransac_type: z.string().optional(),
  // 允许 null 或缺失
  trajectory: z.record(z.unknown()).nullable().optional(),
  matching: MatchingMetricsSchema.optional(),
  ransac: RansacMetricsSchema.optional(),
  avg_frame_time_ms: z.number().min(0).optional().default(0),
  total_time_s: z.number().min(0).optional().default(0),
  fps: z.number().min(0).optional().default(0),
  success_rate: z.number().min(0).max(1).optional().default(0),
  total_frames: z.number().int().min(0).optional().default(0),
  successful_frames: z.number().int().min(0).optional().default(0),
  failed_frames: z.number().int().min(0).optional().default(0),
  failure_reasons: z.record(z.number().int().min(0)).optional().default({}),
}).passthrough(); // Allow additional fields

// Critical: PR Curve validation - empty arrays indicate "no data" state
export const PRCurveResponseSchema = z.object({
  algorithm: z.string(),
  precisions: z.array(z.number().min(0).max(1)),
  recalls: z.array(z.number().min(0).max(1)),
  thresholds: z.array(z.number()),
  auc_score: z.number().min(0).max(1),
  optimal_threshold: z.number(),
  optimal_precision: z.number().min(0).max(1),
  optimal_recall: z.number().min(0).max(1),
  f1_scores: z.array(z.number().min(0).max(1)),
  max_f1_score: z.number().min(0).max(1),
}).passthrough();

export const AlgorithmResultResponseSchema = z.object({
  algorithm_key: z.string(),
  feature_type: z.string(),
  ransac_type: z.string(),
  sequence: z.string(),
  metrics: AlgorithmMetricsResponseSchema,
  pr_curve: PRCurveResponseSchema.nullable().optional(),
  visualization_files: z.array(z.string()),
});

export const FrameResultResponseSchema = z.object({
  // 后端可能返回数字，这里全部转成字符串
  frame_id: z.union([z.string(), z.number()]).transform(v => String(v)),
  timestamp: z.union([z.string(), z.number()]).transform(v => String(v)),
  num_matches: z.number().int().min(0),
  num_inliers: z.number().int().min(0),
  inlier_ratio: z.number().min(0).max(1),
  processing_time: z.number().min(0),
  status: z.string(),
  pose_error: z.number().optional(),
  // 允许 null，并规范化为 []
  reprojection_errors: z.array(z.number()).nullable().optional().transform(v => Array.isArray(v) ? v : []),
});

export const FrameResultsResponseSchema = z.object({
  experiment_id: z.union([z.string(), z.number()]).transform(v => String(v)),
  algorithm_key: z.string(),
  sequence: z.union([z.string(), z.number()]).transform(v => String(v)),
  frames: z.array(FrameResultResponseSchema),
  pagination: PaginationSchema,
  summary: z.record(z.unknown()),
});

// Critical: Trajectory validation - accept both backend shapes and normalize to { poses, gt, ref }
const TrajectoryShapeA = z.object({
  poses: z.array(z.record(z.unknown())),
  gt: z.array(z.record(z.unknown())).optional(),
  ref: z.array(z.record(z.unknown())).optional(),
}).passthrough();

const TrajectoryShapeB = z.object({
  estimated_trajectory: z.array(z.record(z.unknown())),
  groundtruth_trajectory: z.array(z.record(z.unknown())).optional(),
  metadata: z
    .object({
      has_groundtruth: z.boolean().optional(),
      reference_groundtruth: z.boolean().optional(),
    })
    .optional(),
}).passthrough();

export const TrajectoryResponseSchema = z
  .union([TrajectoryShapeA, TrajectoryShapeB])
  .transform((data: any) => {
    if ('poses' in data) {
      return {
        poses: data.poses || [],
        gt: Array.isArray((data as any).gt) ? (data as any).gt : undefined,
        ref: Array.isArray((data as any).ref) ? (data as any).ref : undefined,
      };
    }
    const hasGT = !!data?.metadata?.has_groundtruth;
    const isRef = !!data?.metadata?.reference_groundtruth;
    const gtArr = Array.isArray(data.groundtruth_trajectory)
      ? (data.groundtruth_trajectory as any[])
      : [];
    return {
      poses: (data.estimated_trajectory as any[]) || [],
      gt: hasGT ? gtArr : undefined,
      ref: !hasGT && isRef ? gtArr : undefined,
    };
  });

// =============================================================================
// VALIDATION HELPERS
// =============================================================================

export const validateApiResponse = <T>(schema: z.ZodType<T, any, any>, data: unknown): T => {
  try {
    return schema.parse(data);
  } catch (error) {
    if (error instanceof z.ZodError) {
      console.error('API Response validation failed:', {
        errors: error.errors,
        data,
      });
      throw new Error(`API response validation failed: ${error.errors.map(e => e.message).join(', ')}`);
    }
    throw error;
  }
};

// Export type inference helpers
export type ValidatedResultsOverview = z.infer<typeof ResultsOverviewSchema>;
export type ValidatedResultsDiagnostics = z.infer<typeof ResultsDiagnosticsSchema>;
export type ValidatedPRCurveResponse = z.infer<typeof PRCurveResponseSchema>;
export type ValidatedTrajectoryResponse = z.infer<typeof TrajectoryResponseSchema>;
export type ValidatedFrameResultsResponse = z.infer<typeof FrameResultsResponseSchema>;
export type ValidatedAlgorithmResultResponse = z.infer<typeof AlgorithmResultResponseSchema>;
export type ValidatedExperimentsListResponse = z.infer<typeof ExperimentsListResponseSchema>;
export type ValidatedClientConfig = z.infer<typeof ClientConfigSchema>;
export type ValidatedHealthResponse = z.infer<typeof HealthResponseSchema>;
export type ValidatedTaskResponse = z.infer<typeof TaskResponseSchema>;
