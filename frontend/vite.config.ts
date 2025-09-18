import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    host: true,
    strictPort: true,
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
          api: ['axios'],
        },
      },
    },
  },
});

import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    open: true,
    proxy: {
      '/api': 'http://localhost:8080'
    }
  },
  build: {
    sourcemap: true,
    minify: 'esbuild',
    target: 'esnext',
    cssCodeSplit: true,
    chunkSizeWarningLimit: 600
  },
  optimizeDeps: {
    include: ['axios', 'react', 'react-dom']
  }
});
