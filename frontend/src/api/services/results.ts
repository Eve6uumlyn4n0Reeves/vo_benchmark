/**
 * Results API service
 * Handles experiment results endpoints with runtime validation
 */

import { useQuery } from '@tanstack/react-query';
import { apiRequest } from '../httpClient';
import { queryKeys } from '../queryKeys';
import { measureNetworkRequest } from '@/utils/performance';
import {
  AlgorithmResultResponseSchema,
  FrameResultsResponseSchema,
  PRCurveApiResponseSchema,
  TrajectoryApiResponseSchema,
  ResultsOverviewSchema,
  ResultsDiagnosticsSchema,
  validateApiResponse,
} from '../schemas';
import type {
  AlgorithmResultResponse,
  FrameResultsResponse,
  PRCurveApiResponse,
  TrajectoryApiResponse,
  FrameResultsParams,
  TrajectoryParams,
  ExportParams,
} from '@/types/api';
import type { ValidatedResultsOverview, ValidatedResultsDiagnostics } from '../schemas';

// =============================================================================
// API FUNCTIONS
// =============================================================================

/**
 * Get experiment results overview
 * GET /api/v1/results/{id}/overview
 */
export const getResultsOverview = async (experimentId: string): Promise<ValidatedResultsOverview> => {
  const response = await apiRequest.get(`/results/${experimentId}/overview`);
  return validateApiResponse(ResultsOverviewSchema, response.data);
};

/**
 * Get experiment diagnostics
 * GET /api/v1/results/{id}/diagnose
 */
export const getResultsDiagnostics = async (experimentId: string): Promise<ValidatedResultsDiagnostics> => {
  const response = await apiRequest.get(`/results/${experimentId}/diagnose`);
  return validateApiResponse(ResultsDiagnosticsSchema, response.data);
};

/**
 * Get algorithm results
 * GET /api/v1/results/{id}/{algorithm}
 */
export const getAlgorithmResult = async (
  experimentId: string,
  algorithmKey: string
): Promise<AlgorithmResultResponse> => {
  const response = await apiRequest.get(`/results/${experimentId}/${algorithmKey}`);
  const validated = validateApiResponse(AlgorithmResultResponseSchema, response.data);
  // Normalize trajectory: backend may return null; our TS type expects optional
  const normalized: AlgorithmResultResponse = {
    ...validated,
    metrics: {
      ...(validated as any).metrics,
      trajectory: ((validated as any).metrics?.trajectory ?? undefined) as any,
    },
  } as AlgorithmResultResponse;
  return normalized;
};

/**
 * Get frame results with pagination
 * GET /api/v1/results/{id}/{algorithm}/frames
 */
export const getFrameResults = async (
  experimentId: string,
  algorithmKey: string,
  params: FrameResultsParams = {}
): Promise<FrameResultsResponse> => {
  const normalized = params?.page || params?.per_page ? params : { page: 1, per_page: 100 };
  const response = await apiRequest.get(`/results/${experimentId}/${algorithmKey}/frames`, { params: normalized });
  return validateApiResponse(FrameResultsResponseSchema, response.data);
};

/**
 * Get PR curve data
 * GET /api/v1/results/{id}/{algorithm}/pr-curve
 */
export const getPRCurve = async (
  experimentId: string,
  algorithmKey: string
): Promise<PRCurveApiResponse> => {
  const response = await apiRequest.get(`/results/${experimentId}/${algorithmKey}/pr-curve`);
  return validateApiResponse(PRCurveApiResponseSchema, response.data);
};

/**
 * Get trajectory data
 * GET /api/v1/results/{id}/{algorithm}/trajectory
 */
export const getTrajectory = async (
  experimentId: string,
  algorithmKey: string,
  params: TrajectoryParams = {}
): Promise<TrajectoryApiResponse> => {
  return measureNetworkRequest(
    `getTrajectory-${algorithmKey}`,
    async () => {
      const response = await apiRequest.get(`/results/${experimentId}/${algorithmKey}/trajectory`, { params });
      const data = validateApiResponse(TrajectoryApiResponseSchema, response.data);

      // 记录响应大小和压缩信息
      const headers = response.headers;
      const payloadSize = headers['x-payload-size'] || 'unknown';
      const compressed = headers['x-compressed'] === 'true';
      const responseTime = headers['x-response-time'] || 'unknown';

      console.log(`[getTrajectory] ${algorithmKey}: payload=${payloadSize}bytes, compressed=${compressed}, server_time=${responseTime}`);

      return data;
    },
    { experimentId, algorithmKey, params }
  );
};

/**
 * Export experiment results
 * GET /api/v1/results/{id}/export
 */
export const exportResults = async (
  experimentId: string,
  params: ExportParams
): Promise<Blob> => {
  const response = await apiRequest.get(`/results/${experimentId}/export`, {
    params,
    responseType: 'blob',
  });
  return response.data;
};

// =============================================================================
// REACT QUERY HOOKS
// =============================================================================

/**
 * Hook for results overview
 */
export const useResultsOverview = (experimentId: string) => {
  return useQuery({
    queryKey: queryKeys.resultsOverview(experimentId),
    queryFn: () => getResultsOverview(experimentId),
    staleTime: 2 * 60 * 1000, // 2 minutes
    gcTime: 10 * 60 * 1000, // 10 minutes
    enabled: !!experimentId,
    retry: (failureCount, error) => {
      if (error instanceof Error && 'status' in error) {
        const status = (error as any).status;
        if (status >= 400 && status < 500) {
          return false;
        }
      }
      return failureCount < 2;
    },
  });
};

