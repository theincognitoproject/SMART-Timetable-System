import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    allowedHosts: ['smart-timetable-system.onrender.com'],
    host: true, // also helpful when deploying
    port: 4173,
  }
})
