import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    // 0.0.0.0: reachable from the login node over the internal cluster
    // network, not just loopback on GPU57 itself. See dashboard/README.md.
    host: '0.0.0.0',
    port: 5173,
    proxy: {
      '/api': 'http://127.0.0.1:8000',
    },
  },
})