/**
 * Hook for results diagnostics
 */
export const useResultsDiagnostics = (experimentId: string) => {
  return useQuery({
    queryKey: queryKeys.resultsDiagnose(experimentId),
    queryFn: () => getResultsDiagnostics(experimentId),
    staleTime: 2 * 60 * 1000,
    gcTime: 10 * 60 * 1000,
    enabled: !!experimentId,
    retry: (failureCount, error) => {
      if (error instanceof Error && 'status' in error) {
        const status = (error as any).status;
        if (status >= 400 && status < 500) {
          return false;
        }
      }
      return failureCount < 2;
    },
  });
};

/**
 * Hook for algorithm results
 */
export const useAlgorithmResult = (experimentId: string, algorithmKey: string) => {
  return useQuery({
    queryKey: queryKeys.resultsAlgorithm(experimentId, algorithmKey),
    queryFn: () => getAlgorithmResult(experimentId, algorithmKey),
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 15 * 60 * 1000, // 15 minutes
    enabled: !!(experimentId && algorithmKey),
    retry: (failureCount, error) => {
      if (error instanceof Error && 'status' in error) {
        const status = (error as any).status;
        if (status >= 400 && status < 500) {
          return false;
        }
      }
      return failureCount < 2;
    },
  });
};

/**
 * Hook for frame results
 */
export const useFrameResults = (
  experimentId: string,
  algorithmKey: string,
  params: FrameResultsParams = {}
) => {
  return useQuery({
    queryKey: queryKeys.resultsFrames(experimentId, algorithmKey, params),
    queryFn: () => getFrameResults(experimentId, algorithmKey, params),
    staleTime: 5 * 60 * 1000,
    gcTime: 15 * 60 * 1000,
    enabled: !!(experimentId && algorithmKey),
    retry: (failureCount, error) => {
      if (error instanceof Error && 'status' in error) {
        const status = (error as any).status;
        if (status >= 400 && status < 500) {
          return false;
        }
      }
      return failureCount < 2;
    },
  });
};

/**
 * Hook for PR curve data with enhanced computing state handling
 */
export const usePRCurve = (experimentId: string, algorithmKey: string) => {
  return useQuery({
    queryKey: queryKeys.resultsPrCurve(experimentId, algorithmKey),
    queryFn: async () => {
      const result = await getPRCurve(experimentId, algorithmKey);

      // 检查是否是计算中状态
      if (result && typeof result === 'object' && 'status' in result && result.status === 'computing') {
        // 抛出特殊错误，触发重试
        const error = new Error('PR曲线正在计算中') as any;
        error.isComputing = true;
        error.retryAfter = 3000; // 3秒后重试
        throw error;
      }

      return result;
    },
    staleTime: 10 * 60 * 1000, // 10 minutes - PR curves don't change
    gcTime: 30 * 60 * 1000, // 30 minutes
    enabled: !!(experimentId && algorithmKey),
    retry: (failureCount, error: any) => {
      // 如果是计算中状态，继续重试（最多10次）
      if (error?.isComputing && failureCount < 10) {
        return true;
      }

      // 其他错误的重试逻辑
      if (error instanceof Error && 'status' in error) {
        const status = (error as any).status;
        if (status >= 400 && status < 500) {
          return false;
        }
      }
      return failureCount < 2;
    },
    retryDelay: (attemptIndex, error: any) => {
      // 如果是计算中状态，使用较短的重试间隔
      if (error?.isComputing) {
        return error.retryAfter || 3000;
      }
      // 其他错误使用指数退避
      return Math.min(1000 * 2 ** attemptIndex, 30000);
    },
  });
};

/**
 * Hook for trajectory data
 */
export const useTrajectory = (
  experimentId: string,
  algorithmKey: string,
  params: TrajectoryParams = {}
) => {
  return useQuery({
    queryKey: queryKeys.resultsTrajectory(experimentId, algorithmKey, params),
    queryFn: async () => {
      const result = await getTrajectory(experimentId, algorithmKey, params);

      // 检查是否是计算中状态
      if (result && typeof result === 'object' && 'status' in result && result.status === 'computing') {
        // 抛出特殊错误，触发重试
        const error = new Error('轨迹正在计算中') as any;
        error.isComputing = true;
        error.retryAfter = 3000; // 3秒后重试
        throw error;
      }

      return result;
    },
    staleTime: 10 * 60 * 1000,
    gcTime: 30 * 60 * 1000,
    enabled: !!(experimentId && algorithmKey),
    retry: (failureCount, error: any) => {
      // 如果是计算中状态，继续重试（最多10次）
      if (error?.isComputing && failureCount < 10) {
        return true;
      }

      // 其他错误的重试逻辑
      if (error instanceof Error && 'status' in error) {
        const status = (error as any).status;
        if (status >= 400 && status < 500) {
          return false;
        }
      }
      return failureCount < 2;
    },
    retryDelay: (attemptIndex, error: any) => {
      // 如果是计算中状态，使用较短的重试间隔
      if (error?.isComputing) {
        return error.retryAfter || 3000;
      }
      // 其他错误使用指数退避
      return Math.min(1000 * 2 ** attemptIndex, 30000);
    },
  });
};


