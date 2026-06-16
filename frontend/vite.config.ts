import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'
import type { ServerResponse } from 'http'
import { codeHashPlugin } from './vite-plugin-code-hash'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react(),
    codeHashPlugin({
      include: ['src/**/*.{ts,tsx,js,jsx}'],
      exclude: ['**/node_modules/**', '**/dist/**', '**/*.d.ts']
    })
  ],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 5173,
    strictPort: true,
    host: true,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
        ws: true,
        configure: (proxy, _options) => {
          // Preservar cookies na REQUEST (frontend → backend)
          proxy.on('proxyReq', (proxyReq, req, _res) => {
            if (req.headers.cookie) {
              proxyReq.setHeader('cookie', req.headers.cookie)
            }
          })

          // Preservar cookies na RESPONSE (backend → frontend)
          proxy.on('proxyRes', (proxyRes, req, res: ServerResponse) => {
            // Encaminhar todos os Set-Cookie headers para o navegador
            const setCookieHeaders = proxyRes.headers['set-cookie']
            if (setCookieHeaders) {
              res.setHeader('set-cookie', setCookieHeaders)
            }
          })
        }
      },
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: false, // Desabilitar em produção para reduzir tamanho
    minify: 'esbuild',
    target: 'es2015',
    chunkSizeWarningLimit: 1000,
    rollupOptions: {
      output: {
        manualChunks: {
          'react-vendor': ['react', 'react-dom', 'react-router-dom'],
          'ui-vendor': ['@tanstack/react-query', 'axios'],
        },
      },
    },
  },
  preview: {
    port: 4173,
    strictPort: false,
    host: true,
    allowedHosts: ['laudonr13-frontend-prod.up.railway.app'],
  },
})
