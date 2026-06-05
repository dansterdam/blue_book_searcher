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
        external: ['/pagefind/pagefind.js'],
      },
    },
    optimizeDeps: {
      exclude: ['pagefind'],
    },
    plugins: [
      {
        name: 'ignore-pagefind',
        apply: 'serve',
        resolveId(id) {
          if (id.includes('pagefind')) return { id, external: true };
        },
      },
    ],
  },
});
