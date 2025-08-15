/**
 * Tasks API service
 * Handles task management endpoints with runtime validation
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiRequest } from '../httpClient';
import { queryKeys } from '../queryKeys';
import {
  TaskResponseSchema,
  validateApiResponse,
} from '../schemas';
import type {
  Task,
  TasksListParams,
} from '@/types/api';
import { useToast } from '@/components/common';

// =============================================================================
// API FUNCTIONS
// =============================================================================

/**
 * Get tasks list with pagination and filtering
 * GET /api/v1/tasks/
 */
export const getTasks = async (params: TasksListParams = {}): Promise<Task[]> => {
  const response = await apiRequest.get('/tasks/', { params });
  return (response.data as unknown[]).map((item) => validateApiResponse(TaskResponseSchema, item) as Task);
};

/**
 * Get task by ID
 * GET /api/v1/tasks/{id}
 */
export const getTask = async (id: string): Promise<Task> => {
  const response = await apiRequest.get(`/tasks/${id}`);
  return validateApiResponse(TaskResponseSchema, response.data) as Task;
};

/**
 * Cancel task
 * POST /api/v1/tasks/{id}/cancel
 */
export const cancelTask = async (id: string): Promise<{ success: boolean }> => {
  const response = await apiRequest.post(`/tasks/${id}/cancel`);
  return response.data as { success: boolean };
};

/**
 * Get task logs
 * GET /api/v1/tasks/{id}/logs
 */
export const getTaskLogs = async (id: string): Promise<{ logs: string[] }> => {
  const response = await apiRequest.get(`/tasks/${id}/logs`);
  return response.data;
};

// =============================================================================
// REACT QUERY HOOKS
// =============================================================================

/**
 * Hook for tasks list with pagination and filtering
 */
export const useTasks = (params: TasksListParams = {}, options?: { autoRefresh?: boolean; refetchMs?: number }) => {
  return useQuery({
    queryKey: queryKeys.tasksList(params as unknown as Record<string, unknown>),
    queryFn: () => getTasks(params),
    staleTime: 30 * 1000, // 30 seconds
    gcTime: 5 * 60 * 1000, // 5 minutes
    refetchInterval: options?.autoRefresh ? (options?.refetchMs ?? 30 * 1000) : false,
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
 * Hook for single task details
 */
export const useTask = (id: string, options?: { autoRefresh?: boolean; refetchMs?: number }) => {
  return useQuery({
    queryKey: queryKeys.tasksDetail(id),
    queryFn: () => getTask(id),
    staleTime: 10 * 1000, // 10 seconds for real-time updates
    gcTime: 5 * 60 * 1000, // 5 minutes
    refetchInterval: options?.autoRefresh ? (options?.refetchMs ?? 10 * 1000) : false,
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
 * Hook for task logs
 */
export const useTaskLogs = (id: string, options?: { autoRefresh?: boolean; refetchMs?: number }) => {
  return useQuery({
    queryKey: queryKeys.tasksLogs(id),
    queryFn: () => getTaskLogs(id),
    staleTime: 5 * 1000, // 5 seconds for real-time logs
    gcTime: 2 * 60 * 1000, // 2 minutes
    refetchInterval: options?.autoRefresh ? (options?.refetchMs ?? 5 * 1000) : false,
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
 * Hook for canceling tasks
 */
export const useCancelTask = () => {
  const queryClient = useQueryClient();
  const { toast } = useToast();

  return useMutation({
    mutationFn: cancelTask,
    onSuccess: () => {
      // Invalidate tasks list to refresh
      queryClient.invalidateQueries({ queryKey: queryKeys.tasks });

      toast.success('任务已取消', {
        title: '取消成功',
      });
    },
    onError: (error) => {
      console.error('Failed to cancel task:', error);
      
      let errorMessage = '取消任务失败';
      if (error instanceof Error) {
        errorMessage = error.message;
      }

      toast.error(errorMessage, {
        title: '取消失败',
      });
    },
    retry: false,
  });
};
