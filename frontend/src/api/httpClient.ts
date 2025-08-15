import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse, AxiosError } from 'axios';
import { v4 as uuidv4 } from 'uuid';

// Environment configuration
import { env } from '@/utils/env';
const API_BASE_URL = env.apiBaseUrl();
const API_TIMEOUT = env.apiTimeout();
const MAX_RETRIES = env.maxRetries();

// Error types based on backend contract
export interface ApiError {
  error?: string;
  error_code?: string;
  message?: string;
  details?: Record<string, unknown>;
  request_id?: string;
}

export interface ApiErrorResponse {
  data: ApiError;
  status: number;
  statusText: string;
}

// Request configuration with retry support
interface RetryConfig {
  retries: number;
  retryDelay: number;
  retryCondition: (error: AxiosError) => boolean;
}

// Create axios instance
const createHttpClient = (): AxiosInstance => {
  const client = axios.create({
    baseURL: API_BASE_URL,
    timeout: API_TIMEOUT,
    headers: {
      'Content-Type': 'application/json',
    },
  });

  // Request interceptor
  client.interceptors.request.use(
    (config) => {
      // Add request ID for tracing
      const requestId = uuidv4();
      config.headers['x-request-id'] = requestId;
      
      // Log request in debug mode
      if (env.enableDebug()) {
        console.log(`[API Request] ${config.method?.toUpperCase()} ${config.url}`, {
          requestId,
          params: config.params,
          data: config.data,
        });
      }
      
      return config;
    },
    (error) => {
      console.error('[API Request Error]', error);
      return Promise.reject(error);
    }
  );

  // Response interceptor
  client.interceptors.response.use(
    (response: AxiosResponse) => {
      // Log response in debug mode
      if (env.enableDebug()) {
        const requestId = response.config.headers['x-request-id'];
        console.log(`[API Response] ${response.status} ${response.config.url}`, {
          requestId,
          data: response.data,
        });
      }
      
      return response;
    },
    (error: AxiosError) => {
      // Extract request ID for error tracking
      const requestId = error.config?.headers?.['x-request-id'] as string;
      
      // Parse error response according to backend contract
      const apiError: ApiError = {
        request_id: requestId,
      };

      if (error.response?.data) {
        const errorData = error.response.data as Record<string, unknown>;
        
        // Handle structured error response
        if (typeof errorData === 'object') {
          apiError.error = errorData['error'] as string;
          apiError.error_code = errorData['error_code'] as string;
          apiError.message = errorData['message'] as string;
          apiError.details = errorData['details'] as Record<string, unknown>;
        }
      } else if (error.message) {
        // Handle network/timeout errors
        apiError.error = error.message;
        apiError.message = error.message;
      }

      // Log error
      console.error('[API Error]', {
        requestId,
        status: error.response?.status,
        url: error.config?.url,
        method: error.config?.method,
        error: apiError,
      });

      // Create enhanced error object
      const enhancedError = new Error(apiError.message || apiError.error || 'Unknown API error');
      (enhancedError as any).apiError = apiError;
      (enhancedError as any).status = error.response?.status;
      (enhancedError as any).requestId = requestId;

      return Promise.reject(enhancedError);
    }
  );

  return client;
};

// Retry logic for network errors
const shouldRetry = (error: AxiosError): boolean => {
  // Don't retry on 4xx errors (client errors)
  if (error.response && error.response.status >= 400 && error.response.status < 500) {
    return false;
  }
  
  // Retry on network errors, timeouts, and 5xx errors
  return (
    !error.response || // Network error
    error.code === 'ECONNABORTED' || // Timeout
    (error.response.status >= 500) // Server error
  );
};

const delay = (ms: number): Promise<void> => 
  new Promise(resolve => setTimeout(resolve, ms));

// Enhanced request method with retry logic
const requestWithRetry = async <T = any>(
  client: AxiosInstance,
  config: AxiosRequestConfig,
  retryConfig: Partial<RetryConfig> = {}
): Promise<AxiosResponse<T>> => {
  const {
    retries = MAX_RETRIES,
    retryDelay = 1000,
    retryCondition = shouldRetry,
  } = retryConfig;

  let lastError: AxiosError;

  for (let attempt = 0; attempt <= retries; attempt++) {
    try {
      return await client.request<T>(config);
    } catch (error) {
      lastError = error as AxiosError;
      
      // Don't retry if condition is not met or it's the last attempt
      if (!retryCondition(lastError) || attempt === retries) {
        throw lastError;
      }
      
      // Exponential backoff
      const delayMs = retryDelay * Math.pow(2, attempt);
      await delay(delayMs);
      
      if (env.enableDebug()) {
        console.log(`[API Retry] Attempt ${attempt + 1}/${retries + 1} after ${delayMs}ms delay`);
      }
    }
  }

  throw lastError!;
};

// Create and export the HTTP client instance
export const httpClient = createHttpClient();

// Export enhanced request methods
export const apiRequest = {
  get: <T = any>(url: string, config?: AxiosRequestConfig) =>
    requestWithRetry<T>(httpClient, { ...config, method: 'GET', url }),
    
  post: <T = any>(url: string, data?: any, config?: AxiosRequestConfig) =>
    requestWithRetry<T>(httpClient, { ...config, method: 'POST', url, data }),
    
  put: <T = any>(url: string, data?: any, config?: AxiosRequestConfig) =>
    requestWithRetry<T>(httpClient, { ...config, method: 'PUT', url, data }),
    
  patch: <T = any>(url: string, data?: any, config?: AxiosRequestConfig) =>
    requestWithRetry<T>(httpClient, { ...config, method: 'PATCH', url, data }),
    
  delete: <T = any>(url: string, config?: AxiosRequestConfig) =>
    requestWithRetry<T>(httpClient, { ...config, method: 'DELETE', url }),
};

// Export utility functions
export const getApiBaseUrl = (): string => API_BASE_URL;
export const isApiError = (error: unknown): error is Error & { apiError: ApiError } => {
  return error instanceof Error && 'apiError' in error;
};
