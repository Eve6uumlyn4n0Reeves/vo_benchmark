import React from 'react';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { env, getEnv } from '@/utils/env';
import { ThemeProvider, CssBaseline } from '@mui/material';
import { createTheme } from '@/theme';
import { useThemeStore } from '@/store';
import { ErrorBoundary, ToastContainer } from '@/components/common';
import { RealtimeProvider } from '@/app/realtime/RealtimeProvider';

// Create Query Client with optimized defaults
const createQueryClient = () => {
  return new QueryClient({
    defaultOptions: {
      queries: {
        // Stale time - how long data is considered fresh
        staleTime: 5 * 60 * 1000, // 5 minutes
        // Cache time - how long data stays in cache after component unmounts
        gcTime: 10 * 60 * 1000, // 10 minutes (was cacheTime in v4)
        // Retry configuration
        retry: (failureCount, error) => {
          // Don't retry on 4xx errors
          if (error instanceof Error && 'status' in error) {
            const status = (error as any).status;
            if (status >= 400 && status < 500) {
              return false;
            }
          }
          // Retry up to 2 times for other errors
          return failureCount < 2;
        },
        retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
        // Refetch configuration
        refetchOnWindowFocus: false,
        refetchOnReconnect: true,
        refetchOnMount: true,
      },
      mutations: {
        retry: false, // Don't retry mutations by default
      },
    },
  });
};

// Theme Provider Component
const AppThemeProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { mode } = useThemeStore();
  const theme = React.useMemo(() => createTheme(mode), [mode]);

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      {children}
    </ThemeProvider>
  );
};

// Query Client Provider Component
const AppQueryProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [queryClient] = React.useState(() => createQueryClient());

  return (
    <QueryClientProvider client={queryClient}>
      {children}
      {getEnv().VITE_ENABLE_REACT_QUERY_DEVTOOLS === 'true' && (
        <ReactQueryDevtools initialIsOpen={false} />
      )}
    </QueryClientProvider>
  );
};

// Error Handler for ErrorBoundary
const handleGlobalError = (error: Error, errorInfo: React.ErrorInfo) => {
  // Log to console in development
  if (env.isDev()) {
    console.error('Global Error Boundary:', error, errorInfo);
  }

  // In production, you might want to send this to an error reporting service
  if (env.isProd()) {
    // Example: Send to error reporting service
    // errorReportingService.captureException(error, {
    //   extra: errorInfo,
    //   tags: { component: 'ErrorBoundary' },
    // });
  }
};

// Main App Providers Component
interface AppProvidersProps {
  children: React.ReactNode;
}

export const AppProviders: React.FC<AppProvidersProps> = ({ children }) => {
  return (
    <ErrorBoundary onError={handleGlobalError}>
      <BrowserRouter>
        <AppQueryProvider>
          <AppThemeProvider>
            <RealtimeProvider>
              {children}
              <ToastContainer />
            </RealtimeProvider>
          </AppThemeProvider>
        </AppQueryProvider>
      </BrowserRouter>
    </ErrorBoundary>
  );
};
