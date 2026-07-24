import { defineConfig } from 'astro/config';
import tailwindcss from '@tailwindcss/vite';

export default defineConfig({
  site: 'https://yh420649215.github.io',
  base: '/palworld-legendary-pals',
  output: 'static',
  vite: {
    plugins: [tailwindcss()],
  },
});
