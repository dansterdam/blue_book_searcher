import { defineConfig } from 'astro/config';
import tailwind from '@astrojs/tailwind';

export default defineConfig({
  integrations: [tailwind()],
  output: 'static',
  build: {
    format: 'directory',
  },
  vite: {
    build: {
      rollupOptions: {
        // pagefind.js is generated after the build, so externalize it
        external: ['/pagefind/pagefind.js'],
      },
    },
    // Also prevent Vite from trying to resolve it during dev
    optimizeDeps: {
      exclude: ['pagefind'],
    },
  },
});
