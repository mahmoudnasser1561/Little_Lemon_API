import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'node:path';

const proxyTarget = process.env.VITE_PROXY_TARGET ?? 'http://localhost:8000';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@little-lemon/api-client': path.resolve(__dirname, '../../packages/api-client/src'),
      '@little-lemon/ui': path.resolve(__dirname, '../../packages/ui/src'),
    },
  },
  server: {
    host: true,
    port: 5174,
    fs: { allow: ['../..'] },
    watch: {
      usePolling: true,
    },
    proxy: {
      '/api': { target: proxyTarget, changeOrigin: true },
      '/token': { target: proxyTarget, changeOrigin: true },
      '/media': { target: proxyTarget, changeOrigin: true },
    },
  },
});
