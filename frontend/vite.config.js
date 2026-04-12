import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      // Proxy SalesGenius API to avoid CORS issues in dev
      '/api/sales': {
        target: 'http://127.0.0.1:7860',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/sales/, ''),
      },
    },
  },
})
