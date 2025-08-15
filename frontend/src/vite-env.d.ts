/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_FRONTEND_PORT: string;
  readonly VITE_BACKEND_HOST: string;
  readonly VITE_BACKEND_PORT: string;
  readonly VITE_API_BASE_URL: string;
  readonly VITE_API_TIMEOUT: string;
  readonly VITE_MAX_RETRIES: string;
  readonly VITE_SSE_RECONNECT_INTERVAL: string;
  readonly VITE_SSE_MAX_RECONNECT_ATTEMPTS: string;
  readonly VITE_DEFAULT_PAGE_SIZE: string;
  readonly VITE_MAX_PAGE_SIZE: string;
  readonly VITE_ENABLE_DEBUG: string;
  readonly VITE_ENABLE_REACT_QUERY_DEVTOOLS: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
