import { useMemo } from 'react';
import { env } from '@/utils/env';

/**
 * Hook to get the API base URL from environment variables
 * Provides a consistent way to access the API base URL across the application
 */
export const useApiBaseUrl = () => {
  const baseUrl = useMemo(() => {
    return env.apiBaseUrl();
  }, []);

  return baseUrl;
};
