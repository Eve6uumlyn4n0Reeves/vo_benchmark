export type Env = {
  VITE_API_BASE_URL?: string;
  VITE_API_TIMEOUT?: string;
  VITE_MAX_RETRIES?: string;
  VITE_SSE_RECONNECT_INTERVAL?: string;
  VITE_SSE_MAX_RECONNECT_ATTEMPTS?: string;
  VITE_DEFAULT_PAGE_SIZE?: string;
  VITE_MAX_PAGE_SIZE?: string;
  VITE_ENABLE_DEBUG?: string;
  VITE_ENABLE_REACT_QUERY_DEVTOOLS?: string;
  PROD?: boolean;
  DEV?: boolean;
};

export const getEnv = (): Env => {
  // Avoid direct `import.meta` to keep Jest (CJS) happy; prefer a safe global probe
  const g: any = (typeof globalThis !== 'undefined' ? (globalThis as any) : {}) as any;
  const viteEnv = g.import?.meta?.env;
  const nodeEnv = typeof process !== 'undefined' ? (process as any).env : undefined;
  const env: any = viteEnv || nodeEnv || {};
  return env as Env;
};

export const env = {
  apiBaseUrl: () => getEnv().VITE_API_BASE_URL || '/api/v1',
  apiTimeout: () => parseInt(getEnv().VITE_API_TIMEOUT || '30000', 10),
  maxRetries: () => parseInt(getEnv().VITE_MAX_RETRIES || '3', 10),
  sseReconnectInterval: () => parseInt(getEnv().VITE_SSE_RECONNECT_INTERVAL || '5000', 10),
  sseMaxReconnectAttempts: () => parseInt(getEnv().VITE_SSE_MAX_RECONNECT_ATTEMPTS || '5', 10),
  defaultPageSize: () => parseInt(getEnv().VITE_DEFAULT_PAGE_SIZE || '20', 10),
  maxPageSize: () => parseInt(getEnv().VITE_MAX_PAGE_SIZE || '100', 10),
  enableDebug: () => getEnv().VITE_ENABLE_DEBUG === 'true',
  isProd: () => !!getEnv().PROD,
  isDev: () => !!getEnv().DEV,
};
