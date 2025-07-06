import { createServer } from 'node:http';
import {
  CopilotRuntime,
  copilotRuntimeNodeHttpEndpoint,
  OpenAIAdapter,
} from '@copilotkit/runtime';
import dotenv from 'dotenv';
import path from 'path';
import { fileURLToPath } from 'url';
import cors from 'cors';
import http from 'http';

// Cargar variables de entorno desde el archivo .env en la raíz del proyecto
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
dotenv.config({ path: path.resolve(__dirname, '../.env') });

console.log('[LOG MCP] Iniciando configuración del Runtime...');

// 1. Verificar si la API key de OpenAI está cargada
const openaiApiKey = process.env.OPENAI_API_KEY;
if (!openaiApiKey) {
  console.error('[ERROR MCP] La variable de entorno OPENAI_API_KEY no se pudo cargar desde ../.env');
  process.exit(1); // Detener si la clave no está
} else {
  console.log('[LOG MCP] La clave de API de OpenAI ha sido cargada correctamente desde la raíz del proyecto.');
}

// 2. Configurar el Runtime para que apunte al backend correcto (puerto 8001)
const runtime = new CopilotRuntime({
  remoteEndpoints: [
    { url: "http://18.214.59.62:8001/copilotkit" },
  ],
});
console.log('[LOG MCP] CopilotRuntime configurado para apuntar a http://18.214.59.62:8001/copilotkit');

// 3. Instanciar el adaptador de OpenAI para satisfacer la dependencia
const serviceAdapter = new OpenAIAdapter();
console.log('[LOG MCP] OpenAIAdapter instanciado correctamente.');

// 4. Crear el manejador HTTP, pasando el serviceAdapter
const copilotHandler = copilotRuntimeNodeHttpEndpoint({
  endpoint: '/copilotkit',
  runtime,
  serviceAdapter,
});
console.log('[LOG MCP] Manejador HTTP de CopilotKit creado.');

// 5. Configurar CORS
const corsOptions = {
  origin: ['http://localhost:5174', 'http://127.0.0.1:5174', 'http://18.214.59.62:5174', 'http://18.214.59.62:5175'],
  credentials: true,
};
console.log(`[LOG MCP] CORS configurado para permitir orígenes: ${corsOptions.origin.join(', ')}`);

// 6. Crear el servidor y aplicar middlewares
const server = http.createServer((req: http.IncomingMessage, res: http.ServerResponse) => {
  const corsMiddleware = cors(corsOptions);
  corsMiddleware(req, res, () => {
    copilotHandler(req, res);
  });
});

console.log('[LOG MCP] Runtime CopilotKit arrancando...');

server.listen(4000, '0.0.0.0', () => {
  console.log('Runtime escuchando en http://0.0.0.0:4000/copilotkit');
});

process.on('exit', (code) => {
  console.log(`[LOG MCP] Proceso Node.js terminado con código: ${code}`);
});
process.on('SIGINT', () => {
  console.log('[LOG MCP] Proceso Node.js recibió SIGINT (Ctrl+C o kill)');
  process.exit();
});