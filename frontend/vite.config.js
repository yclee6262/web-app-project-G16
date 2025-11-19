import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react({
      babel: {
        plugins: [["babel-plugin-react-compiler"]],
      },
    }),
  ],
  server: {
    host: "0.0.0.0",
    watch: {
      usePolling: true,
      interval: 100,
    },
    proxy: {
      "/api": "http://backend:5000", //since we are in docker network, use service name 'backend' and port 5000
    },
  },
});
