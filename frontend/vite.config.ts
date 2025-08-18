import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  // Load environment variables
  const backendPort = process.env['VITE_BACKEND_PORT'] || '5000';
  const frontendPort = parseInt(process.env['VITE_FRONTEND_PORT'] || '3000', 10);
  const backendHost = process.env['VITE_BACKEND_HOST'] || '127.0.0.1';

  return {
    appType: 'spa',
    plugins: [react()],
    resolve: {
      alias: {
        '@': path.resolve(__dirname, './src'),
      },
    },
    server: {
      port: frontendPort,
      strictPort: false,
      host: '127.0.0.1',
      proxy: {
        // Proxy API requests to the backend server during development
        '/api': {
          target: `http://${backendHost}:${backendPort}`,
          changeOrigin: true,
          ws: false,
          proxyTimeout: 3600000,
          configure: (proxy) => {
            // Disable proxy buffering for SSE
            proxy.on('proxyRes', (proxyRes) => {
              const headers = proxyRes.headers;
              delete headers['content-length'];
            });
          },
        },
      },
    },
    build: {
      rollupOptions: {
        input: {
          main: './index.html',
        },
        output: {
          manualChunks: {
            // Vendor chunks
            vendor: ['react', 'react-dom', 'react-router-dom'],
            mui: ['@mui/material', '@mui/icons-material', '@emotion/react', '@emotion/styled'],
            query: ['@tanstack/react-query'],
            // Heavy visualization libraries - lazy loaded（由组件内动态 import）
            plotly: ['react-plotly.js'],
            forms: ['react-hook-form', 'zod'],
          },
        },
      },
      target: 'es2020',
      sourcemap: mode === 'development',
      minify: mode === 'production',
    },
    optimizeDeps: {
      include: [
        'react',
        'react-dom',
        'react-router-dom',
        '@mui/material',
        '@mui/icons-material',
        '@tanstack/react-query',
        'axios',
        'zod',
        'zustand',
        // 预构建 plotly 相关包（仅包含已安装依赖）
        'react-plotly.js',
      ],
      exclude: [
        // 移除排除，让 Vite 预构建这些包
      ],
    },
    // 添加特殊配置处理 react-plotly.js 的 CJS/ESM 兼容性
    define: {
      global: 'globalThis',
    },
  };
});
