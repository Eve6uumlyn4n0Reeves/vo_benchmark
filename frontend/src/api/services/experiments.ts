/**
 * Experiments API service
 * Handles experiment management endpoints with runtime validation
 *
 * 注意：仅支持 /experiments-doc/ 前缀路径，避免使用 legacy /experiments/
 * 所有实验相关功能统一使用文档化的 API 端点
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiRequest } from '../httpClient';
import { queryKeys } from '../queryKeys';
import {
  ExperimentsListResponseSchema,
  ExperimentSchema,
  CreateExperimentResponseSchema,
  validateApiResponse,
} from '../schemas';
import type {
  ExperimentsListResponse,
  Experiment,
  CreateExperimentRequest,
  CreateExperimentResponse,
  ExperimentsListParams,
} from '@/types/api';
import { useToast } from '@/components/common';

// =============================================================================
// API FUNCTIONS
// =============================================================================

/**
 * Get experiments list with pagination and filtering
 * GET /api/v1/experiments-doc/
 */
export const getExperiments = async (params: ExperimentsListParams = {}): Promise<ExperimentsListResponse> => {
  const response = await apiRequest.get('/experiments-doc/', { params });
  return validateApiResponse(ExperimentsListResponseSchema, response.data);
};

/**
 * Get experiment by ID
 * GET /api/v1/experiments-doc/{id}
 */
export const getExperiment = async (id: string): Promise<Experiment> => {
  const response = await apiRequest.get(`/experiments-doc/${id}`);
  return validateApiResponse(ExperimentSchema, response.data);
};

/**
 * Create new experiment
 * POST /api/v1/experiments-doc/
 */
export const createExperiment = async (data: CreateExperimentRequest): Promise<CreateExperimentResponse> => {
  const response = await apiRequest.post('/experiments-doc/', data);
  // 后端保证返回 { task, experiment }，但在某些错误恢复场景下可能缺少 experiment。
  // 这里强制构造缺省 experiment 以满足类型要求，防止 TS 报错。
  const parsed = validateApiResponse(CreateExperimentResponseSchema, response.data) as CreateExperimentResponse;
  return parsed;
};

/**
 * Get experiment history
 * GET /api/v1/experiments-doc/{id}/history
 */
export const getExperimentHistory = async (id: string): Promise<Experiment[]> => {
  const response = await apiRequest.get(`/experiments-doc/${id}/history`);
  // History returns array of experiments
  return response.data.map((item: unknown) => validateApiResponse(ExperimentSchema, item));
};

/**
 * Delete experiment
 * DELETE /api/v1/experiments-doc/{id}
 */
export const deleteExperiment = async (id: string): Promise<void> => {
  await apiRequest.delete(`/experiments-doc/${id}`);
};

/**
 * Preview output path for experiment
 * POST /api/v1/experiments/preview-output-path
 */
export const previewOutputPath = async (params: {
  dataset_path: string;
  output_root?: string;
}): Promise<{ output_path: string; files?: string[] }> => {
  const response = await apiRequest.post('/experiments-doc/preview-output-path', params);
  return response.data;
};

// =============================================================================
// REACT QUERY HOOKS
// =============================================================================

/**
 * Hook for experiments list with pagination and filtering
 */
export const useExperiments = (params: ExperimentsListParams = {}) => {
  return useQuery({
    queryKey: queryKeys.experimentsList(params),
    queryFn: () => getExperiments(params),
    staleTime: 30 * 1000, // 30 seconds
    gcTime: 5 * 60 * 1000, // 5 minutes
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
 * Hook for single experiment details
 */
export const useExperiment = (id: string) => {
  return useQuery({
    queryKey: queryKeys.experimentsDetail(id),
    queryFn: () => getExperiment(id),
    staleTime: 60 * 1000, // 1 minute
    gcTime: 10 * 60 * 1000, // 10 minutes
    enabled: !!id,
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
 * Hook for experiment history
 */
export const useExperimentHistory = (id: string) => {
  return useQuery({
    queryKey: queryKeys.experimentsHistory(id),
    queryFn: () => getExperimentHistory(id),
    staleTime: 2 * 60 * 1000, // 2 minutes
    gcTime: 10 * 60 * 1000, // 10 minutes
    enabled: !!id,
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
 * Hook for output path preview
 */
export const usePreviewOutputPath = () => {
  return useMutation({
    mutationFn: previewOutputPath,
    retry: false,
  });
};

/**
 * Hook for creating experiments
 */
export const useCreateExperiment = () => {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: createExperiment,
    onSuccess: (data) => {
      // Invalidate experiments list to refresh
      queryClient.invalidateQueries({ queryKey: queryKeys.experiments });

      toast.success('实验创建成功', {
        title: '创建成功',
      });

      return data;
    },
    onError: (error) => {
      console.error('Failed to create experiment:', error);

      let errorMessage = '创建实验失败';
      if (error instanceof Error) {
        errorMessage = error.message;
      }

      toast.error(errorMessage, {
        title: '创建失败',
      });
    },
    retry: false,
  });
};

/**
 * Hook for deleting experiments
 */
export const useDeleteExperiment = () => {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: deleteExperiment,
    onSuccess: () => {
      // Invalidate experiments list to refresh
      queryClient.invalidateQueries({ queryKey: queryKeys.experiments });

      toast.success('实验删除成功', {
        title: '删除成功',
      });
    },
    onError: (error) => {
      console.error('Failed to delete experiment:', error);

      let errorMessage = '删除实验失败';
      if (error instanceof Error) {
        errorMessage = error.message;
      }

      toast.error(errorMessage, {
        title: '删除失败',
      });
    },
    retry: false,
  });
};
