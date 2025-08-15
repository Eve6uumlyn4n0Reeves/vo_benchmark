import { describe, it, expect, jest, beforeEach, afterEach } from '@jest/globals';

// Mock axios before importing httpClient to ensure proper initialization
jest.mock('axios', () => ({
  default: {
    create: jest.fn(() => ({
      interceptors: {
        request: { use: jest.fn() },
        response: { use: jest.fn() },
      },
      request: jest.fn(),
      get: jest.fn(),
      post: jest.fn(),
      put: jest.fn(),
      patch: jest.fn(),
      delete: jest.fn(),
    })),
  },
  create: jest.fn(() => ({
    interceptors: {
      request: { use: jest.fn() },
      response: { use: jest.fn() },
    },
    request: jest.fn(),
    get: jest.fn(),
    post: jest.fn(),
    put: jest.fn(),
    patch: jest.fn(),
    delete: jest.fn(),
  })),
}));

import axios from 'axios';
import { apiRequest, isApiError, getApiBaseUrl, httpClient } from '../httpClient';

const mockedAxios = axios as jest.Mocked<typeof axios>;
const mockedHttpClient = httpClient as jest.Mocked<typeof httpClient>;

describe('httpClient', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  describe('getApiBaseUrl', () => {
    it('should return the API base URL', () => {
      expect(getApiBaseUrl()).toBe('/api/v1');
    });
  });

  describe('isApiError', () => {
    it('should identify API errors correctly', () => {
      const apiError = new Error('API Error');
      (apiError as any).apiError = {
        error_code: 'VALIDATION_ERROR',
        message: 'Invalid input',
      };

      expect(isApiError(apiError)).toBe(true);
      expect(isApiError(new Error('Regular error'))).toBe(false);
      expect(isApiError('string error')).toBe(false);
    });
  });

  describe('apiRequest', () => {
    it('should make successful GET request', async () => {
      const mockResponse = {
        data: { status: 'healthy' },
        status: 200,
        statusText: 'OK',
        headers: {},
        config: {},
      };

      // Mock the httpClient request method directly
      mockedHttpClient.request = jest.fn().mockResolvedValue(mockResponse);

      const response = await apiRequest.get('/health');
      expect(response.data).toEqual({ status: 'healthy' });
    });

    it('should make successful POST request', async () => {
      const mockResponse = {
        data: { task_id: 'task-123' },
        status: 201,
        statusText: 'Created',
        headers: {},
        config: {},
      };

      const requestData = { name: 'test-experiment' };

      // Mock the httpClient request method directly
      mockedHttpClient.request = jest.fn().mockResolvedValue(mockResponse);

      const response = await apiRequest.post('/experiments', requestData);
      expect(response.data).toEqual({ task_id: 'task-123' });
    });

    it('should handle network errors with retry', async () => {
      const networkError = new Error('Network Error');
      (networkError as any).code = 'ECONNABORTED';

      // Mock the httpClient request method with retry behavior
      mockedHttpClient.request = jest.fn()
        .mockRejectedValueOnce(networkError)
        .mockRejectedValueOnce(networkError)
        .mockResolvedValue({
          data: { status: 'healthy' },
          status: 200,
        });

      const response = await apiRequest.get('/health');
      expect(response.data).toEqual({ status: 'healthy' });
    });

    it('should not retry 4xx errors', async () => {
      const clientError = new Error('Bad Request');
      (clientError as any).response = { status: 400 };

      // Mock the httpClient request method to reject with client error
      mockedHttpClient.request = jest.fn().mockRejectedValue(clientError);

      await expect(apiRequest.get('/invalid')).rejects.toThrow('Bad Request');
    });

    it('should handle structured error responses', async () => {
      // Create an error object that matches what the response interceptor would create
      const enhancedError = new Error('Invalid experiment name');
      (enhancedError as any).apiError = {
        error_code: 'VALIDATION_ERROR',
        message: 'Invalid experiment name',
        request_id: 'req-123',
        details: { field: 'name' },
      };
      // Add response property to prevent retry logic
      (enhancedError as any).response = { status: 422 };

      // Mock the httpClient request method to reject with enhanced error
      mockedHttpClient.request = jest.fn().mockRejectedValue(enhancedError);

      // Test that the request rejects with the expected error
      await expect(apiRequest.post('/experiments', {})).rejects.toMatchObject({
        message: 'Invalid experiment name',
        apiError: {
          error_code: 'VALIDATION_ERROR',
          message: 'Invalid experiment name',
          request_id: 'req-123',
        },
      });
    });
  });
});
