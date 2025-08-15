import '@testing-library/jest-dom';

// Mock Vite's import.meta for Jest environment
Object.defineProperty(globalThis, 'import', {
  value: {
    meta: {
      env: {
        VITE_API_BASE_URL: '/api/v1',
        VITE_API_TIMEOUT: '30000',
        VITE_MAX_RETRIES: '3',
        VITE_DEFAULT_PAGE_SIZE: '20',
        VITE_MAX_PAGE_SIZE: '100',
        VITE_SSE_RECONNECT_INTERVAL: '5000',
        VITE_SSE_MAX_RECONNECT_ATTEMPTS: '5',
        VITE_ENABLE_DEBUG: 'false',
        VITE_ENABLE_REACT_QUERY_DEVTOOLS: 'false',
        DEV: false,
        PROD: false,
      },
    },
  },
  writable: true,
});

// Mock window.matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: jest.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(), // deprecated
    removeListener: jest.fn(), // deprecated
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  })),
});

// Mock ResizeObserver
global.ResizeObserver = jest.fn().mockImplementation(() => ({
  observe: jest.fn(),
  unobserve: jest.fn(),
  disconnect: jest.fn(),
}));

// Mock IntersectionObserver
global.IntersectionObserver = jest.fn().mockImplementation(() => ({
  observe: jest.fn(),
  unobserve: jest.fn(),
  disconnect: jest.fn(),
}));

// Suppress console warnings in tests
const originalError = console.error;
beforeAll(() => {
  console.error = (...args: any[]) => {
    if (
      typeof args[0] === 'string' &&
      args[0].includes('Warning: ReactDOM.render is no longer supported')
    ) {
      return;
    }
    originalError.call(console, ...args);
  };
});

afterAll(() => {
  console.error = originalError;
});
