import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    // Opcional: Configurar un proxy si el frontend se sirve desde un puerto diferente al backend
    // y se quieren evitar problemas de CORS durante el desarrollo.
    // En producción, Nginx manejaría esto.
    proxy: {
      '/agent': { // Cualquier petición que comience con /agent (ej. /agent/chat)
        target: 'http://localhost:5175', // Actualizado al puerto correcto del backend del agente
        changeOrigin: true, 
        rewrite: (path) => path.replace(/^\/agent/, '/api/v1/agent'), // Corregido: un solo \ para escapar la / en la regex
        configure: (proxy, options) => {
          proxy.on('proxyReq', (proxyReq, req, res) => {
            // Asegúrate de que la cabecera Authorization se pasa
            // req es la solicitud original del navegador
            // proxyReq es la solicitud que Vite enviará al backend
            if (req.headers.authorization) {
              proxyReq.setHeader('Authorization', req.headers.authorization);
              console.log('[Vite Proxy] Authorization header set on proxy request for:', proxyReq.path);
            } else {
              console.log('[Vite Proxy] Original request to Vite DID NOT have Authorization header for path:', req.url);
            }
          });
        }
      }
    }
  }
}); 