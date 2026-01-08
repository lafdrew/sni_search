import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/query': 'http://localhost:9000',
      '/query/stream': 'http://localhost:9000',
      '/health': 'http://localhost:9000'
    }
  }
})
