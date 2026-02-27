/* global process */
import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '');
  const apiTarget = env.VITE_API_BASE || 'http://127.0.0.1:8000';

  return {
    plugins: [react()],
    define: {
      // Injected at build time so the frontend can report its own deployment SHA.
      __BUILD_SHA__: JSON.stringify(process.env.VITE_BUILD_SHA || env.VITE_BUILD_SHA || 'local-dev'),
    },
    server: {
      host: true,
      port: 3000,
      strictPort: true,
      proxy: {
        '/api': {
          target: apiTarget,
          changeOrigin: true,
          secure: false,
        },
      },
    },
  };
});
