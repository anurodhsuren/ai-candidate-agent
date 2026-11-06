import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  base: './',
  // Classic JSX: elements are created by the same `react` copy that main.jsx imports,
  // so a stray/stale React 19 jsx-runtime can never be mixed in.
  plugins: [react({ jsxRuntime: 'classic' })],
  // Fresh cache folder: ignores any stale node_modules/.vite pre-bundled React.
  cacheDir: '.vite-cache',
  resolve: { dedupe: ['react', 'react-dom'] },
  optimizeDeps: { include: ['react', 'react-dom/client'] },
  server: { host: true, port: 5173, strictPort: true },
  preview: { host: true, port: 4173 },
})
