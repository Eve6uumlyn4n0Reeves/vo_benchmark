import * as React from 'react';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { describe, it, expect, jest, beforeEach } from '@jest/globals';
import { useHealth, useHealthDetailed, useHealthReady } from '../health';
import * as httpClient from '../../httpClient';

// Mock the HTTP client
jest.mock('../../httpClient');
const mockedApiRequest = httpClient.apiRequest as jest.Mocked<typeof httpClient.apiRequest>;

// Test wrapper with QueryClient
const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        gcTime: 0,
      },
    },
  });

  return ({ children }: { children: React.ReactNode }) =>
    React.createElement(QueryClientProvider, { client: queryClient }, children);
};

describe('Health API Services', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('useHealth', () => {
    it('should fetch basic health status successfully', async () => {
      const mockHealthData = {
        status: 'healthy' as const,
        timestamp: '2025-01-13T12:00:00Z',
        version: '1.0.0',
        uptime: 3600,
      };

      mockedApiRequest.get.mockResolvedValue({
        data: mockHealthData,
      } as any);

      const { result } = renderHook(() => useHealth(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data).toEqual(mockHealthData);
      expect(mockedApiRequest.get).toHaveBeenCalledWith('/health-doc/');
    });

    it('should handle health API errors', async () => {
      const mockError = new Error('Health check failed');
      mockedApiRequest.get.mockRejectedValue(mockError);

      const { result } = renderHook(() => useHealth(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isError).toBe(true);
      });

      expect(result.current.error).toEqual(mockError);
    });
  });

  describe('useHealthDetailed', () => {
    it('should fetch detailed health status successfully', async () => {
      const mockDetailedData = {
        status: 'healthy' as const,
        timestamp: '2025-01-13T12:00:00Z',
        version: '1.0.0',
        uptime: 3600,
        system_metrics: { cpu: 45, memory: 60 },
        dependencies: { database: 'connected' },
        active_experiments: 5,
        total_experiments: 100,
        queue_size: 2,
      };

      mockedApiRequest.get.mockResolvedValue({
        data: mockDetailedData,
      } as any);

      const { result } = renderHook(() => useHealthDetailed(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data).toEqual(mockDetailedData);
      expect(mockedApiRequest.get).toHaveBeenCalledWith('/health-doc/detailed');
    });
  });

  describe('useHealthReady', () => {
    it('should fetch readiness check successfully', async () => {
      const mockReadyData = {
        ready: true,
        timestamp: '2025-01-13T12:00:00Z',
        checks: [
          { name: 'database', status: 'pass' as const, message: 'Connected' },
          { name: 'storage', status: 'pass' as const },
        ],
      };

      mockedApiRequest.get.mockResolvedValue({
        data: mockReadyData,
      } as any);

      const { result } = renderHook(() => useHealthReady(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data).toEqual(mockReadyData);
      expect(mockedApiRequest.get).toHaveBeenCalledWith('/health-doc/ready');
    });

    it('should handle failed readiness checks', async () => {
      const mockReadyData = {
        ready: false,
        timestamp: '2025-01-13T12:00:00Z',
        checks: [
          { name: 'database', status: 'pass' as const },
          { name: 'storage', status: 'fail' as const, message: 'Connection timeout' },
        ],
      };

      mockedApiRequest.get.mockResolvedValue({
        data: mockReadyData,
      } as any);

      const { result } = renderHook(() => useHealthReady(), {
        wrapper: createWrapper(),
      });

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true);
      });

      expect(result.current.data?.ready).toBe(false);
      expect(result.current.data?.checks).toHaveLength(2);
    });
  });
});
