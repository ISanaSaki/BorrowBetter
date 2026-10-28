import { defineConfig } from 'vite';

export default defineConfig({
  // Relative base keeps the build portable (GitHub Pages, sub-paths, preview servers).
  base: './',
  server: {
    port: 5173,
    strictPort: true,
  },
  preview: {
    port: 4173,
    strictPort: true,
  },
  build: {
    target: 'es2020',
    cssCodeSplit: false,
    assetsInlineLimit: 2048,
    sourcemap: false,
  },
});
