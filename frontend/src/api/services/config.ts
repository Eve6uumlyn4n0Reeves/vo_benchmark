/**
 * Config API service
 * Handles configuration endpoints with runtime validation
 */

import { useQuery } from '@tanstack/react-query';
import { apiRequest } from '../httpClient';
import { queryKeys } from '../queryKeys';
import {
  ClientConfigSchema,
  AlgorithmConfigSchema,
  DiagnosticsConfigSchema,
  validateApiResponse,
} from '../schemas';
import type {
  ClientConfig,
  AlgorithmConfig,
  DiagnosticsConfig,
} from '@/types/api';

// =============================================================================
// API FUNCTIONS
// =============================================================================

/**
 * Get client configuration (experiment defaults + algorithms)
 * GET /api/v1/config/client
 */
export const getClientConfig = async (): Promise<ClientConfig> => {
  const response = await apiRequest.get('/config/client');
  return validateApiResponse(ClientConfigSchema, response.data);
};

/**
 * Get system configuration (non-sensitive summary)
 * GET /api/v1/config/system
 */
export const getSystemConfig = async (): Promise<Record<string, unknown>> => {
  const response = await apiRequest.get('/config/system');
  return response.data as Record<string, unknown>;
};

/**
 * Get algorithm configuration
 * GET /api/v1/config/algorithms
 */
export const getAlgorithmConfig = async (): Promise<AlgorithmConfig> => {
  const response = await apiRequest.get('/config/algorithms');
  return validateApiResponse(AlgorithmConfigSchema, response.data);
};

/**
 * Get diagnostics configuration (results root + visible experiments)
 * GET /api/v1/config/diagnostics
 */
export const getDiagnosticsConfig = async (): Promise<DiagnosticsConfig> => {
  const response = await apiRequest.get('/config/diagnostics');
  return validateApiResponse(DiagnosticsConfigSchema, response.data);
};

// =============================================================================
// REACT QUERY HOOKS
// =============================================================================

/**
 * Hook for client configuration
 * This is frequently used for form defaults, so cache it longer
 */
export const useClientConfig = () => {
  return useQuery({
    queryKey: queryKeys.configClient(),
    queryFn: getClientConfig,
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 10 * 60 * 1000, // 10 minutes
    retry: (failureCount, error) => {
      // Don't retry on 4xx errors
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
 * Hook for system configuration
 */
export const useSystemConfig = () => {
  return useQuery({
    queryKey: queryKeys.configSystem(),
    queryFn: getSystemConfig,
    staleTime: 5 * 60 * 1000,
    gcTime: 10 * 60 * 1000,
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
 * Hook for algorithm configuration
 */
export const useAlgorithmConfig = () => {
  return useQuery({
    queryKey: queryKeys.configAlgorithms(),
    queryFn: getAlgorithmConfig,
    staleTime: 5 * 60 * 1000,
    gcTime: 10 * 60 * 1000,
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
 * Hook for diagnostics configuration
 */
export const useDiagnosticsConfig = () => {
  return useQuery({
    queryKey: queryKeys.configDiagnostics(),
    queryFn: getDiagnosticsConfig,
    staleTime: 2 * 60 * 1000, // 2 minutes
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
