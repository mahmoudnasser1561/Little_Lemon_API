import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'node:path';

// Internal workspace packages are consumed as raw TS source (no separate build step
// for them yet) - the aliases below make Vite treat them as part of its own source
// graph regardless of how npm resolves the workspace symlink, and fs.allow lets Vite's
// dev server read files that live outside apps/storefront (in ../../packages).
// http://localhost:8000 works for `npm run dev` on the host; inside docker-compose the
// API isn't reachable as "localhost" (that's the frontend container's own loopback), so
// compose overrides this to the API's service name, e.g. VITE_PROXY_TARGET=http://api:8000.
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
    // 0.0.0.0, not just localhost - required for the dev server to be reachable from
    // outside its own container when run via docker-compose; harmless for local dev too.
    host: true,
    fs: { allow: ['../..'] },
    watch: {
      usePolling: true,
    },
    proxy: {
      // Same-origin from the browser's point of view in dev, mirroring how an ingress
      // would route these paths in production - no CORS setup needed on the API.
      '/api': { target: proxyTarget, changeOrigin: true },
      '/token': { target: proxyTarget, changeOrigin: true },
      // Menu item images under local storage (RelativeImageField returns a relative
      // /media/... path for exactly this reason - see restaurant/serializers.py).
      // Unused once the API switches to S3/MinIO, which returns a directly-reachable
      // URL instead and never needs proxying.
      '/media': { target: proxyTarget, changeOrigin: true },
    },
  },
});
