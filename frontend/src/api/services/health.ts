/**
 * Health API service
 * Handles health check endpoints with runtime validation
 */

import { useQuery } from '@tanstack/react-query';
import { apiRequest } from '../httpClient';
import { queryKeys } from '../queryKeys';
import {
  HealthResponseSchema,
  HealthDetailedResponseSchema,
  HealthReadyResponseSchema,
  validateApiResponse,
} from '../schemas';
import type {
  HealthResponse,
  HealthDetailedResponse,
  HealthReadyResponse,
} from '@/types/api';

// =============================================================================
// API FUNCTIONS
// =============================================================================

/**
 * Get basic health status
 * GET /api/v1/health-doc/
 */
export const getHealth = async (): Promise<HealthResponse> => {
  const response = await apiRequest.get('/health-doc/');
  return validateApiResponse(HealthResponseSchema, response.data);
};

/**
 * Get detailed health status with system metrics
 * GET /api/v1/health-doc/detailed
 */
export const getHealthDetailed = async (): Promise<HealthDetailedResponse> => {
  const response = await apiRequest.get('/health-doc/detailed');
  return validateApiResponse(HealthDetailedResponseSchema, response.data);
};

/**
 * Get readiness check status
 * GET /api/v1/health-doc/ready
 */
export const getHealthReady = async (): Promise<HealthReadyResponse> => {
  const response = await apiRequest.get('/health-doc/ready');
  return validateApiResponse(HealthReadyResponseSchema, response.data);
};

// =============================================================================
// REACT QUERY HOOKS
// =============================================================================

/**
 * Hook for basic health status
 */
export const useHealth = () => {
  return useQuery({
    queryKey: queryKeys.health,
    queryFn: getHealth,
    staleTime: 30 * 1000, // 30 seconds
    gcTime: 2 * 60 * 1000, // 2 minutes
    refetchInterval: 30 * 1000, // Refetch every 30 seconds

  });
};

/**
 * Hook for detailed health status
 */
export const useHealthDetailed = () => {
  return useQuery({
    queryKey: queryKeys.healthDetailed(),
    queryFn: getHealthDetailed,
    staleTime: 30 * 1000,
    gcTime: 2 * 60 * 1000,
    refetchInterval: 30 * 1000,

  });
};

/**
 * Hook for readiness check
 */
export const useHealthReady = () => {
  return useQuery({
    queryKey: queryKeys.healthReady(),
    queryFn: getHealthReady,
    staleTime: 10 * 1000, // 10 seconds for readiness
    gcTime: 1 * 60 * 1000, // 1 minute
    refetchInterval: 10 * 1000, // Refetch every 10 seconds

  });
};
